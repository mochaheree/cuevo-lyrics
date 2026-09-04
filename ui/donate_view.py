"""
Tab Donate dan kontak.

Kalau kamu fork proyek ini, ubah blok konfigurasi di bawah ke milikmu
sendiri. Semuanya sengaja ditaruh di satu tempat di paling atas, tidak
tersebar ke mana-mana, supaya gampang diganti.

Nada tabnya sengaja tenang. Aplikasi ini dipakai orang saat bekerja, jadi
halaman donasi yang mendesak akan terasa mengganggu.

Catatan soal QR: gambarnya QRIS, bukan QR satu dompet tertentu. QRIS adalah
standar nasional, jadi bisa dipindai dari DANA, GoPay, OVO, ShopeePay,
LinkAja, dan aplikasi bank. Labelnya ditulis QRIS supaya pengguna dompet
selain DANA tidak mengira tidak bisa ikut.

Isi QRIS_FILE harus kode QR-nya saja, bukan poster QRIS utuh. Poster yang
diperkecil ke kotak 230px menyisakan QR sekitar 80px di layar, kelihatan
benar tapi tidak bisa dipindai. Cara mengujinya: pindai tangkapan layar
aplikasinya, bukan file gambarnya.
"""
import os
import webbrowser

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QScrollArea, QFrame,
)

from store.paths import resource_path
from ui import theme

# ---------------------------------------------------------------------------
# Ganti bagian ini kalau kamu fork proyeknya
SAWERIA_URL = "https://saweria.co/cuevo"

QRIS_FILE = resource_path("assets", "qris.png")
QRIS_NAME = "Mocha Heree"
QRIS_NMID = "NMID ID1026526607985"

CONTACTS = [
    ("TikTok",    "@gevan.py",             "https://www.tiktok.com/@gevan.py"),
    ("Instagram", "@gevan.py",             "https://www.instagram.com/gevan.py/"),
    ("GitHub",    "mochaheree",            "https://github.com/mochaheree"),
    ("Email",     "putra.gevan00@gmail.com", "mailto:putra.gevan00@gmail.com"),
]

INTRO = [
    "If you found this project helpful, consider supporting me with a "
    "donation. Any amount is greatly appreciated and helps me keep building, "
    "improving, and sharing more projects like this.",

    "If you are looking for a custom app, tool, or have an idea you would "
    "like to bring to life, feel free to reach out. I would be happy to help.",
]
# ---------------------------------------------------------------------------

# Kode QRIS ini QR versi 26, 121 modul. Ditampilkan 516px berarti 4 piksel
# per modul, dan gambarnya memang dibuat persis segitu supaya Qt tidak
# menskalakan apa pun. Angkanya bukan selera: di bawah 490px kode ini gagal
# dipindai dari layar pada setiap percobaan, karena memperkecil grid modul
# menimbulkan moire. QR yang tidak bisa dipindai sama saja tidak ada.
QR_SIZE = 516
TEXT_WIDTH = 720


def _fit_wrapped(label, width):
    """
    Beri QLabel ber-wordWrap tinggi minimum yang benar.

    Qt menghitung sizeHint QLabel seolah teksnya satu baris, jadi label yang
    membungkus akan terpotong begitu ditaruh di layout yang menghormati
    sizeHint. Ini pernah terjadi di tab ini dan baru ketahuan dari tangkapan
    layar, bukan dari pemeriksaan otomatis, karena pemeriksaan lebar teks
    memang melewati label yang membungkus sementara yang kurang justru
    tingginya.
    """
    # ensurePolished() dulu: ukuran font datang dari stylesheet, dan sebelum
    # widget dipoles fontMetrics masih memakai font default. Menghitung tinggi
    # sebelum itu memberi angka yang meleset, dan teksnya tetap terpotong.
    label.ensurePolished()
    label.setMinimumHeight(label.heightForWidth(width))


class DonateView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._reset_timer = None

        # Isinya digulir. QR-nya butuh 536px tinggi supaya bisa dipindai
        # (lihat catatan QR_SIZE), dan di jendela minimum 1280x800 tinggi
        # segitu tidak muat setelah intro dan bar kontak. Tanpa gulir,
        # QR-nya terpotong panel dan langsung tidak berguna.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        theme.paint(scroll, f"background:{theme.V2};")
        outer.addWidget(scroll)

        content = QWidget()
        theme.paint(content, f"background:{theme.V2};")
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_intro())

        columns = QWidget()
        theme.paint(columns, f"background:{theme.SEAM};")
        cb = QHBoxLayout(columns)
        cb.setContentsMargins(0, 0, 0, 0)
        cb.setSpacing(1)
        cb.addWidget(self._build_saweria(), 1)
        cb.addWidget(self._build_qris(), 1)
        root.addWidget(columns)

        root.addWidget(self._build_contact())
        root.addStretch(1)

    # ---------- pengantar ----------

    def _build_intro(self):
        panel = QWidget()
        theme.paint(panel, f"background:{theme.V2};"
                           f"border-bottom:1px solid {theme.SEAM};")
        box = QVBoxLayout(panel)
        box.setContentsMargins(20, 18, 20, 18)
        box.setSpacing(10)

        title = QLabel("Support CUEVO Lyrics")
        theme.paint(title, f"color:{theme.T1};font-size:15px;font-weight:600;"
                           f"background:transparent;")
        box.addWidget(title)

        for paragraph in INTRO:
            body = QLabel(paragraph)
            body.setWordWrap(True)
            body.setMaximumWidth(TEXT_WIDTH)
            theme.paint(body, f"color:{theme.T2};font-size:12.5px;"
                              f"background:transparent;")
            _fit_wrapped(body, TEXT_WIDTH)
            box.addWidget(body)
        return panel

    # ---------- kolom kiri: Saweria ----------

    def _build_saweria(self):
        panel, box = self._column("Saweria")

        note = QLabel("Opens in your browser. Accepts QRIS, bank transfer, "
                      "and most Indonesian e-wallets.")
        note.setWordWrap(True)
        theme.paint(note, f"color:{theme.T3};font-size:11.5px;background:transparent;")
        _fit_wrapped(note, 380)
        box.addWidget(note)
        box.addSpacing(6)

        link = QLabel(SAWERIA_URL)
        link.setTextInteractionFlags(Qt.TextSelectableByMouse)
        theme.paint(link,
                    f"color:{theme.T2};font-family:{theme.MONO};font-size:11.5px;"
                    f"background:{theme.V1};padding:9px 11px;border-radius:2px;")
        box.addWidget(link)
        box.addSpacing(9)

        buttons = QWidget()
        theme.paint(buttons, "background:transparent;")
        bb = QHBoxLayout(buttons)
        bb.setContentsMargins(0, 0, 0, 0)
        bb.setSpacing(7)

        open_btn = QPushButton("Open Saweria")
        open_btn.clicked.connect(lambda: webbrowser.open(SAWERIA_URL))
        self.copy_btn = QPushButton("Copy link")
        self.copy_btn.setProperty("variant", "quiet")
        self.copy_btn.clicked.connect(self._copy_link)
        bb.addWidget(open_btn)
        bb.addWidget(self.copy_btn)
        bb.addStretch(1)
        box.addWidget(buttons)
        box.addStretch(1)
        return panel

    def _copy_link(self):
        QGuiApplication.clipboard().setText(SAWERIA_URL)
        # Konfirmasi ditulis di tombolnya sendiri, bukan lewat dialog. Dialog
        # untuk aksi sekecil ini memaksa satu klik tambahan tanpa alasan.
        self.copy_btn.setText("Copied")
        if self._reset_timer is not None:
            self._reset_timer.stop()
        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(lambda: self.copy_btn.setText("Copy link"))
        self._reset_timer.start(1500)

    # ---------- kolom kanan: QRIS ----------

    def _build_qris(self):
        panel, box = self._column("QRIS")

        note = QLabel("Scan with DANA, GoPay, OVO, ShopeePay, LinkAja, "
                      "or any banking app.")
        note.setWordWrap(True)
        theme.paint(note, f"color:{theme.T3};font-size:11.5px;background:transparent;")
        _fit_wrapped(note, 380)
        box.addWidget(note)
        box.addSpacing(10)

        holder = QWidget()
        theme.paint(holder, "background:transparent;")
        hb = QHBoxLayout(holder)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.setSpacing(14)

        if os.path.exists(QRIS_FILE):
            image = QLabel()
            # Latar putih di belakang QR: kode QR butuh kontras terang-gelap
            # untuk terbaca kamera, dan di panel gelap ini QR berlatar
            # transparan bisa gagal dipindai.
            theme.paint(image, "background:#ffffff;padding:10px;border-radius:3px;")
            # Tanpa scaled(): gambarnya sudah persis QR_SIZE. Menskalakan ulang
            # ke ukuran yang sama pun tetap melewatkan resampling, dan itu yang
            # merusak grid modulnya.
            image.setPixmap(QPixmap(QRIS_FILE))
            image.setFixedSize(QR_SIZE + 20, QR_SIZE + 20)
            image.setAlignment(Qt.AlignCenter)
            hb.addWidget(image)
        else:
            hb.addWidget(self._todo(
                "Put your QRIS image at assets/qris.png", height=QR_SIZE))
        hb.addStretch(1)
        box.addWidget(holder)

        # Nama dan NMID di bawah QR, bukan di sampingnya: pada 516px QR-nya
        # sudah hampir selebar kolom, dan menaruhnya di samping akan menekan
        # QR-nya lebih kecil dari ukuran yang terbukti bisa dipindai.
        name = QLabel(QRIS_NAME)
        theme.paint(name, f"color:{theme.T1};font-size:12.5px;font-weight:600;"
                          f"background:transparent;")
        nmid = QLabel(QRIS_NMID)
        theme.paint(nmid, f"color:{theme.T4};font-family:{theme.MONO};"
                          f"font-size:10.5px;background:transparent;")
        box.addSpacing(10)
        box.addWidget(name)
        box.addWidget(nmid)
        box.addStretch(1)
        return panel

    # ---------- kontak ----------

    def _build_contact(self):
        panel = QWidget()
        theme.paint(panel, f"background:{theme.V2};"
                           f"border-top:1px solid {theme.SEAM};")
        box = QVBoxLayout(panel)
        box.setContentsMargins(20, 14, 20, 18)
        box.setSpacing(9)

        head = QLabel("Contact")
        theme.paint(head, f"color:{theme.T3};font-size:11px;background:transparent;")
        box.addWidget(head)

        row = QWidget()
        theme.paint(row, "background:transparent;")
        rb = QHBoxLayout(row)
        rb.setContentsMargins(0, 0, 0, 0)
        rb.setSpacing(8)
        for label, handle, url in CONTACTS:
            rb.addWidget(self._contact_button(label, handle, url))
        rb.addStretch(1)
        box.addWidget(row)
        return panel

    def _contact_button(self, label, handle, url):
        button = QPushButton(f"{label}   {handle}")
        button.setProperty("variant", "quiet")
        button.setToolTip(url)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda: webbrowser.open(url))
        return button

    # ---------- pembantu ----------

    def _column(self, title):
        panel = QWidget()
        theme.paint(panel, f"background:{theme.V2};")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        head = QWidget()
        theme.paint(head, f"background:{theme.V3};"
                          f"border-bottom:1px solid {theme.SEAM};")
        hb = QHBoxLayout(head)
        hb.setContentsMargins(20, 8, 20, 8)
        name = QLabel(title)
        theme.paint(name, f"color:{theme.T1};font-size:12px;font-weight:600;"
                          f"background:transparent;")
        hb.addWidget(name)
        hb.addStretch(1)
        outer.addWidget(head)

        body = QWidget()
        theme.paint(body, "background:transparent;")
        box = QVBoxLayout(body)
        box.setContentsMargins(20, 16, 20, 20)
        box.setSpacing(4)
        outer.addWidget(body, 1)
        return panel, box

    def _todo(self, text, height=None):
        """
        Keadaan kosong yang menyebutkan persis apa yang harus dilakukan.

        Dipakai orang yang fork proyek ini, dan juga jaring pengaman kalau
        file QR-nya lupa ikut dibundel saat build .exe. Lebih baik kotak
        bertuliskan penyebabnya daripada ruang kosong tanpa penjelasan.
        """
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        theme.paint(label,
                    f"color:{theme.T4};font-size:11.5px;background:{theme.V1};"
                    f"border:1px dashed {theme.V4};border-radius:3px;padding:16px;")
        if height:
            label.setFixedSize(QR_SIZE + 20, height + 20)
        else:
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return label
