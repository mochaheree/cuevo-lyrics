"""
Penerima trigger OSC -- REQ-F-RC-01.

Dipakai untuk memicu next/prev/blank/play/pause dari controller fisik,
TouchOSC, atau Resolume sendiri (Resolume punya OSC out).

Parser OSC 1.0 ditulis sendiri, **tanpa dependency baru**: formatnya
sederhana (string null-terminated yang di-pad ke kelipatan 4 byte, lalu
type tag, lalu argumen) dan yang dibutuhkan di sini cuma sebagian kecil
dari spesifikasi. Menambah library hanya untuk ini tidak sepadan.

Tidak meng-import PySide6 (REQ-NF-06): handler-nya callable biasa.
Pemanggil yang bertanggung jawab memindahkan eksekusinya ke thread GUI --
lihat catatan keselamatan thread di bawah.

KESELAMATAN THREAD
------------------
`on_command` dipanggil dari thread socket, BUKAN thread GUI. Menyentuh
widget Qt dari thread lain adalah undefined behaviour (bisa crash, bisa
diam-diam salah). Karena itu `app.py` menyambungkannya lewat signal Qt,
yang otomatis di-queue ke thread GUI.
"""
import socket
import struct
import sys
import threading

DEFAULT_PORT = 8000

# Peta alamat OSC -> nama perintah. Sengaja pakai prefix /cuevo supaya tidak
# bentrok dengan pesan OSC lain yang lalu-lalang di jaringan yang sama.
ADDRESS_MAP = {
    "/cuevo/play": "play",
    "/cuevo/pause": "pause",
    "/cuevo/playpause": "play_pause",
    "/cuevo/next": "next_line",
    "/cuevo/prev": "prev_line",
    "/cuevo/blank": "blank_toggle",
    "/cuevo/blank/on": "blank_on",
    "/cuevo/blank/off": "blank_off",
    "/cuevo/song/next": "next_song",
    "/cuevo/song/prev": "prev_song",
    "/cuevo/song/goto": "goto_song",     # arg: int (1-based)
    "/cuevo/offset": "set_offset",       # arg: float (detik)
    "/cuevo/offset/nudge": "nudge_offset",  # arg: float (detik)
}


# Perintah yang argumennya adalah NILAI, bukan status tombol.
#
# Filter "tombol dilepas" (lihat is_release) membuang pesan berargumen 0 --
# benar untuk tombol, tapi salah total di sini: `/cuevo/offset 0.0` artinya
# "set offset ke nol", nilai yang sah dan justru sering dipakai untuk
# me-reset. Tanpa pengecualian ini, satu-satunya nilai yang tidak bisa
# dikirim adalah nol.
VALUE_COMMANDS = {"goto_song", "set_offset", "nudge_offset"}


def address_help():
    """Daftar alamat untuk ditampilkan di tab Settings."""
    return sorted(ADDRESS_MAP)


# ---------- parser OSC 1.0 (bagian yang dipakai saja) ----------

def _read_string(data, offset):
    end = data.find(b"\x00", offset)
    if end < 0:
        raise ValueError("string OSC tidak diakhiri null")
    text = data[offset:end].decode("utf-8", "replace")
    # setiap blok di-pad ke kelipatan 4 byte
    return text, offset + (len(text) // 4 + 1) * 4


def parse_message(data: bytes):
    """
    Kembalikan (address, args) dari satu datagram OSC, atau None kalau
    bukan pesan yang bisa dipahami.

    Bundle (#bundle) dilewati isinya satu per satu; yang dikembalikan hanya
    pesan pertama yang dikenali -- cukup untuk kebutuhan trigger di sini.
    """
    if not data:
        return None
    try:
        if data.startswith(b"#bundle"):
            # #bundle<null> + timetag 8 byte, lalu elemen: [size int32][isi]
            offset = 16
            while offset + 4 <= len(data):
                (size,) = struct.unpack_from(">i", data, offset)
                offset += 4
                element = data[offset:offset + size]
                parsed = parse_message(element)
                if parsed is not None:
                    return parsed
                offset += size
            return None

        address, offset = _read_string(data, 0)
        if not address.startswith("/"):
            return None

        args = []
        if offset < len(data):
            tags, offset = _read_string(data, offset)
            for tag in tags.lstrip(","):
                if tag == "i":
                    (value,) = struct.unpack_from(">i", data, offset)
                    offset += 4
                    args.append(value)
                elif tag == "f":
                    (value,) = struct.unpack_from(">f", data, offset)
                    offset += 4
                    args.append(value)
                elif tag == "s":
                    value, offset = _read_string(data, offset)
                    args.append(value)
                elif tag in "TF":          # true/false tanpa payload
                    args.append(tag == "T")
                elif tag == "N":
                    args.append(None)
                else:
                    break                   # tipe tak dikenal -- berhenti, jangan tebak
        return address, args
    except (ValueError, struct.error, IndexError):
        return None


def is_release(args) -> bool:
    """
    True kalau pesan ini adalah "tombol dilepas", bukan "ditekan".

    Banyak controller (TouchOSC, Resolume, kebanyakan foot controller)
    mengirim dua pesan per tekanan: 1.0 saat ditekan, 0.0 saat dilepas.
    Kalau keduanya diproses, SATU tekanan akan memicu aksi DUA KALI --
    saat live itu artinya lirik melompat dua baris.
    """
    if not args:
        return False
    first = args[0]
    if isinstance(first, bool):
        return not first
    if isinstance(first, (int, float)):
        return first == 0
    return False


class OscListener(threading.Thread):
    """
    Pemakaian:
        listener = OscListener(8000, on_command)
        ok, error = listener.start_listening()
        ...
        listener.stop()

    `on_command(nama_perintah, args)` dipanggil dari thread ini.
    """

    def __init__(self, port=DEFAULT_PORT, on_command=None, on_activity=None):
        super().__init__(daemon=True)
        self.port = port
        self.on_command = on_command
        self.on_activity = on_activity   # dipanggil utk SEMUA pesan, buat indikator
        self._socket = None
        self._stop = threading.Event()
        self.status = "belum dimulai"
        self.last_address = None

    def start_listening(self):
        """
        Bind dulu sebelum thread jalan, supaya kegagalan (port dipakai
        aplikasi lain) bisa dilaporkan langsung ke pemanggil -- bukan hilang
        di dalam thread dan menyisakan tombol "aktif" yang sebenarnya mati.
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # JANGAN pasang SO_REUSEADDR di sini. Di Windows opsi itu justru
            # MENGIZINKAN proses kedua ikut mengikat port yang sama (berbeda
            # dari Linux), sehingga bind ke port yang sudah dipakai aplikasi
            # lain akan "berhasil" -- padahal pesan OSC-nya bisa nyasar ke
            # aplikasi itu, sementara UI kita melaporkan status aktif.
            # SO_EXCLUSIVEADDRUSE membuat bentrokan gagal secara eksplisit,
            # sehingga bisa dilaporkan ke operator.
            exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
            if sys.platform == "win32" and exclusive is not None:
                self._socket.setsockopt(socket.SOL_SOCKET, exclusive, 1)
            self._socket.bind(("0.0.0.0", self.port))
            self._socket.settimeout(0.3)
        except OSError as exc:
            self._socket = None
            self.status = f"gagal: {exc}"
            return False, str(exc)

        self.status = f"mendengarkan di UDP {self.port}"
        self.start()
        return True, None

    def stop(self):
        self._stop.set()
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass

    def run(self):
        while not self._stop.is_set():
            try:
                data, _ = self._socket.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break        # socket ditutup saat stop()

            parsed = parse_message(data)
            if parsed is None:
                continue
            address, args = parsed
            self.last_address = address
            if self.on_activity is not None:
                self.on_activity(address, args)

            command = ADDRESS_MAP.get(address)
            if command is None:
                continue
            if command not in VALUE_COMMANDS and is_release(args):
                continue
            if self.on_command is not None:
                self.on_command(command, args)

        self.status = "berhenti"
