"""
Design token + stylesheet Qt, diturunkan dari MOCKUP.html v0.4.

Aturan bahasa visual (jangan dilanggar tanpa alasan):
  - Pemisah antar area pakai TINGKAT ABU, bukan garis terang.
    Divider lebih GELAP dari panel (seam), bukan lebih terang.
  - Satu-satunya warna jenuh adalah MERAH, dan artinya hanya satu:
    sedang tayang (ON AIR). Amber hanya berarti standby/next/offset aktif.
    Jangan pakai warna untuk hiasan.
  - Radius 0-3px. Tanpa shadow, tanpa gradient, tanpa glow.
  - Monospace HANYA untuk angka waktu (supaya digit tidak goyang).
  - Padat: baris 22-24px. Tombol besar hanya untuk aksi yang ditekan
    sambil live (transport dan BLANK).

Alasannya: alat ini dipakai di venue gelap, sekali lirik, sambil panik.
"""

# --- tingkat abu ---
V0 = "#000000"   # kanvas output
V1 = "#0e0e0f"   # latar app
V2 = "#151517"   # panel
V3 = "#1b1c1e"   # strip header
V4 = "#232427"   # baris aktif, tombol
V5 = "#2e3033"   # border tegas
SEAM = "#0a0a0b"  # divider -- lebih gelap dari panel

# --- teks ---
T1 = "#dcdde0"
T2 = "#8d9096"
T3 = "#5c5f65"
T4 = "#3c3e43"

# --- semantik (bukan dekorasi) ---
LIVE = "#ff3b30"     # ON AIR, dan tidak untuk hal lain
STANDBY = "#ffb020"  # NEXT, offset aktif, peringatan
OK = "#4ade80"       # ketersediaan synced lyrics

# --- font: diambil dari sistem, bukan dipatok di kode ---
#
# Nilai di bawah ini hanya fallback untuk saat modul di-import sebelum
# QApplication ada (mis. pengujian yang tidak membuat aplikasi Qt).
# `init_fonts()` menggantinya dengan font sistem sebenarnya, dipanggil dari
# main() tepat setelah QApplication dibuat.
#
# Semua pemakaian MONO/SANS ada di DALAM fungsi (f-string dievaluasi saat
# dipanggil), jadi penggantian global di sini ikut terpakai di seluruh UI.
MONO = "monospace"
SANS = "sans-serif"


# Font monospace yang didahulukan, sebelum jatuh ke font lebar-tetap sistem.
#
# Kenapa ada daftar ini padahal font UI murni ikut sistem: di Windows,
# `QFontDatabase.systemFont(FixedFont)` mengembalikan **Courier New** --
# peninggalan lama. Diukur berdampingan pada 13px, Courier New jauh lebih
# tipis dan lebih sulit dibaca sekilas dibanding Consolas, padahal teks yang
# memakainya adalah timecode yang dibaca dengan cepat di venue gelap.
# Keduanya sama-sama monospace (lebar digit seragam), jadi ini murni soal
# keterbacaan, bukan soal fungsi.
#
# Kosongkan daftar ini kalau ingin benar-benar 100% mengikuti sistem:
#     theme.PREFER_MONO = []
PREFER_MONO = ("Consolas", "Cascadia Mono", "SF Mono", "DejaVu Sans Mono")


def init_fonts():
    """
    Pakai font default sistem, bukan nama font yang dipatok di kode.

    Sebelumnya SANS dipatok ke "Segoe UI" dan MONO ke "Consolas". Itu salah
    di mesin yang font sistemnya diganti: aplikasi jadi tidak senada dengan
    aplikasi lain, dan kalau font itu tidak ada Qt jatuh ke pengganti yang
    belum tentu cocok.

    - SANS: murni dari `QApplication.font()` -- font antarmuka yang sudah
      ditentukan Qt dari pengaturan OS. Tidak ada preferensi apa pun.
    - MONO: `PREFER_MONO` dulu (lihat alasannya di atas), baru font
      lebar-tetap sistem. Monospace tetap wajib di sini karena teks waktu
      memakainya: dengan font proporsional, lebar tiap digit berbeda
      sehingga angka detik membuat seluruh baris bergoyang tiap perubahan.
    """
    global MONO, SANS
    from PySide6.QtGui import QFontDatabase, QGuiApplication

    ui_font = QGuiApplication.font().family()
    SANS = f'"{ui_font}", sans-serif' if ui_font else "sans-serif"

    installed = set(QFontDatabase.families())
    mono_font = next((name for name in PREFER_MONO if name in installed), None)
    if mono_font is None:
        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont).family()
    MONO = f'"{mono_font}", monospace' if mono_font else "monospace"
    return SANS, MONO

# tinggi baris daftar (px) -- lihat catatan kepadatan di atas
ROW_H = 24

_paint_counter = [0]


def paint(widget, css: str):
    """
    Terapkan CSS ke SATU widget saja, bukan ke anak-anaknya.

    Di Qt, `widget.setStyleSheet("background:#111")` tanpa selector berlaku
    untuk widget itu DAN seluruh keturunannya, serta mengalahkan stylesheet
    aplikasi. Akibatnya sebuah panel pembungkus diam-diam mengecat ulang
    setiap tombol dan input di dalamnya.

    Itu pernah terjadi: tombol Play di tab Live memakai latar terang dengan
    teks gelap (#0b0b0c), lalu panel transport menimpanya jadi latar gelap --
    tombolnya jadi tidak terlihat sama sekali, tapi tetap bisa diklik.
    Lihat SRS §3.7.

    Selalu pakai fungsi ini untuk mewarnai container. Selector `#nama`
    membuat aturannya berhenti di widget itu sendiri.
    """
    name = widget.objectName()
    if not name:
        _paint_counter[0] += 1
        name = f"pnl{_paint_counter[0]}"
        widget.setObjectName(name)
    widget.setStyleSheet(f"#{name} {{ {css} }}")


def stylesheet() -> str:
    return f"""
QWidget {{
    background: {V2};
    color: {T1};
    font-family: {SANS};
    font-size: 12px;
}}
QMainWindow, QWidget#Root {{ background: {V1}; }}

/* ---------- status strip ---------- */
QWidget#Strip {{ background: {V3}; border-bottom: 1px solid {SEAM}; }}
QLabel#StripCell {{
    color: {T2}; padding: 7px 13px;
    border-right: 1px solid {SEAM};
}}
QLabel#OnAir {{
    background: {LIVE}; color: #ffffff;
    font-family: {MONO}; font-weight: 700; font-size: 11px;
    padding: 7px 12px; border-right: 1px solid #000000;
}}
QLabel#OffAir {{
    background: {V4}; color: {T3};
    font-family: {MONO}; font-weight: 700; font-size: 11px;
    padding: 7px 12px; border-right: 1px solid {SEAM};
}}

/* ---------- tabs ---------- */
QTabWidget::pane {{ border: 0; background: {V2}; }}
QTabBar {{ background: {V3}; }}
QTabBar::tab {{
    background: {V3}; color: {T3};
    padding: 8px 15px; border-right: 1px solid {SEAM}; border-bottom: 1px solid {SEAM};
}}
QTabBar::tab:selected {{ background: {V2}; color: {T1}; border-bottom: 1px solid {V2}; }}

/* ---------- header kolom ---------- */
QLabel#ColHead {{
    background: {V3}; color: {T3};
    padding: 6px 12px; font-size: 11px;
    border-bottom: 1px solid {SEAM};
}}
QWidget#Foot {{ background: {V3}; border-top: 1px solid {SEAM}; }}
QLabel#FootText {{ background: transparent; color: {T3}; font-size: 11px; }}

/* ---------- daftar ---------- */
QListWidget {{
    background: {V2}; border: 0; outline: 0;
    show-decoration-selected: 1;
}}
QListWidget::item {{ color: {T2}; padding: 0 12px; border: 0; }}
QListWidget::item:selected {{ background: {V4}; color: #ffffff; }}
QListWidget::item:hover {{ background: {V3}; }}

/* ---------- tabel ---------- */
QTableWidget {{
    background: {V2}; border: 0; gridline-color: {SEAM};
    selection-background-color: {V4}; selection-color: {T1};
    outline: 0;
}}
QTableWidget::item {{ padding: 0 10px; border-bottom: 1px solid {SEAM}; }}
QHeaderView::section {{
    background: {V3}; color: {T3};
    padding: 6px 10px; border: 0; border-bottom: 1px solid {SEAM};
    font-weight: 400; font-size: 11px;
}}
QTableCornerButton::section {{ background: {V3}; border: 0; }}

/* ---------- tombol ---------- */
QPushButton {{
    background: {V4}; color: {T1};
    border: 0; border-radius: 2px; padding: 5px 10px; font-size: 11px;
}}
QPushButton:hover {{ background: {V5}; }}
QPushButton:disabled {{ background: {V3}; color: {T4}; }}
QPushButton[variant="quiet"] {{ background: transparent; color: {T2}; border: 1px solid {V4}; }}
QPushButton[variant="quiet"]:hover {{ background: {V3}; color: {T1}; }}
QPushButton[variant="transport"] {{ padding: 11px 18px; font-size: 13px; font-weight: 600; }}
QPushButton[variant="go"] {{
    background: #e8e9eb; color: #0b0b0c;
    padding: 11px 18px; font-size: 13px; font-weight: 600;
}}
QPushButton[variant="go"]:hover {{ background: #ffffff; }}
QPushButton[variant="kill"] {{
    background: transparent; color: {LIVE}; border: 1px solid {LIVE};
    padding: 11px 18px; font-size: 13px; font-weight: 700;
}}
QPushButton[variant="kill"]:hover {{ background: {LIVE}; color: #ffffff; }}
QPushButton[variant="kill"][engaged="true"] {{ background: {LIVE}; color: #ffffff; }}

/* ---------- input ---------- */
QLineEdit {{
    background: {V1}; color: {T1};
    border: 1px solid {V4}; border-radius: 2px; padding: 7px 10px;
    selection-background-color: {V5};
}}
QLineEdit:focus {{ border-color: {T3}; }}
QLineEdit[role="search"] {{ font-size: 13px; padding: 9px 12px; }}
QComboBox {{
    background: {V1}; color: {T1};
    border: 1px solid {V4}; border-radius: 2px; padding: 5px 9px;
}}
QComboBox::drop-down {{ border: 0; width: 16px; }}
QComboBox QAbstractItemView {{
    background: {V2}; color: {T1};
    border: 1px solid {V4}; selection-background-color: {V4};
}}
/* ---------- kontrol pilihan ---------- */
/* Radio dan checkbox sekarang diganti SegmentedControl di seluruh aplikasi.
   Aturan di bawah tetap ada sebagai jaring pengaman: tanpa menggayai
   ::indicator, kontrol semacam ini akan memakai indikator native Windows
   (sudut membulat ~4px, centang Windows 11) di dalam panel yang seluruh
   sudutnya 0-2px. Itu penyebab asli masalahnya, lihat SRS §3.12. */
QRadioButton, QCheckBox {{ color: {T2}; spacing: 7px; }}
QRadioButton:checked, QCheckBox:checked {{ color: {T1}; }}
QRadioButton:disabled, QCheckBox:disabled {{ color: {T4}; }}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 12px; height: 12px; border-radius: 2px;
    border: 1px solid {V5}; background: {V1};
}}
QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
    border-color: {T2}; background: {T1};
}}
QRadioButton::indicator:disabled, QCheckBox::indicator:disabled {{
    border-color: {V4}; background: {V2};
}}

/* ---------- segmented ---------- */
/* Ditaruh SESUDAH aturan QPushButton di atas supaya menang tanpa !important. */
QPushButton[seg] {{
    background: transparent; color: {T3};
    border: 1px solid {V4}; border-radius: 0;
    padding: 5px 12px; font-size: 11.5px; font-weight: 400;
}}
QPushButton[seg="first"] {{ border-top-left-radius: 2px; border-bottom-left-radius: 2px; }}
QPushButton[seg="last"] {{ border-top-right-radius: 2px; border-bottom-right-radius: 2px; }}
/* segmen selain yang pertama tidak menggambar tepi kiri, supaya garis
   pemisahnya satu, bukan dua yang berhimpit dan terlihat lebih tebal */
QPushButton[seg="mid"], QPushButton[seg="last"] {{ border-left: 0; }}
QPushButton[seg]:hover {{ background: {V3}; color: {T2}; }}
QPushButton[segRole="choice"]:checked {{ background: {V5}; color: #ffffff; font-weight: 600; }}
QPushButton[segRole="off"]:checked {{ background: {V4}; color: {T2}; font-weight: 600; }}
QPushButton[segRole="on"]:checked {{ background: {OK}; color: #04231a; font-weight: 700; }}
QPushButton[seg]:disabled {{ background: transparent; color: {T4}; border-color: {V3}; }}
QPushButton[segRole="on"]:checked:disabled {{ background: {V4}; color: {T4}; }}
QPushButton[segRole="off"]:checked:disabled,
QPushButton[segRole="choice"]:checked:disabled {{ background: {V3}; color: {T4}; }}

/* ---------- slider transport ---------- */
QSlider::groove:horizontal {{ background: {V2}; height: 16px; border-radius: 1px; }}
QSlider::sub-page:horizontal {{ background: {V4}; border-radius: 1px; }}
QSlider::add-page:horizontal {{ background: {V2}; border-radius: 1px; }}
QSlider::handle:horizontal {{ background: {LIVE}; width: 3px; margin: 0; }}

/* ---------- teks bantu ---------- */
QLabel[role="dim"] {{ color: {T3}; font-size: 11px; }}
QLabel[role="tc"] {{ color: {T1}; font-family: {MONO}; font-size: 13px; }}
QLabel[role="tc-dim"] {{ color: {T3}; font-family: {MONO}; font-size: 13px; }}
QLabel[role="offset"] {{ color: {STANDBY}; font-family: {MONO}; font-size: 12px; }}
QLabel[role="alert"] {{ color: {STANDBY}; padding: 7px 12px; font-size: 11px; }}
QLabel[role="cue-key"] {{ color: {STANDBY}; font-family: {MONO}; font-size: 11px; }}
QLabel[role="cue-val"] {{ color: {T1}; font-size: 14px; font-weight: 600; }}

QScrollBar:vertical {{ background: {V2}; width: 9px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {V4}; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {V5}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QSplitter::handle {{ background: {SEAM}; width: 1px; }}
"""
