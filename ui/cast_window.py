"""
Jendela Cast -- permukaan siar untuk OBS, TikTok Live Studio, dan layar kedua.

KENAPA KETIGANYA SATU FITUR, BUKAN TIGA
---------------------------------------
Permintaannya "multicast ke OBS, TikTok Live, dan window baru". Ketiganya
bermuara ke satu hal yang sama: **sebuah jendela yang bisa ditangkap**.

- OBS  : Window Capture atau Game Capture menangkap jendela mana pun.
- TikTok Live Studio : hanya bisa menangkap layar atau jendela. Tidak
  mengenal Spout, tidak mengenal NDI.
- Layar kedua : jendela yang sama, di-fullscreen di monitor lain.

Jadi yang dibangun satu: jendela ini. Tiga tujuan itu cara memakainya.

CATATAN JUJUR SOAL TRANSPARANSI
-------------------------------
Spout membawa alpha sungguhan, jadi di Resolume lirik menumpuk mulus di atas
video. **Window Capture tidak begitu.** Baik BitBlt maupun Windows Graphics
Capture menyusun jendela di atas latar buram sebelum menyerahkannya, jadi
alpha per-piksel tidak ikut. Ini batasan Windows, bukan sesuatu yang bisa
diakali dari sisi aplikasi.

Itulah alasan pemilih latar di bawah ada:

    OBS, mau alpha asli   -> pasang plugin Spout2, terima sender langsung
                             (jendela ini tidak diperlukan)
    OBS, tanpa plugin     -> Window Capture + filter Chroma Key, latar hijau
    TikTok Live Studio    -> Screen/Window Capture, latar hijau atau magenta
    Layar kedua/proyektor -> fullscreen di monitor itu, latar hitam

Magenta disediakan karena lirik putih ber-outline hitam kadang menyisakan
tepi kehijauan setelah di-key dari latar hijau.

BIAYA RENDER: NOL
-----------------
Jendela ini tidak merender apa pun sendiri. Ia memakai `PreviewWidget` yang
sama, disambungkan ke sumber yang sama seperti Operator Display: frame dari
thread Spout kalau output jalan, atau mencerminkan preview tab Live kalau
tidak. Lihat `PreviewWidget.set_mirror()` dan SRS §3.9.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QKeySequence, QShortcut, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QMenu,
)

from ui import theme
from ui.preview import PreviewWidget

# Nilai chroma sengaja jenuh penuh supaya key-nya bersih. Hijau dan magenta
# adalah dua warna yang paling jauh dari warna teks lirik pada umumnya
# (putih, hitam, amber).
BACKGROUNDS = [
    ("Black", "#000000", "second screen, projector"),
    ("Chroma green", "#00ff00", "OBS / TikTok, then Chroma Key"),
    ("Chroma magenta", "#ff00ff", "if text edges look green"),
]


class CastWindow(QWidget):
    """
    Jendela terpisah, sengaja tanpa hiasan apa pun di area gambarnya.

    Semua kontrol ada di bilah atas yang bisa disembunyikan. Saat
    disembunyikan, jendelanya jadi tanpa bingkai dan seluruh isinya adalah
    frame lirik -- itu yang ditangkap OBS. Klik kanan tetap memunculkan menu
    dan Esc selalu mengembalikan bilahnya, supaya jendela ini tidak pernah
    bisa terkunci tanpa jalan keluar.
    """

    closed = Signal()
    opacityFalloffFixRequested = Signal()   # minta app.py men-nol-kan falloff

    def __init__(self, player_state, style=None, background="#000000",
                 mirror_of=None, parent=None):
        super().__init__(parent)
        self.player_state = player_state
        self._drag_origin = None
        self._background = background

        self.setWindowTitle("CUEVO Lyrics - Cast")
        self.setWindowFlag(Qt.Window)
        self.resize(960, 540)
        self.setStyleSheet(theme.stylesheet())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._bar = self._build_bar()
        root.addWidget(self._bar)

        self.preview = PreviewWidget(player_state, style)
        if mirror_of is not None:
            self.preview.set_mirror(mirror_of)
        root.addWidget(self.preview, 1)

        self._warning = self._build_warning()
        root.insertWidget(1, self._warning)

        self._style = style
        self.set_background(background)

        # Esc selalu mengembalikan bilah dan keluar dari fullscreen. Ini
        # satu-satunya jalan keluar yang dijamin ada saat jendela tanpa bingkai.
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._escape)

    # ---------- bilah kontrol ----------

    def _build_bar(self):
        bar = QWidget()
        theme.paint(bar, f"background:{theme.V3};border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(bar)
        box.setContentsMargins(12, 7, 12, 7)
        box.setSpacing(8)

        label = QLabel("Cast")
        theme.paint(label, f"color:{theme.T2};font-size:11.5px;font-weight:600;"
                           f"background:transparent;")
        box.addWidget(label)

        self.background_combo = QComboBox()
        for name, value, note in BACKGROUNDS:
            self.background_combo.addItem(f"{name}: {note}", value)
        self.background_combo.setMinimumWidth(240)
        self.background_combo.currentIndexChanged.connect(self._on_background_changed)
        box.addWidget(self.background_combo)

        self.screen_combo = QComboBox()
        self.screen_combo.setMinimumWidth(150)
        for index, screen in enumerate(QGuiApplication.screens()):
            size = screen.geometry()
            primary = " (primary)" if screen == QGuiApplication.primaryScreen() else ""
            self.screen_combo.addItem(
                f"Monitor {index + 1}: {size.width()}x{size.height()}{primary}", index)
        self.screen_combo.activated.connect(self._move_to_screen)
        box.addWidget(self.screen_combo)
        box.addStretch(1)

        self.top_btn = QPushButton("Always on top")
        self.top_btn.setProperty("variant", "quiet")
        self.top_btn.setCheckable(True)
        self.top_btn.toggled.connect(self._set_always_on_top)
        box.addWidget(self.top_btn)

        clean_btn = QPushButton("Hide bar")
        clean_btn.setProperty("variant", "quiet")
        clean_btn.setToolTip("Hides the frame so the capture stays clean.\n"
                             "Press Esc or right-click to bring it back.")
        clean_btn.clicked.connect(self.enter_clean_mode)
        box.addWidget(clean_btn)

        full_btn = QPushButton("Full screen")
        full_btn.setProperty("variant", "quiet")
        full_btn.setToolTip("Press Esc to exit")
        full_btn.clicked.connect(self._toggle_fullscreen)
        box.addWidget(full_btn)
        return bar

    def _build_warning(self):
        """
        Peringatan chroma key.

        Sengaja diletakkan di antara bilah kontrol dan gambar, BUKAN di atas
        gambar: apa pun yang menimpa area gambar akan ikut tersiar. Bilah ini
        juga ikut tersembunyi di mode bersih, jadi tidak pernah bocor ke
        tangkapan OBS.
        """
        bar = QWidget()
        theme.paint(bar, f"background:{theme.V2};"
                         f"border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(bar)
        box.setContentsMargins(12, 8, 12, 8)
        box.setSpacing(9)

        self._warning_text = QLabel("")
        self._warning_text.setWordWrap(True)
        theme.paint(self._warning_text,
                    f"color:{theme.STANDBY};font-size:11px;background:transparent;")
        box.addWidget(self._warning_text, 1)

        fix = QPushButton("Zero the opacity falloff")
        fix.setProperty("variant", "quiet")
        fix.setToolTip("Makes every context line fully opaque so it survives "
                       "the chroma key. Size falloff still works.")
        fix.clicked.connect(self.opacityFalloffFixRequested.emit)
        box.addWidget(fix)

        bar.hide()
        return bar

    def _refresh_warning(self):
        """
        Baris konteks memakai alpha untuk memudar. Alpha TIDAK selamat lewat
        Window Capture: Windows menyusun jendela di atas latar buram dulu,
        sehingga baris pudar tercampur warna latar. Di latar chroma, hasilnya
        terukur begini pada falloff bawaan 0.32:

            baris aktif  255,255,255  putih murni, aman
            baris +-1    173,255,173  tepi hijau
            baris +-2     90,254,90   nyaris hijau murni, ikut terbuang key

        Jadi di latar chroma, hanya baris aktif yang selamat utuh. Ini bukan
        bug yang bisa diperbaiki dari sini; ini sifat window capture. Yang
        bisa dilakukan: memberi tahu, dan menawarkan jalan keluarnya.
        """
        chroma = self._background not in ("#000000",)
        falloff = getattr(self._style, "opacity_falloff", 0.0) if self._style else 0.0
        context = 0
        if self._style is not None:
            context = self._style.context_before + self._style.context_after

        if chroma and falloff > 0.01 and context > 0:
            self._warning_text.setText(
                "Context lines fade using alpha, and alpha does not survive "
                "Window Capture. On a chroma background, faded lines blend with it "
                "and get keyed away. Zero the opacity falloff, or use "
                "OBS with the Spout2 plugin, which carries real alpha."
            )
            self._warning.show()
        else:
            self._warning.hide()

    def set_style(self, style):
        self._style = style
        self.preview.set_style(style)
        self._refresh_warning()

    # ---------- latar ----------

    def _on_background_changed(self):
        self.set_background(self.background_combo.currentData())

    def set_background(self, value):
        self._background = value
        self.preview.set_cast_background(QColor(value))
        theme.paint(self, f"background:{value};")
        index = self.background_combo.findData(value)
        if index >= 0:
            self.background_combo.blockSignals(True)
            self.background_combo.setCurrentIndex(index)
            self.background_combo.blockSignals(False)
        self._refresh_warning()

    def background(self):
        return self._background

    # ---------- mode bersih & fullscreen ----------

    def enter_clean_mode(self):
        """Sembunyikan semua kecuali gambar, supaya tangkapan OBS bersih."""
        self._bar.hide()
        self._warning.hide()
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        if was_visible:
            self.show()

    def exit_clean_mode(self):
        self._bar.show()
        self._refresh_warning()
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.FramelessWindowHint, False)
        if was_visible:
            self.show()

    def is_clean(self) -> bool:
        return self._bar.isHidden()

    def _escape(self):
        if self.isFullScreen():
            self.showNormal()
        if self.is_clean():
            self.exit_clean_mode()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _set_always_on_top(self, on):
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, on)
        if was_visible:
            self.show()

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

    # ---------- menu kanan: satu-satunya kontrol saat bilah disembunyikan ----------

    def _show_menu(self, position):
        menu = QMenu(self)
        menu.setStyleSheet(theme.stylesheet())

        if self.is_clean():
            menu.addAction("Show control bar", self.exit_clean_mode)
        else:
            menu.addAction("Hide control bar", self.enter_clean_mode)
        menu.addAction("Exit full screen" if self.isFullScreen() else "Full screen",
                       self._toggle_fullscreen)
        menu.addSeparator()
        for name, value, note in BACKGROUNDS:
            action = QAction(f"Background: {name}", menu)
            action.setCheckable(True)
            action.setChecked(value == self._background)
            action.triggered.connect(lambda _=False, v=value: self.set_background(v))
            menu.addAction(action)
        menu.addSeparator()
        menu.addAction("Close Cast window", self.close)
        menu.exec(self.mapToGlobal(position))

    # ---------- geser jendela saat tanpa bingkai ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_clean() and not self.isFullScreen():
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_origin is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_origin)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_origin = None
        super().mouseReleaseEvent(event)

    # ---------- sumber frame ----------

    def set_source(self, spout_thread):
        self.preview.set_source(spout_thread)

    def set_mirror(self, preview):
        self.preview.set_mirror(preview)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
