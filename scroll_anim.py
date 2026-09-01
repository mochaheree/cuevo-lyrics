"""
State machine posisi scroll lirik.

Menjawab satu pertanyaan saja: "baris ke berapa yang sedang berada di
tengah kanvas saat ini?" -- jawabannya boleh pecahan (mis. 2.4) selama
animasi perpindahan berjalan.

Kelas ini sengaja dipisah supaya thread Spout dan widget preview di GUI
memakai logika yang PERSIS SAMA. Kalau logikanya diduplikasi, preview dan
output akan menyimpang seiring waktu dan panel Style jadi tidak bisa
dipercaya (SRS REQ-F-OUT-08 / ADR-002).

Tidak boleh meng-import PySide6, Pillow, maupun SpoutGL.
"""
import time


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


class ScrollAnimator:
    """
    Pemakaian tiap frame:

        pos, need_redraw = animator.update(active_index, lines_version)
        if need_redraw:
            frame = renderer.render(lines, pos)

    `need_redraw` False artinya tampilan tidak berubah sejak frame lalu,
    jadi frame lama boleh dipakai ulang -- inilah yang membuat CPU tetap
    rendah saat lirik diam (REQ-F-OUT-02).
    """

    def __init__(self, transition_ms: int = 550):
        self.transition_sec = max(0.0, transition_ms / 1000.0)
        self.displayed_pos = -1.0
        self._version = None
        self._last_active = None
        self._anim_start = None
        self._from_pos = 0.0
        self._to_pos = 0.0
        self._force = True

    def set_transition_ms(self, transition_ms: int):
        """Dipanggil saat slider Transisi di panel Style digeser."""
        self.transition_sec = max(0.0, transition_ms / 1000.0)

    def update(self, active_index: int, lines_version: int, now: float = None):
        """
        active_index  : indeks baris aktif dari PlayerState.get_active_index()
        lines_version : PlayerState.get_lines_version() -- BUKAN id(lines),
                        lihat SRS §3.1 kenapa.

        Mengembalikan (displayed_pos, need_redraw).
        """
        now = time.perf_counter() if now is None else now
        need_redraw = self._force
        self._force = False

        if lines_version != self._version:
            # lagu baru dimuat -- lompat langsung, tanpa animasi
            self._version = lines_version
            self._last_active = active_index
            self.displayed_pos = float(active_index)
            self._anim_start = None
            return self.displayed_pos, True

        if active_index != self._last_active:
            self._from_pos = self.displayed_pos
            self._to_pos = float(active_index)
            self._anim_start = now
            self._last_active = active_index

        if self._anim_start is not None:
            if self.transition_sec <= 0:
                t = 1.0
            else:
                t = min(1.0, (now - self._anim_start) / self.transition_sec)
            self.displayed_pos = self._from_pos + (self._to_pos - self._from_pos) * ease_out_cubic(t)
            need_redraw = True
            if t >= 1.0:
                self._anim_start = None

        return self.displayed_pos, need_redraw

    def force_redraw(self):
        """
        Paksa frame berikutnya digambar ulang tanpa menggeser posisi.
        Dipakai saat parameter style berubah (slider di panel Style) --
        posisinya sama, tapi tampilannya beda.
        """
        self._force = True
