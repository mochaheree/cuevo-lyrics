"""
Screen 05 -- pengaturan per-instalasi (REQ-F-CFG-01/02).

Tata letak "modul rak" (redesign v0.9.2, lihat MOCKUP_SETTINGS.html opsi A).
Tiap kelompok jadi modul tersendiri dengan kepala dan lencana keadaan, disusun
dua kolom supaya lebar jendela yang selama ini menganggur terpakai.

Tiga hal yang diperbaiki dari tata letak lama:

1. Bobot visual mengikuti akibat, bukan urutan. Nama sender yang disetel sekali
   seumur hidup tidak lagi tampil sepenting tombol OSC yang berakibat langsung
   saat acara berjalan.
2. Keadaan hidup/mati terlihat tanpa dicoba. Dulu satu-satunya cara tahu OSC
   jalan atau tidak adalah menekan sesuatu dan berharap.
3. Bahan rujukan (alamat OSC, peta note MIDI) jadi tabel yang bisa dipindai,
   bukan paragraf mono yang membungkus.

ATURAN LENCANA: lencana WAJIB mencerminkan keadaan sebenarnya. `app.py`
mendorong keadaan itu tiap 500ms lewat `refresh_state()`. Lencana yang
menampilkan "aktif" tanpa benar-benar memeriksa lebih buruk daripada tidak ada
lencana sama sekali -- itu persis mode gagal BLANK di SRS §3.3.

Perubahan langsung disimpan ke settings.json begitu kolomnya ditinggalkan,
jadi tidak ada tombol Simpan yang bisa lupa ditekan.
"""
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QFileDialog, QComboBox, QSizePolicy,
)

from ui import theme
from ui.segmented import SegmentedToggle


def _short_path(path: str) -> str:
    """
    "...\\CUEVO Lyrics\\library.json" -- dua bagian terakhir saja.

    Path penuh selalu tersedia di tooltip. Merentangkan path penuh selebar
    panel memakan ruang besar untuk informasi yang jarang dibaca utuh.
    """
    if not path:
        return ""
    parts = os.path.normpath(path).split(os.sep)
    return "..." + os.sep + os.sep.join(parts[-2:]) if len(parts) > 2 else path


class Badge(QLabel):
    """Lencana keadaan di kepala modul. Warna mengikuti arti, bukan hiasan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_state("off", "MATI")

    def set_state(self, kind, text):
        colors = {
            "live": (theme.OK, "#04231a", 700),
            "warn": (theme.STANDBY, "#241800", 700),
            "off": (theme.V4, theme.T3, 600),
            "info": (theme.V4, theme.T2, 600),
        }
        background, foreground, weight = colors.get(kind, colors["off"])
        self.setText(text)
        theme.paint(self, f"background:{background};color:{foreground};"
                          f"font-family:{theme.MONO};font-size:10px;font-weight:{weight};"
                          f"padding:3px 7px;border-radius:2px;")


class Module(QWidget):
    """Satu modul rak: kepala (judul + lencana) dan badan."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        theme.paint(self, f"background:{theme.V2};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        head = QWidget()
        theme.paint(head, f"background:{theme.V3};border-bottom:1px solid {theme.SEAM};")
        hb = QHBoxLayout(head)
        hb.setContentsMargins(14, 8, 14, 8)
        hb.setSpacing(10)
        name = QLabel(title)
        theme.paint(name, f"color:{theme.T1};font-size:12px;font-weight:600;"
                          f"background:transparent;")
        self.note = QLabel("")
        theme.paint(self.note, f"color:{theme.T4};font-size:11px;background:transparent;")
        self.badge = Badge()
        hb.addWidget(name)
        hb.addWidget(self.note)
        hb.addStretch(1)
        hb.addWidget(self.badge)
        outer.addWidget(head)

        body = QWidget()
        theme.paint(body, "background:transparent;")
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(14, 12, 14, 14)
        self.body.setSpacing(6)
        outer.addWidget(body)
        outer.addStretch(1)

    # --- pembantu isi modul ---

    def field(self, label, *widgets):
        """Baris: label sempit di kiri, kontrol di kanan."""
        row = QWidget()
        theme.paint(row, "background:transparent;")
        box = QHBoxLayout(row)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(9)
        if label:
            name = QLabel(label)
            name.setFixedWidth(84)
            theme.paint(name, f"color:{theme.T3};font-size:11.5px;background:transparent;")
            box.addWidget(name)
        for widget in widgets:
            box.addWidget(widget)
        self.body.addWidget(row)
        return box

    def line(self, *widgets, spacing=9):
        """Baris tanpa label kiri."""
        row = QWidget()
        theme.paint(row, "background:transparent;")
        box = QHBoxLayout(row)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(spacing)
        for widget in widgets:
            box.addWidget(widget)
        box.addStretch(1)
        self.body.addWidget(row)
        return box

    def hint(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        theme.paint(label, f"color:{theme.T4};font-size:11px;background:transparent;")
        self.body.addWidget(label)
        return label

    def reference(self, title, columns):
        """
        Tabel rujukan: pasangan (kode, arti), dikelompokkan per kolom.

        `columns` adalah daftar kolom, tiap kolom daftar pasangan. Pengelompokan
        dibuat EKSPLISIT begini, bukan dengan membagi rata sejumlah kolom:
        pembagian rata memecah kelompok logis di tempat sembarang. Versi
        pertama fungsi ini membagi 13 alamat OSC jadi tiga kolom berisi 5/5/3,
        sehingga alamat blank tercampur dengan alamat lagu di kolom yang sama.

        Menggantikan paragraf mono panjang yang dulu membungkus tak terbaca.
        """
        if title:
            head = QLabel(title)
            theme.paint(head, f"color:{theme.T3};font-size:11px;background:transparent;"
                              f"border-top:1px solid {theme.SEAM};padding-top:8px;")
            self.body.addWidget(head)

        grid_host = QWidget()
        theme.paint(grid_host, "background:transparent;")
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 3, 0, 0)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(2)

        for column_index, entries in enumerate(columns):
            for row, (code, meaning) in enumerate(entries):
                code_label = QLabel(code)
                theme.paint(code_label, f"color:{theme.T2};font-family:{theme.MONO};"
                                        f"font-size:11px;background:transparent;")
                meaning_label = QLabel(meaning)
                theme.paint(meaning_label, f"color:{theme.T4};font-size:11px;"
                                           f"background:transparent;")
                grid.addWidget(code_label, row, column_index * 2)
                grid.addWidget(meaning_label, row, column_index * 2 + 1)
            grid.setColumnStretch(column_index * 2 + 1, 1)
        self.body.addWidget(grid_host)
        return grid_host


class SettingsView(QWidget):
    settingsChanged = Signal()
    libraryPathChanged = Signal(str)
    globalHotkeyToggled = Signal(bool)      # REQ-F-PLAY-07
    oscToggled = Signal(bool, int)          # REQ-F-RC-01 (aktif, port)
    midiToggled = Signal(bool, int)         # REQ-F-RC-02 (aktif, index port)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Latar berwarna seam + jarak 1px = garis pemisah setipis rambut,
        # tanpa perlu menggambar border di tiap modul.
        rack = QWidget()
        theme.paint(rack, f"background:{theme.SEAM};")
        grid = QGridLayout(rack)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(1)
        grid.setVerticalSpacing(1)

        grid.addWidget(self._build_output(), 0, 0)
        grid.addWidget(self._build_storage(), 0, 1)
        grid.addWidget(self._build_hotkey(), 1, 0)
        grid.addWidget(self._build_midi(), 1, 1)
        grid.addWidget(self._build_osc(), 2, 0, 1, 2)   # selebar penuh
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        root.addWidget(rack)

        if settings.load_error:
            warning = QLabel(f"⚠ {settings.load_error}. Dipakai nilai default.")
            warning.setWordWrap(True)
            theme.paint(warning, f"color:{theme.STANDBY};padding:10px 16px;font-size:11px;"
                                 f"background:{theme.V2};border-top:1px solid {theme.SEAM};")
            root.addWidget(warning)

        root.addStretch(1)
        self.refresh_state()

    # ---------- pembantu kontrol ----------

    def _line_edit(self, text, width=None, mono=False):
        widget = QLineEdit(text)
        if width:
            widget.setFixedWidth(width)
        if mono:
            widget.setStyleSheet(f"font-family:{theme.MONO};font-size:11px;")
        return widget

    def _spin(self, low, high, value, width=66):
        widget = QSpinBox()
        widget.setRange(low, high)
        widget.setValue(value)
        widget.setFixedWidth(width)
        widget.setButtonSymbols(QSpinBox.NoButtons)
        widget.setAlignment(Qt.AlignRight)
        return widget

    def _quiet(self, text, tooltip=None):
        button = QPushButton(text)
        button.setProperty("variant", "quiet")
        if tooltip:
            button.setToolTip(tooltip)
        return button

    def _small(self, text, color=None, mono=False):
        label = QLabel(text)
        css = f"color:{color or theme.T3};font-size:11px;background:transparent;"
        if mono:
            css += f"font-family:{theme.MONO};"
        theme.paint(label, css)
        return label

    # ---------- modul: Output ----------

    def _build_output(self):
        module = Module("Output Spout")
        self.output_module = module

        self.sender_input = self._line_edit(self.settings.spout_sender_name, 170)
        self.sender_input.editingFinished.connect(self._commit)
        module.field("Sender name", self.sender_input)
        module.body.itemAt(module.body.count() - 1).widget().layout().addStretch(1)

        self.width_input = self._spin(160, 7680, self.settings.output_width, 64)
        self.height_input = self._spin(90, 4320, self.settings.output_height, 64)
        self.fps_input = QComboBox()
        self.fps_input.addItems(["24", "25", "30", "50", "60"])
        self.fps_input.setCurrentText(str(self.settings.fps))
        self.fps_input.setFixedWidth(66)
        for widget in (self.width_input, self.height_input):
            widget.editingFinished.connect(self._commit)
        self.fps_input.currentTextChanged.connect(lambda _: self._commit())

        box = module.field("Resolusi", self.width_input, self._small("x", theme.T4),
                           self.height_input, self._small("FPS"), self.fps_input)
        box.addStretch(1)
        module.hint("Muncul di Resolume pada Sources, lalu Spout. "
                    "Resolusi hanya bisa diubah saat output berhenti.")
        return module

    # ---------- modul: Penyimpanan ----------

    def _build_storage(self):
        module = Module("Penyimpanan")
        self.storage_module = module

        self.library_input = self._line_edit(self.settings.library_path, mono=True)
        self.shows_input = self._line_edit(self.settings.shows_path, mono=True)
        for widget in (self.library_input, self.shows_input):
            widget.setReadOnly(True)
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._refresh_path_display()

        module.field("Library", self.library_input,
                     self._quiet("Ubah"), self._quiet("Buka"))
        module.body.itemAt(module.body.count() - 1).widget().layout().itemAt(2).widget()\
            .clicked.connect(self._pick_library)
        module.body.itemAt(module.body.count() - 1).widget().layout().itemAt(3).widget()\
            .clicked.connect(lambda: self._reveal(self.settings.library_path))

        module.field("Shows", self.shows_input,
                     self._quiet("Ubah"), self._quiet("Buka"))
        module.body.itemAt(module.body.count() - 1).widget().layout().itemAt(2).widget()\
            .clicked.connect(self._pick_shows)
        module.body.itemAt(module.body.count() - 1).widget().layout().itemAt(3).widget()\
            .clicked.connect(lambda: self._reveal(self.settings.shows_path))

        module.hint("Path dipendekkan. Lengkapnya muncul saat disentuh kursor. "
                    "Satu file .showproject.json per show.")
        return module

    def _refresh_path_display(self):
        for widget, path in ((self.library_input, self.settings.library_path),
                             (self.shows_input, self.settings.shows_path)):
            widget.setText(_short_path(path))
            widget.setToolTip(path)

    # ---------- modul: Hotkey ----------

    def _build_hotkey(self):
        from ui.global_hotkey import is_supported, DEFAULT_BINDINGS

        module = Module("Hotkey")
        self.hotkey_module = module

        globals_by_name = {name: label for name, _, _, label in DEFAULT_BINDINGS}
        module.reference(None, [
            [("Space", "play / pause"),
             ("Kiri / Kanan", "pindah baris"),
             ("B", "blank")],
            [(globals_by_name.get("play_pause", ""), "global"),
             ("Ctrl+Alt+Kiri / Kanan", "global"),
             (globals_by_name.get("blank", ""), "global")],
        ])

        self.global_hotkey_box = SegmentedToggle()
        self.global_hotkey_box.setChecked(self.settings.global_hotkey_enabled)
        self.global_hotkey_box.toggled.connect(self._on_global_hotkey_toggled)
        self.global_hotkey_status = self._small("", theme.STANDBY)
        module.line(self._small("Hotkey global", theme.T3),
                    self.global_hotkey_box, self.global_hotkey_status)

        if not is_supported():
            self.global_hotkey_box.setEnabled(False)
            self.global_hotkey_box.setToolTip("Hotkey global hanya tersedia di Windows.")

        module.hint("Kombinasi global sengaja berbeda. Hotkey global bersifat eksklusif "
                    "se-sistem, jadi mendaftarkan Space polos akan mematikan tombol spasi "
                    "di seluruh Windows.")
        return module

    def _on_global_hotkey_toggled(self, enabled):
        self.settings.global_hotkey_enabled = enabled
        self.settings.save()
        self.globalHotkeyToggled.emit(enabled)
        self.refresh_state()

    def show_global_hotkey_problem(self, message):
        self.global_hotkey_status.setText(message)
        self.refresh_state()

    # ---------- modul: MIDI ----------

    def _build_midi(self):
        from remote.midi_listener import MIDI_AVAILABLE, available_ports, note_map_help

        module = Module("MIDI")
        self.midi_module = module

        self.midi_port = QComboBox()
        self.midi_port.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ports = available_ports()
        if ports:
            for index, name in enumerate(ports):
                self.midi_port.addItem(name, index)
            self.midi_port.setCurrentIndex(min(self.settings.midi_port_index, len(ports) - 1))
        else:
            self.midi_port.addItem("(tidak ada device terdeteksi)", 0)
            self.midi_port.setEnabled(False)
        self.midi_port.currentIndexChanged.connect(self._on_midi_toggled)

        rescan = self._quiet("Scan", "Device yang dicolok setelah aplikasi dibuka "
                                     "tidak muncul sendiri.")
        rescan.clicked.connect(self._rescan_midi)
        module.field("Device", self.midi_port, rescan)

        self.midi_box = SegmentedToggle()
        self.midi_box.setChecked(self.settings.midi_enabled)
        self.midi_box.toggled.connect(self._on_midi_toggled)
        self.midi_status = self._small("", theme.STANDBY)
        module.line(self.midi_box, self.midi_status)

        notes = [(str(note), command.replace("_", " "))
                 for note, command in note_map_help()]
        half = (len(notes) + 1) // 2
        module.reference("Peta note", [notes[:half], notes[half:]])

        if not MIDI_AVAILABLE:
            for widget in (self.midi_box, self.midi_port, rescan):
                widget.setEnabled(False)
            self.midi_box.setToolTip("python-rtmidi belum terpasang.\n"
                                     "pip install python-rtmidi")
        elif not ports:
            self.midi_box.setEnabled(False)
            self.midi_box.setToolTip("Tidak ada device MIDI terdeteksi. "
                                     "Colok device lalu tekan Scan.")
        return module

    def _rescan_midi(self):
        from remote.midi_listener import available_ports
        ports = available_ports()
        self.midi_port.blockSignals(True)
        self.midi_port.clear()
        if ports:
            for index, name in enumerate(ports):
                self.midi_port.addItem(name, index)
            self.midi_port.setEnabled(True)
            self.midi_box.setEnabled(True)
            self.midi_status.setText(f"{len(ports)} device ditemukan")
        else:
            self.midi_port.addItem("(tidak ada device terdeteksi)", 0)
            self.midi_port.setEnabled(False)
            self.midi_box.setEnabled(False)
            self.midi_status.setText("masih tidak ada device")
        self.midi_port.blockSignals(False)
        self.refresh_state()

    def _on_midi_toggled(self, *_):
        self.settings.midi_enabled = self.midi_box.isChecked()
        self.settings.midi_port_index = max(0, self.midi_port.currentIndex())
        self.settings.save()
        self.midiToggled.emit(self.settings.midi_enabled, self.settings.midi_port_index)
        self.refresh_state()

    def show_midi_status(self, message):
        self.midi_status.setText(message)
        self.refresh_state()

    # ---------- modul: OSC (selebar penuh) ----------

    def _build_osc(self):
        from remote.osc_listener import DEFAULT_PORT, ADDRESS_MAP

        module = Module("OSC")
        self.osc_module = module

        self.osc_box = SegmentedToggle()
        self.osc_box.setChecked(self.settings.osc_enabled)
        self.osc_box.toggled.connect(self._on_osc_toggled)
        self.osc_port = self._spin(1024, 65535, self.settings.osc_port or DEFAULT_PORT)
        self.osc_port.editingFinished.connect(self._on_osc_toggled)
        self.osc_status = self._small("", theme.STANDBY)
        module.line(self.osc_box, self._small("Port"), self.osc_port, self.osc_status)

        # Dikelompokkan menurut fungsi, bukan diurutkan abjad: operator mencari
        # "yang mana untuk blank", bukan "yang mana huruf b".
        arguments = {"/cuevo/song/goto": "nomor lagu",
                     "/cuevo/offset": "detik",
                     "/cuevo/offset/nudge": "detik"}
        groups = (("/cuevo/play", "/cuevo/pause", "/cuevo/playpause",
                   "/cuevo/next", "/cuevo/prev"),
                  ("/cuevo/blank", "/cuevo/blank/on", "/cuevo/blank/off"),
                  ("/cuevo/song/next", "/cuevo/song/prev", "/cuevo/song/goto",
                   "/cuevo/offset", "/cuevo/offset/nudge"))
        columns = [[(address, arguments.get(address, ""))
                    for address in group if address in ADDRESS_MAP]
                   for group in groups]
        module.reference("Alamat yang diterima", columns)

        # Kalau nanti ada alamat baru di ADDRESS_MAP tapi lupa dimasukkan ke
        # `groups`, alamat itu tidak akan pernah muncul di layar. Lebih baik
        # ketahuan sekarang daripada operator mengira alamatnya tidak ada.
        listed = {address for group in groups for address in group}
        missing = sorted(set(ADDRESS_MAP) - listed)
        if missing:
            module.hint("Belum dikelompokkan: " + "  ".join(missing))
        module.hint("Bentrokan port dilaporkan, bukan didiamkan. Pesan bernilai nol "
                    "tetap diterima untuk alamat berargumen, misalnya reset offset ke 0.")
        return module

    def _on_osc_toggled(self, *_):
        self.settings.osc_enabled = self.osc_box.isChecked()
        self.settings.osc_port = self.osc_port.value()
        self.settings.save()
        self.oscToggled.emit(self.settings.osc_enabled, self.settings.osc_port)
        self.refresh_state()

    def show_osc_status(self, message):
        self.osc_status.setText(message)
        self.refresh_state()

    # ---------- keadaan lencana ----------

    def refresh_state(self, output_running=None, song_count=None, show_count=None):
        """
        Perbarui lencana tiap modul.

        Dipanggil `app.py` tiap 500ms dengan keadaan sebenarnya. Argumen yang
        None berarti "tidak diketahui dari sini" dan lencananya dibiarkan
        netral, BUKAN ditebak. Lencana yang menebak sama saja berbohong.
        """
        if output_running is not None:
            self.output_module.badge.set_state(
                "live" if output_running else "off",
                "MENGIRIM" if output_running else "BERHENTI")

        if song_count is not None and show_count is not None:
            self.storage_module.note.setText(f"{song_count} lagu, {show_count} show")
            self.storage_module.badge.set_state("info", "LOKAL")

        active = self.settings.global_hotkey_enabled
        problem = self.global_hotkey_status.text().startswith("⚠")
        self.hotkey_module.badge.set_state(
            "warn" if problem else ("live" if active else "off"),
            "BERMASALAH" if problem else ("GLOBAL AKTIF" if active else "GLOBAL MATI"))

        osc_problem = self.osc_status.text().startswith("⚠")
        osc_on = self.osc_box.isChecked()
        self.osc_module.badge.set_state(
            "warn" if osc_problem else ("live" if osc_on else "off"),
            "GAGAL" if osc_problem else (f"PORT {self.osc_port.value()}" if osc_on else "MATI"))

        midi_problem = self.midi_status.text().startswith("⚠")
        midi_on = self.midi_box.isChecked() and self.midi_box.isEnabled()
        self.midi_module.badge.set_state(
            "warn" if midi_problem else ("live" if midi_on else "off"),
            "GAGAL" if midi_problem else ("AKTIF" if midi_on else "MATI"))

    # ---------- simpan ----------

    def _pick_library(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Lokasi file library", self.settings.library_path, "JSON (*.json)")
        if not path:
            return
        self.settings.library_path = path
        self._refresh_path_display()
        self._commit()
        self.libraryPathChanged.emit(path)

    def _pick_shows(self):
        path = QFileDialog.getExistingDirectory(self, "Folder show", self.settings.shows_path)
        if path:
            self.settings.shows_path = path
            self._refresh_path_display()
            self._commit()

    def _reveal(self, path):
        folder = path if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
        os.makedirs(folder, exist_ok=True)
        if hasattr(os, "startfile"):
            os.startfile(folder)   # Windows

    def _commit(self):
        self.settings.spout_sender_name = self.sender_input.text().strip() or "CUEVO Lyrics"
        self.settings.output_width = self.width_input.value()
        self.settings.output_height = self.height_input.value()
        self.settings.fps = int(self.fps_input.currentText())
        self.settings.save()
        self.settingsChanged.emit()

    def refresh_from_settings(self):
        """Dipanggil kalau nilai diubah dari tempat lain (mis. strip di atas)."""
        self.sender_input.setText(self.settings.spout_sender_name)
        self.width_input.setValue(self.settings.output_width)
        self.height_input.setValue(self.settings.output_height)
        self.fps_input.setCurrentText(str(self.settings.fps))
        self._refresh_path_display()
