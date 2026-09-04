"""
Di mana file data disimpan.

SRS §5.4 versi awal menaruh library di `./data/library.json` (relatif ke
folder project). Itu salah begitu aplikasi di-package jadi .exe: folder
instalasi biasanya read-only, dan dua instalasi akan saling menimpa.

Jadi lokasi sebenarnya:
    Windows : %APPDATA%\\CUEVO Lyrics\\
    lain    : ~/.local/share/CUEVO Lyrics/   (supaya tetap bisa diuji di
              non-Windows, REQ-NF-06)

`settings.json` selalu di folder itu dan TIDAK bisa dipindah -- kalau
lokasinya sendiri bisa dikonfigurasi, tidak ada tempat menyimpan
konfigurasi lokasinya. Path library dan shows boleh dipindah user
(REQ-F-CFG-02), dan nilainya disimpan di dalam settings.json.

Aplikasi ini sebelumnya bernama "Lyric Spout" dan menyimpan data di folder
`LyricSpout`. `migrate_legacy_data()` memindahkan folder lama itu (kalau
ada) ke nama baru sekali saja saat startup -- supaya rebranding tidak
diam-diam menghilangkan library/show yang sudah disimpan orang.
"""
import json
import os
import sys
import tempfile

APP_DIR_NAME = "CUEVO Lyrics"
_LEGACY_APP_DIR_NAMES = ["LyricSpout"]   # nama folder sebelum rebranding


def _app_data_base() -> str:
    if sys.platform == "win32":
        return os.environ.get("APPDATA") or os.path.expanduser("~")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support")
    return os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")


def app_data_dir() -> str:
    return os.path.join(_app_data_base(), APP_DIR_NAME)


def migrate_legacy_data():
    """
    Pindahkan folder data dari nama aplikasi lama ke nama baru, sekali saja.

    Dipanggil di awal startup, sebelum Settings/Library/dll dibaca. Kalau
    folder baru sudah ada (migrasi sudah pernah terjadi, atau ini instalasi
    baru), fungsi ini tidak melakukan apa-apa. Kegagalan migrasi (mis. file
    sedang dipakai proses lain) tidak boleh menghalangi aplikasi dibuka --
    dalam kasus itu app tetap jalan, hanya dengan data kosong, dan folder
    lama tetap utuh untuk dipindahkan manual.

    PENTING: `settings.json` yang ikut terbawa dalam folder yang dipindah
    berisi `library_path`/`shows_path` sebagai **path absolut** yang ditulis
    lengkap saat pertama kali disimpan -- bukan dihitung ulang dari
    `app_data_dir()` tiap dibaca. Kalau setelah rename kita biarkan begitu
    saja, dua field itu masih menunjuk ke folder lama yang baru saja
    lenyap. Efeknya diam-diam: `Library()` menganggap file "belum ada"
    (bukan error) dan mulai dari koleksi kosong -- padahal lagunya utuh,
    cuma terputus dari konfigurasi yang menunjuknya. Ini persis ditemukan
    saat memverifikasi migrasi pada data asli (SRS §3.8): 11 lagu nyaris
    jadi tidak terlihat oleh aplikasi meski filenya tidak hilang.

    Makanya `_rewrite_stored_paths()` dipanggil segera setelah rename
    berhasil, dan HANYA mengganti path yang masih berupa default lama
    (di dalam folder yang baru saja dipindah) -- path yang sudah
    dikustomisasi user ke lokasi lain (REQ-F-CFG-02) tidak disentuh.

    Fungsi ini juga **self-healing**: kalau folder baru sudah ada tapi
    folder lama sudah tidak ada (persis kondisi yang tertinggal dari versi
    migrasi sebelum perbaikan path di atas ada), ia tetap mencoba
    memperbaiki `library_path`/`shows_path` yang nyasar -- tanpa itu,
    instalasi yang sempat kena bug ini tidak akan pernah pulih sendiri.
    """
    new_dir = app_data_dir()
    base = _app_data_base()

    if os.path.isdir(new_dir):
        for legacy_name in _LEGACY_APP_DIR_NAMES:
            old_dir = os.path.join(base, legacy_name)
            if not os.path.isdir(old_dir):
                try:
                    _rewrite_stored_paths(new_dir, old_dir)
                except OSError:
                    pass
        return

    for legacy_name in _LEGACY_APP_DIR_NAMES:
        old_dir = os.path.join(base, legacy_name)
        if os.path.isdir(old_dir):
            try:
                os.rename(old_dir, new_dir)
                _rewrite_stored_paths(new_dir, old_dir)
            except OSError:
                pass
            return


def _rewrite_stored_paths(new_dir: str, old_dir: str):
    """
    Setelah folder dipindah, perbaiki referensi path absolut di dalam
    settings.json yang masih menunjuk ke folder lama.

    Hanya `library_path` dan `shows_path` yang diperiksa -- keduanya
    satu-satunya field path absolut di skema Settings (§5.4). Kalau nilainya
    berada TEPAT di dalam folder lama (mis. `...\\LyricSpout\\library.json`),
    prefiksnya diganti ke folder baru. Kalau user pernah memindahkannya ke
    lokasi lain sama sekali, path itu tidak diawali `old_dir` dan dibiarkan
    apa adanya.
    """
    settings_file = os.path.join(new_dir, "settings.json")
    data, error = read_json(settings_file, None)
    if error or not isinstance(data, dict):
        return

    old_prefix = os.path.normcase(os.path.abspath(old_dir))
    changed = False
    for key in ("library_path", "shows_path"):
        value = data.get(key)
        if not value:
            continue
        abs_value = os.path.abspath(value)
        if os.path.normcase(abs_value).startswith(old_prefix):
            data[key] = new_dir + abs_value[len(old_dir):]
            changed = True

    if changed:
        try:
            write_json_atomic(settings_file, data)
        except OSError:
            pass   # settings tetap menunjuk path lama; lebih baik daripada crash


def resource_path(*parts) -> str:
    """
    Cari file yang ikut dibundel bersama aplikasi (gambar, ikon).

    Beda dari app_data_dir(): yang itu tempat data pengguna yang bisa berubah,
    ini file bawaan yang cuma dibaca.

    PyInstaller mengekstrak bundel ke folder sementara dan menaruh path-nya di
    sys._MEIPASS. Kalau dijalankan langsung dari source, atribut itu tidak ada
    dan patokannya folder project. Tanpa pembedaan ini, gambar yang tampil
    normal saat development akan hilang begitu dibungkus jadi .exe.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def settings_path() -> str:
    return os.path.join(app_data_dir(), "settings.json")


def default_library_path() -> str:
    return os.path.join(app_data_dir(), "library.json")


def default_shows_dir() -> str:
    return os.path.join(app_data_dir(), "shows")


def ensure_parent_dir(path: str):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def read_json(path: str, fallback):
    """
    Baca file JSON. Kalau tidak ada, rusak, atau tidak bisa dibaca ->
    kembalikan `fallback` beserta pesannya, JANGAN melempar exception.

    Alasan: file library rusak tidak boleh membuat aplikasi gagal dibuka
    di tengah acara. Lebih baik jalan dengan library kosong dan memberi
    tahu, daripada tidak jalan sama sekali (semangat REQ-NF-03).

    Mengembalikan (data, error_message_atau_None).
    """
    if not os.path.exists(path):
        return fallback, None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle), None
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        return fallback, f"{os.path.basename(path)} could not be read ({exc})"


def write_json_atomic(path: str, data):
    """
    Tulis JSON lewat file sementara lalu os.replace().

    Kenapa atomik: kalau aplikasi mati atau listrik padam persis saat
    menyimpan, cara naif akan meninggalkan library.json terpotong --
    seluruh koleksi lagu hilang. os.replace() bersifat atomik di Windows
    maupun POSIX, jadi file lama tetap utuh sampai file baru lengkap.
    """
    ensure_parent_dir(path)
    directory = os.path.dirname(os.path.abspath(path))
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=directory, prefix=".tmp-", suffix=".json", delete=False
    )
    try:
        with handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
