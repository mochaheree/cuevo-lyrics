"""
Kontrol segmented, pengganti radio dan checkbox di seluruh aplikasi.

Kenapa diganti (SRS §3.12):

`theme.py` dulu hanya mengatur warna teks radio dan checkbox, tidak pernah
menyentuh `::indicator`. Akibatnya indikatornya adalah kontrol native Windows
apa adanya: sudut membulat sekitar 4px dan centang gaya Windows 11, di dalam
panel yang seluruh sudutnya 0 sampai 2px. Kontrol itu tidak pernah didesain,
ia diwarisi karena kelalaian.

Selain itu ketiga grup radio di aplikasi ini isinya tepat DUA pilihan. Radio
memakai dua baris untuk menyampaikan satu keputusan, dan pilihan yang tidak
aktif diwarnai sama persis dengan kontrol yang dinonaktifkan, sehingga
terbaca "tidak tersedia" padahal sah dipilih.

DIBANGUN DARI QPushButton, BUKAN DIGAMBAR SENDIRI
-------------------------------------------------
Tiap segmen adalah `QPushButton` checkable di dalam `QButtonGroup` eksklusif.
Konsekuensinya penting: tiap segmen sudah punya `setChecked`, `isChecked`,
`toggled`, `setEnabled`, dan `setToolTip` -- persis API `QRadioButton`. Jadi
`SegmentedControl.button(i)` bisa menggantikan sebuah QRadioButton tanpa
mengubah satu pun pemanggilnya. Menggambar widget sendiri akan memaksa
menulis ulang penanganan klik, fokus keyboard, dan keadaan nonaktif yang
sudah benar di Qt.

ATURAN WARNA (dipakai bersama lencana di tab Settings)
------------------------------------------------------
- Pilihan biasa (mode, sumber, layout) terisi netral terang. Ini preferensi,
  bukan keadaan hidup.
- Sambungan (OSC, MIDI, hotkey global) terisi hijau HANYA saat benar-benar
  berjalan. Memakai hijau untuk pilihan biasa akan menyamakan "saya memilih
  ini" dengan "ini sedang berjalan".
- Merah tidak pernah dipakai di sini. Merah hanya milik ON AIR (BLANK).
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup


class SegmentedControl(QWidget):
    """
    Beberapa pilihan saling meniadakan dalam satu batang.

    changed(int) memancar saat pilihan berpindah, sekali per perpindahan.
    """

    changed = Signal(int)

    def __init__(self, labels, role="choice", parent=None):
        super().__init__(parent)
        self._buttons = []

        box = QHBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)              # 0 supaya tepinya menyatu jadi satu batang

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        last = len(labels) - 1
        for index, label in enumerate(labels):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            # QDialog memperlakukan QPushButton sebagai tombol default kalau
            # dibiarkan; tanpa ini, Enter di editor lirik bisa menekan segmen
            button.setAutoDefault(False)
            button.setProperty("seg", "first" if index == 0
                               else ("last" if index == last else "mid"))
            button.setProperty("segRole", self._role_for(role, index, last))
            self._group.addButton(button, index)
            box.addWidget(button)
            self._buttons.append(button)

        if self._buttons:
            self._buttons[0].setChecked(True)
        self._group.idToggled.connect(self._on_toggled)

    @staticmethod
    def _role_for(role, index, last):
        """
        Peran warna tiap segmen. Untuk sakelar hidup-mati, segmen terakhir
        adalah "menyala" (hijau) dan sisanya "padam" (redup).
        """
        if role != "switch":
            return "choice"
        return "on" if index == last else "off"

    def _on_toggled(self, index, checked):
        if checked:
            self.changed.emit(index)

    # ---------- akses ----------

    def button(self, index) -> QPushButton:
        """
        Satu segmen, siap dipakai menggantikan QRadioButton.

        API-nya identik: setChecked, isChecked, toggled, setEnabled, setToolTip.
        """
        return self._buttons[index]

    def buttons(self):
        return list(self._buttons)

    def current_index(self) -> int:
        return self._group.checkedId()

    def set_current_index(self, index):
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)

    def setEnabled(self, enabled):        # noqa: N802 - mengikuti gaya Qt
        super().setEnabled(enabled)
        for button in self._buttons:
            button.setEnabled(enabled)

    def setToolTip(self, text):           # noqa: N802 - mengikuti gaya Qt
        super().setToolTip(text)
        for button in self._buttons:
            button.setToolTip(text)


class SegmentedToggle(SegmentedControl):
    """
    Sakelar hidup-mati bergaya segmented, pengganti QCheckBox.

    Sengaja meniru API QCheckBox (`isChecked`, `setChecked`, `toggled`) supaya
    bisa ditukar langsung tanpa mengubah pemanggilnya.

    Kenapa keadaan mati ikut ditulis, bukan cuma kotak kosong: checkbox lama
    bertuliskan "Aktif" baik saat hidup maupun mati, dan satu-satunya pembeda
    adalah kotak 13px. Melirik tulisan "Aktif" di venue gelap tidak memberi
    tahu apa pun.
    """

    toggled = Signal(bool)

    def __init__(self, off_label="Mati", on_label="Aktif", parent=None):
        super().__init__([off_label, on_label], role="switch", parent=parent)
        self.changed.connect(lambda index: self.toggled.emit(index == 1))

    def isChecked(self) -> bool:          # noqa: N802 - mengikuti gaya Qt
        return self.current_index() == 1

    def setChecked(self, checked):        # noqa: N802 - mengikuti gaya Qt
        self.set_current_index(1 if checked else 0)

    def toggle(self):
        self.setChecked(not self.isChecked())
