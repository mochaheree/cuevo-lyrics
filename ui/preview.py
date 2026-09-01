"""
Widget preview output (Screen 01 & 04 di mockup).

Ini implementasi REQ-F-OUT-08: preview TIDAK menggambar tiruannya sendiri.
Ia memakai `MultiLineLyricRenderer` dan `ScrollAnimator` yang persis sama
dengan yang dipakai thread Spout, dari `RenderStyle` yang sama pula --
satu-satunya perbedaan adalah faktor skala resolusi supaya ringan digambar
puluhan kali per detik di dalam GUI.

Kalau suatu saat preview dan output terlihat berbeda, itu bug, bukan
"perbedaan wajar antara preview dan hasil akhir".
"""
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QImage, QPainter, QPixmap, QColor, QBrush
from PySide6.QtWidgets import QWidget

from render_style import DEFAULT_STYLE
from scroll_anim import ScrollAnimator
from spout_output import build_renderer
from ui import theme

# Batas bawah ukuran font yang aman untuk dirender.
#
# Diukur: Pillow/FreeType punya tebing performa di sekitar 20px. Menggambar
# teks berukuran <=16px sekitar 5x LEBIH LAMBAT daripada 21px ke atas
# (815 ms vs 225 ms per 100 draw). Jadi mengecilkan kanvas preview justru
# membuatnya lebih mahal, bukan lebih murah -- persis kebalikan dari dugaan.
# Lihat SRS §3.2.
MIN_SAFE_FONT_PX = 22


class PreviewWidget(QWidget):
    """
    Menampilkan output.

    Kalau thread Spout sedang jalan, widget ini TIDAK merender apa pun -- ia
    memakai frame yang barusan dikirim ke Resolume. Jadi "frame identik"
    (REQ-F-OUT-08) bukan sekadar janji: preview dan output benar-benar buffer
    yang sama, dan biaya render tidak dibayar dua kali.

    Kalau output mati, barulah widget merender sendiri supaya operator tetap
    bisa menyetel style sebelum tayang.
    """

    def __init__(self, player_state, style=None, fps=30, parent=None):
        super().__init__(parent)
        self.player_state = player_state
        self._style = style or DEFAULT_STYLE
        self._pixmap = None
        self._source = None          # thread Spout, kalau sedang jalan
        self._last_frame_id = None
        self._mirror = None          # PreviewWidget lain yang framenya disalin

        self._rebuild_renderer()
        self.setMinimumHeight(120)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(int(1000 / max(1, fps)))

    # ---------- style ----------

    def set_style(self, style):
        """Dipanggil panel Style tiap slider digeser (Fase 3)."""
        self._style = style
        self._rebuild_renderer()
        self._animator.force_redraw()

    def _rebuild_renderer(self):
        # Perkecil kanvas hanya sejauh font terkecil masih di atas tebing
        # performa Pillow. Baris terjauh berukuran active*(1 - 2*size_falloff),
        # jadi itu yang dipakai sebagai penentu.
        smallest_ratio = max(0.2, 1.0 - 2 * self._style.size_falloff)
        min_active_font = MIN_SAFE_FONT_PX / smallest_ratio
        factor = min(1.0, max(0.25, min_active_font / max(1, self._style.active_font_size)))
        self._render_style = self._style.scaled(factor)
        self._renderer = build_renderer(self._render_style)
        self._animator = ScrollAnimator(self._style.transition_ms)

    def set_source(self, spout_thread):
        """
        Sambungkan/putuskan ke thread output. Saat tersambung, preview berhenti
        merender sendiri dan hanya menampilkan frame kiriman.
        """
        self._source = spout_thread
        self._last_frame_id = None
        self._animator.force_redraw()

    def set_mirror(self, other):
        """
        Jadikan widget ini cermin dari PreviewWidget lain: ia menyalin pixmap
        yang sudah jadi, tidak merender apa pun sendiri.

        Dipakai Operator Display (Screen 06).

        Dua alasan, dan yang kedua sebenarnya lebih penting:

        1. Lebih murah. Diukur pada kondisi terburuk (gambar ulang dipaksa
           tiap frame, kanvas 1179x663): dua preview yang merender
           sendiri-sendiri 11,7 ms/frame, dengan mirror 6,1 ms/frame --
           sekitar 1,9x lebih hemat. Keduanya masih di bawah budget 33,3 ms
           untuk 30 fps, jadi ini bukan soal "kalau tidak begini akan
           gagal", melainkan menyisakan headroom.
        2. Menjamin kedua layar menampilkan frame yang **sama persis**.
           Dua renderer terpisah punya ScrollAnimator sendiri-sendiri, jadi
           posisi animasinya bisa berbeda beberapa milidetik -- operator
           akan melihat Operator Display sedikit tidak sinkron dengan
           preview di tab Live. Ini alasan yang sama dengan REQ-F-OUT-08.
        """
        self._mirror = other

    def _is_blank(self) -> bool:
        """
        Keadaan blank dibaca dari PlayerState, bukan disimpan di widget ini.

        Versi sebelumnya menyimpannya lokal, dan akibatnya preview gelap
        sementara Resolume tetap menampilkan lirik -- operator mengira
        penonton tidak melihat apa-apa. Lihat SRS §3.3.
        """
        return self.player_state.is_blank()

    # ---------- loop gambar ----------

    def _tick(self):
        if self._is_blank():
            if self._pixmap is not None:
                self._pixmap = None
                self._animator.force_redraw()
                self.update()
            return

        if self._mirror is not None:
            # cukup salin pixmap yang sudah jadi -- tidak merender apa pun
            if self._mirror._pixmap is not self._pixmap:
                self._pixmap = self._mirror._pixmap
                self.update()
            return

        if self._source is not None and self._source.is_alive():
            self._tick_from_output()
            return
        self._tick_self_rendered()

    def _tick_from_output(self):
        """Jalur murah: pakai frame yang sudah dirender thread Spout."""
        frame = self._source.latest_frame
        if frame is None or id(frame) == self._last_frame_id:
            return
        self._last_frame_id = id(frame)
        raw, width, height = frame
        self._set_pixmap(raw, width, height)

    def _tick_self_rendered(self):
        """Jalur mandiri: output mati, preview merender sendiri."""
        lines = self.player_state.get_lines()
        active_index = self.player_state.get_active_index(
            self.player_state.get_current_time()
        )
        pos, need_redraw = self._animator.update(
            active_index, self.player_state.get_lines_version()
        )
        if not need_redraw:
            return  # tampilan tidak berubah -- jangan buang CPU (REQ-F-OUT-02)

        raw = self._renderer.render(lines, pos)
        self._set_pixmap(raw, self._render_style.width, self._render_style.height)

    def _set_pixmap(self, raw, width, height):
        # `raw` harus ditahan referensinya selama QImage hidup: QImage tidak
        # menyalin buffer yang diberikan. copy() memutus ketergantungan itu.
        image = QImage(raw, width, height, QImage.Format_RGBA8888).copy()
        self._pixmap = QPixmap.fromImage(image)
        self.update()

    # ---------- lukis ----------

    def sizeHint(self):
        return QSize(320, 180)

    def heightForWidth(self, width):
        return round(width * 9 / 16)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        # area 16:9 di tengah widget
        w = rect.width()
        h = round(w * self._style.height / max(1, self._style.width))
        if h > rect.height():
            h = rect.height()
            w = round(h * self._style.width / max(1, self._style.height))
        x = rect.x() + (rect.width() - w) // 2
        y = rect.y() + (rect.height() - h) // 2

        painter.fillRect(rect, QColor(theme.V1))
        self._paint_checker(painter, x, y, w, h)

        if self._pixmap is not None:
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.drawPixmap(x, y, w, h, self._pixmap)

        if self._is_blank():
            painter.setPen(QColor(theme.LIVE))
            painter.drawText(x, y, w, h, Qt.AlignCenter, "BLANK")

        painter.end()

    def _paint_checker(self, painter, x, y, w, h):
        """Kotak-kotak = area transparan. Konvensi compositing, bukan hiasan."""
        painter.fillRect(x, y, w, h, QBrush(QColor("#0b0b0c")))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#131314")))
        cell = 7
        for row, cy in enumerate(range(y, y + h, cell)):
            for col, cx in enumerate(range(x, x + w, cell)):
                if (row + col) % 2:
                    painter.drawRect(cx, cy, min(cell, x + w - cx), min(cell, y + h - cy))
        painter.setBrush(Qt.NoBrush)
