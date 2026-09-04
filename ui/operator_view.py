"""
Screen 06 di mockup -- Operator Display (REQ-F-OPS-01/02).

Window kedua, biasanya ditaruh di monitor terpisah dan dibaca dari jarak
1-2 meter sambil melakukan hal lain. Karena itu isinya sengaja cuma dua
informasi berukuran besar: **apa yang sedang tayang** dan **apa
berikutnya**. Sisanya baris status kecil di bawah.

Window ini **read-only**. Tidak ada satu pun tombol yang mengubah keadaan
tayang -- kalau operator menaruhnya di monitor kedua lalu menyenggol mouse,
tidak boleh ada yang berubah di Resolume. Kontrol tetap hanya di tab Live.

Preview outputnya **mencerminkan** preview di tab Live (`set_mirror`),
bukan merender sendiri -- lebih hemat (1,9x, terukur) dan yang lebih
penting: menjamin kedua layar menampilkan frame yang sama persis. Lihat
`PreviewWidget.set_mirror()`.
"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
)

from ui import theme
from ui.preview import PreviewWidget


def _format_clock(seconds: float) -> str:
    seconds = max(0.0, seconds)
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"


class OperatorView(QWidget):
    """Window terpisah -- bukan tab. Ditutup tidak mematikan aplikasi."""

    closed = Signal()

    def __init__(self, player_state, show_session, mirror_of=None, parent=None):
        super().__init__(parent)
        self.player_state = player_state
        self.show_session = show_session
        self._spout_thread = None

        self.setWindowTitle("CUEVO Lyrics - Operator Display")
        self.setWindowFlag(Qt.Window)
        self.resize(900, 560)
        self.setStyleSheet(theme.stylesheet())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_strip())
        root.addWidget(self._build_body(mirror_of), 1)
        root.addWidget(self._build_footer())

        # Esc keluar dari fullscreen -- jalan pintas yang diharapkan orang,
        # dan penting karena di fullscreen tombol "Full screen" ikut tersembunyi
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._leave_fullscreen)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(120)
        self.refresh()

    # ---------- strip atas ----------

    def _build_strip(self):
        strip = QWidget()
        theme.paint(strip, f"background:{theme.V3};border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(strip)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        self.air_label = QLabel("IDLE")
        self.air_label.setStyleSheet(self._air_style("idle"))
        box.addWidget(self.air_label)

        title = QLabel("Operator Display")
        theme.paint(title, f"color:{theme.T2};background:transparent;padding:9px 13px;")
        box.addWidget(title)
        box.addStretch(1)

        self.screen_combo = QComboBox()
        self.screen_combo.setFixedWidth(190)
        self.screen_combo.setToolTip("Move this window to another monitor")
        self._fill_screens()
        self.screen_combo.activated.connect(self._move_to_screen)

        self.preview_btn = QPushButton("Hide preview")
        self.preview_btn.setProperty("variant", "quiet")
        self.preview_btn.clicked.connect(self._toggle_preview)

        self.fullscreen_btn = QPushButton("Full screen")
        self.fullscreen_btn.setProperty("variant", "quiet")
        self.fullscreen_btn.setToolTip("Press Esc to exit")
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)

        wrap = QWidget()
        wb = QHBoxLayout(wrap)
        wb.setContentsMargins(12, 6, 12, 6)
        wb.setSpacing(7)
        for widget in (self.screen_combo, self.preview_btn, self.fullscreen_btn):
            wb.addWidget(widget)
        box.addWidget(wrap)
        self._strip = strip
        return strip

    def _air_style(self, state):
        base = f"font-family:{theme.MONO};font-weight:700;font-size:11px;padding:9px 13px;"
        if state == "live":
            return base + f"background:{theme.LIVE};color:#ffffff;"
        if state == "blank":
            return base + f"background:{theme.V4};color:{theme.STANDBY};"
        return base + f"background:{theme.V4};color:{theme.T3};"

    # ---------- isi utama ----------

    def _build_body(self, mirror_of):
        body = QWidget()
        theme.paint(body, "background:#000000;")
        box = QHBoxLayout(body)
        box.setContentsMargins(34, 28, 34, 28)
        box.setSpacing(28)

        # kiri: NOW / NEXT, ukuran besar
        text_col = QWidget()
        theme.paint(text_col, "background:transparent;")
        tb = QVBoxLayout(text_col)
        tb.setContentsMargins(0, 0, 0, 0)
        tb.setSpacing(0)

        now_key = QLabel("NOW")
        theme.paint(now_key,
                    f"color:{theme.T3};font-family:{theme.MONO};font-size:11px;"
                    f"letter-spacing:2px;background:transparent;")
        self.now_label = QLabel("-")
        self.now_label.setWordWrap(True)
        theme.paint(self.now_label,
                    "color:#ffffff;font-size:40px;font-weight:800;"
                    "letter-spacing:-0.5px;background:transparent;")

        next_key = QLabel("NEXT")
        theme.paint(next_key,
                    f"color:{theme.T3};font-family:{theme.MONO};font-size:11px;"
                    f"letter-spacing:2px;background:transparent;")
        self.next_label = QLabel("-")
        self.next_label.setWordWrap(True)
        theme.paint(self.next_label,
                    f"color:{theme.STANDBY};font-size:23px;font-weight:600;"
                    f"background:transparent;")

        tb.addWidget(now_key)
        tb.addSpacing(9)
        tb.addWidget(self.now_label)
        tb.addSpacing(28)
        tb.addWidget(next_key)
        tb.addSpacing(8)
        tb.addWidget(self.next_label)
        tb.addStretch(1)
        box.addWidget(text_col, 1)

        # kanan: preview -- mencerminkan tab Live, tidak merender sendiri
        self.preview = PreviewWidget(self.player_state)
        self.preview.setFixedWidth(300)
        if mirror_of is not None:
            self.preview.set_mirror(mirror_of)
        box.addWidget(self.preview)
        return body

    def _build_footer(self):
        foot = QWidget()
        theme.paint(foot, f"background:{theme.V2};border-top:1px solid {theme.SEAM};")
        box = QHBoxLayout(foot)
        box.setContentsMargins(16, 10, 16, 10)
        box.setSpacing(24)

        self.song_label = QLabel("-")
        self.time_label = QLabel("00:00 / 00:00")
        self.mode_label = QLabel("AUTO")
        self.offset_label = QLabel("OFFSET +0.00")
        for label in (self.song_label, self.time_label, self.mode_label):
            theme.paint(label,
                        f"color:{theme.T3};font-family:{theme.MONO};font-size:12px;"
                        f"background:transparent;")
        theme.paint(self.offset_label,
                    f"color:{theme.STANDBY};font-family:{theme.MONO};font-size:12px;"
                    f"background:transparent;")
        for label in (self.song_label, self.time_label, self.mode_label, self.offset_label):
            box.addWidget(label)
        box.addStretch(1)
        return foot

    # ---------- monitor & fullscreen ----------

    def _fill_screens(self):
        self.screen_combo.clear()
        for index, screen in enumerate(QGuiApplication.screens()):
            size = screen.geometry()
            primary = " (primary)" if screen == QGuiApplication.primaryScreen() else ""
            self.screen_combo.addItem(
                f"Monitor {index + 1}: {size.width()}×{size.height()}{primary}", index)

    def _move_to_screen(self, combo_index):
        screens = QGuiApplication.screens()
        target = self.screen_combo.itemData(combo_index)
        if target is None or not (0 <= target < len(screens)):
            return
        geometry = screens[target].geometry()
        was_fullscreen = self.isFullScreen()
        if was_fullscreen:
            self.showNormal()
        self.move(geometry.center().x() - self.width() // 2,
                  geometry.center().y() - self.height() // 2)
        if was_fullscreen:
            self.showFullScreen()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self._leave_fullscreen()
        else:
            self.showFullScreen()
            # strip disembunyikan supaya teks dapat ruang penuh; Esc tetap jalan
            self._strip.hide()

    def _leave_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self._strip.show()

    def _toggle_preview(self):
        visible = not self.preview.isVisible()
        self.preview.setVisible(visible)
        self.preview_btn.setText("Hide preview" if visible else "Show preview")

    # ---------- data ----------

    def set_spout_thread(self, thread):
        self._spout_thread = thread

    def refresh(self):
        lines = self.player_state.get_lines()
        index = self.player_state.get_active_index(self.player_state.get_current_time())

        self.now_label.setText(
            lines[index][1] if 0 <= index < len(lines) and lines[index][1] else "-")
        self.next_label.setText(
            lines[index + 1][1] if 0 <= index + 1 < len(lines) and lines[index + 1][1] else "-")

        song = self.show_session.current()
        position = self.show_session.position_label()
        self.song_label.setText(
            f"{position} · {song.title.upper()}" if song else "NOT IN A SHOW")

        self.time_label.setText(
            f"{_format_clock(self.player_state.get_raw_position())} / "
            f"{_format_clock(self.player_state.get_duration())}")
        self.mode_label.setText(
            "MANUAL" if self.player_state.is_manual_mode() else "AUTO")
        self.offset_label.setText(f"OFFSET {self.player_state.get_offset():+.2f}")

        running = bool(self._spout_thread and self._spout_thread.is_alive())
        blanked = self.player_state.is_blank()
        if running and not blanked:
            state, text = "live", "ON AIR"
        elif running:
            state, text = "blank", "BLANK"
        else:
            state, text = "idle", "IDLE"
        self.air_label.setText(text)
        self.air_label.setStyleSheet(self._air_style(state))

    def closeEvent(self, event):
        self._timer.stop()
        self.closed.emit()
        super().closeEvent(event)
