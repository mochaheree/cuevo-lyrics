"""
Menyimpan status pemutaran lirik yang dipakai bersama oleh GUI (Tkinter,
thread utama) dan thread output Spout. Semua akses di-lock supaya aman
diakses dari dua thread berbeda secara bersamaan.

Karena sync dilakukan manual (bukan baca posisi player musik lain),
posisi waktu dihitung dari kapan tombol Play terakhir ditekan, ditambah
offset koreksi manual yang bisa kamu geser kalau lirik terasa
mendahului/tertinggal dari lagu aslinya.
"""
import threading
import time

from lrc_parser import find_current_line, find_current_index


class PlayerState:
    def __init__(self):
        self._lock = threading.Lock()
        self._lines = []              # list of (time_sec, text), dari parse_lrc()
        self._duration = 0.0          # durasi lagu (detik), untuk slider seek
        self._is_playing = False
        self._position = 0.0          # posisi "tersimpan" saat pause/seek (detik)
        self._play_started_at = None  # perf_counter() saat tombol Play ditekan
        self._manual_offset = 0.0     # koreksi manual (detik), + = lirik dimajukan
        self._lines_version = 0       # naik tiap lagu baru dimuat -- lihat get_lines_version()
        self._blank = False           # REQ-F-PLAY-04: output dikosongkan, waktu tetap jalan
        self._manual_mode = False     # REQ-F-PLAY-05: baris ditentukan operator, bukan jam
        self._manual_index = -1

    # ---------- dipanggil dari GUI untuk mengontrol ----------

    def load_lyrics(self, parsed_lines, duration=0.0):
        with self._lock:
            self._lines = parsed_lines
            self._duration = duration
            self._is_playing = False
            self._position = 0.0
            self._play_started_at = None
            self._lines_version += 1
            self._manual_index = 0 if parsed_lines else -1

    # ---------- blank (REQ-F-PLAY-04) ----------

    def set_blank(self, blank: bool):
        """
        Kosongkan output tanpa menyentuh posisi waktu.

        Disimpan di sini, bukan di widget preview, supaya thread Spout dan
        preview membaca keadaan yang sama. Versi sebelumnya menaruh flag ini
        hanya di preview -- akibatnya operator melihat preview gelap sementara
        Resolume tetap menampilkan lirik. Lihat SRS §3.3.
        """
        with self._lock:
            self._blank = blank

    def is_blank(self) -> bool:
        with self._lock:
            return self._blank

    # ---------- mode manual per-baris (REQ-F-PLAY-05) ----------

    def set_manual_mode(self, manual: bool):
        """
        Mode manual: baris aktif ditentukan tombol Next/Prev, bukan timestamp.
        Untuk lagu tanpa tempo tetap (acapella, rubato).

        Saat berpindah mode, posisi baris dibawa dari mode sebelumnya supaya
        tampilan tidak melompat di tengah lagu.
        """
        with self._lock:
            if manual == self._manual_mode:
                return
            if manual:
                lines, offset = self._lines, self._manual_offset
                position = (self._position if not self._is_playing
                            else self._position + (time.perf_counter() - self._play_started_at))
                self._manual_index = find_current_index(lines, position + offset)
            self._manual_mode = manual

    def is_manual_mode(self) -> bool:
        with self._lock:
            return self._manual_mode

    def step_manual(self, delta: int) -> int:
        """Maju/mundur satu baris. Mengembalikan indeks baru."""
        with self._lock:
            if not self._lines:
                return -1
            self._manual_index = max(0, min(len(self._lines) - 1,
                                            self._manual_index + delta))
            return self._manual_index

    def goto_manual(self, index: int) -> int:
        with self._lock:
            if not self._lines:
                return -1
            self._manual_index = max(0, min(len(self._lines) - 1, index))
            return self._manual_index

    def play(self):
        with self._lock:
            if not self._is_playing:
                self._is_playing = True
                self._play_started_at = time.perf_counter()

    def pause(self):
        with self._lock:
            if self._is_playing:
                self._position += time.perf_counter() - self._play_started_at
                self._is_playing = False
                self._play_started_at = None

    def stop(self):
        with self._lock:
            self._is_playing = False
            self._play_started_at = None
            self._position = 0.0

    def seek(self, seconds: float):
        with self._lock:
            self._position = max(0.0, seconds)
            if self._is_playing:
                self._play_started_at = time.perf_counter()

    def nudge_offset(self, delta_seconds: float):
        """Koreksi manual kalau lirik terasa maju/mundur dibanding lagu asli."""
        with self._lock:
            self._manual_offset += delta_seconds

    # ---------- dibaca oleh GUI (update slider/label) & thread Spout ----------

    def get_offset(self) -> float:
        with self._lock:
            return self._manual_offset

    def get_duration(self) -> float:
        with self._lock:
            return self._duration

    def is_playing(self) -> bool:
        with self._lock:
            return self._is_playing

    def get_raw_position(self) -> float:
        """Posisi lagu (detik) tanpa offset koreksi manual."""
        with self._lock:
            if self._is_playing:
                return self._position + (time.perf_counter() - self._play_started_at)
            return self._position

    def get_current_time(self) -> float:
        """Posisi efektif (dipakai untuk mencari baris lirik aktif)."""
        return self.get_raw_position() + self.get_offset()

    def get_line_for_time(self, t: float) -> str:
        with self._lock:
            lines = self._lines
        return find_current_line(lines, t)

    def get_lines(self):
        """Salinan seluruh baris lirik yang sedang dimuat: list of (time_sec, text)."""
        with self._lock:
            return list(self._lines)

    def get_lines_version(self) -> int:
        """
        Counter yang naik tiap load_lyrics(). Dipakai konsumen (thread Spout,
        widget preview) untuk tahu "lagu sudah ganti" tanpa membandingkan isi
        list tiap frame.

        JANGAN pakai id(get_lines()) untuk itu: get_lines() mengembalikan
        salinan baru tiap dipanggil, jadi id()-nya berubah hampir tiap frame.
        Bug itu pernah terjadi dan membuat animasi transisi tidak pernah jalan
        sekaligus mematikan cache frame (lihat SRS §3.1).
        """
        with self._lock:
            return self._lines_version

    def get_active_index(self, t: float) -> int:
        """
        Indeks baris yang sedang aktif pada waktu t, atau -1 kalau belum
        ada baris yang tercapai. Dipakai renderer multi-baris untuk tahu
        baris mana yang harus ditonjolkan di tengah, dan baris apa saja
        yang tampil di atas/bawahnya.

        Di mode manual, `t` diabaikan sepenuhnya -- yang berlaku adalah baris
        yang terakhir dipilih operator (REQ-F-PLAY-05).
        """
        with self._lock:
            if self._manual_mode:
                return self._manual_index
            lines = self._lines
        return find_current_index(lines, t)
