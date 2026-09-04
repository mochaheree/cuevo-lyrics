"""
Window utama CUEVO Lyrics (PySide6).

Struktur mengikuti MOCKUP.html v0.4:
  status strip  -> ON AIR / BLANK / IDLE, sender, resolusi, fps aktual, lagu
  tabs          -> Live · Library · Show · Style · Settings

Tab yang belum dibangun sengaja ditampilkan lengkap dengan fase dan
requirement-nya, bukan disembunyikan -- supaya jelas apa yang belum ada.

Jalankan: python main.py
"""
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QPushButton, QLineEdit, QSpinBox, QMessageBox,
)

from player_state import PlayerState
from render_style import DEFAULT_STYLE, RenderStyle
from spout_output import SpoutOutputThread, SPOUT_AVAILABLE
from show_session import ShowSession
from store.paths import migrate_legacy_data, resource_path
from store.library import Library
from store.settings import Settings
from store.shows import ShowStore
from store.templates import TemplateStore
from ui import theme
from ui.live_view import LiveView
from ui.library_view import LibraryView
from ui.settings_view import SettingsView
from ui.show_view import ShowView
from ui.style_view import StyleView
from ui.donate_view import DonateView
from ui.operator_view import OperatorView
from ui.cast_window import CastWindow
from ui.global_hotkey import GlobalHotkeys
from ui.remote_bridge import RemoteBridge
from remote.osc_listener import OscListener
from remote.midi_listener import MidiListener


class Placeholder(QWidget):
    """Tab yang belum dibangun -- menyebut fase dan requirement-nya."""

    def __init__(self, title, phase, requirements, parent=None):
        super().__init__(parent)
        box = QVBoxLayout(self)
        box.setContentsMargins(28, 26, 28, 26)
        box.setSpacing(8)

        head = QLabel(title)
        head.setStyleSheet(f"color:{theme.T1};font-size:15px;font-weight:600;")
        phase_label = QLabel(phase)
        phase_label.setStyleSheet(f"color:{theme.STANDBY};font-family:{theme.MONO};font-size:11px;")
        reqs = QLabel(requirements)
        reqs.setStyleSheet(f"color:{theme.T3};font-family:{theme.MONO};font-size:11px;")
        reqs.setWordWrap(True)
        note = QLabel("See MOCKUP.html for this screen's design.")
        note.setStyleSheet(f"color:{theme.T3};font-size:12px;")

        box.addWidget(head)
        box.addWidget(phase_label)
        box.addWidget(reqs)
        box.addSpacing(6)
        box.addWidget(note)
        box.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CUEVO Lyrics")
        self.resize(1280, 800)
        self.setMinimumSize(1100, 680)

        migrate_legacy_data()   # folder "LyricSpout" lama -> "CUEVO Lyrics", sekali saja
        self.settings = Settings.load()                 # REQ-F-CFG-01
        self.library = Library(self.settings.library_path)
        self.show_store = ShowStore(self.settings.shows_path)
        self.template_store = TemplateStore()
        self.show_session = ShowSession(self.library)
        self.player_state = PlayerState()
        self.style_config = self._initial_style()
        self.spout_thread = None
        self._song_title = ""
        self.operator_window = None          # REQ-F-OPS-01, window kedua
        self.cast_window = None              # REQ-F-OUT-09, jendela siar
        self.global_hotkeys = GlobalHotkeys()  # REQ-F-PLAY-07
        self.osc_listener = None             # REQ-F-RC-01
        self.midi_listener = None            # REQ-F-RC-02
        self.remote_bridge = RemoteBridge(self)
        self.remote_bridge.commandReceived.connect(self.remote_bridge.dispatch)

        root = QWidget()
        root.setObjectName("Root")
        box = QVBoxLayout(root)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        box.addWidget(self._build_strip())
        box.addWidget(self._build_tabs(), 1)
        self.setCentralWidget(root)

        self._install_shortcuts()
        self._refresh_show()
        self._restore_session_windows()

        self._strip_timer = QTimer(self)
        self._strip_timer.timeout.connect(self._refresh_strip)
        self._strip_timer.start(500)

        if not SPOUT_AVAILABLE:
            self.start_btn.setEnabled(False)
            self.start_btn.setToolTip(
                "SpoutGL/pygame not available, or you are not on Windows.\n"
                "pip install SpoutGL pygame PyOpenGL"
            )

    # ---------- status strip ----------

    def _build_strip(self):
        strip = QWidget()
        strip.setObjectName("Strip")
        theme.paint(strip,f"background:{theme.V3};border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(strip)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        self.air_label = QLabel("IDLE")
        self.air_label.setStyleSheet(self._air_style("idle"))
        box.addWidget(self.air_label)

        self.sender_name = QLineEdit(self.settings.spout_sender_name)
        self.sender_name.setFixedWidth(118)
        self.sender_name.editingFinished.connect(self._save_strip_to_settings)
        box.addWidget(self._cell("Sender", self.sender_name))

        self.res_w = QSpinBox()
        self.res_w.setRange(160, 7680)
        self.res_w.setValue(self.settings.output_width)
        self.res_h = QSpinBox()
        self.res_h.setRange(90, 4320)
        self.res_h.setValue(self.settings.output_height)
        for spin in (self.res_w, self.res_h):
            spin.editingFinished.connect(self._save_strip_to_settings)
        times = QLabel("×")
        theme.paint(times,f"color:{theme.T4};background:transparent;")
        for spin in (self.res_w, self.res_h):
            spin.setFixedWidth(70)
            spin.setButtonSymbols(QSpinBox.NoButtons)
            spin.setAlignment(Qt.AlignRight)
        box.addWidget(self._cell("Resolution", self.res_w, times, self.res_h))

        self.fps_label = QLabel("-")
        self.fps_label.setFixedWidth(38)
        theme.paint(self.fps_label,
            f"color:{theme.T2};font-family:{theme.MONO};background:transparent;"
        )
        box.addWidget(self._cell("FPS", self.fps_label))

        self.song_label = QLabel("no song loaded")
        theme.paint(self.song_label,f"color:{theme.T2};background:transparent;")
        box.addWidget(self._cell(None, self.song_label), 1)

        # REQ-F-SET-05 -- progres show, selalu terlihat di semua tab
        self.show_label = QLabel("-")
        theme.paint(self.show_label,
            f"color:{theme.T2};font-family:{theme.MONO};background:transparent;")
        box.addWidget(self._cell("Show", self.show_label))

        # REQ-F-OPS-01 -- ada di strip, bukan di dalam tab, supaya bisa
        # dibuka/ditutup dari tab mana pun tanpa berpindah dulu
        self.operator_btn = QPushButton("Operator")
        self.operator_btn.setProperty("variant", "quiet")
        self.operator_btn.setCheckable(True)
        self.operator_btn.setToolTip(
            "Second window with large NOW/NEXT text, for a separate monitor")
        self.operator_btn.toggled.connect(self._toggle_operator_window)
        box.addWidget(self._cell(None, self.operator_btn))

        # REQ-F-OUT-09 -- jendela yang bisa ditangkap OBS / TikTok Live Studio,
        # atau di-fullscreen di layar kedua. Ketiganya satu fitur yang sama.
        self.cast_btn = QPushButton("Cast")
        self.cast_btn.setProperty("variant", "quiet")
        self.cast_btn.setCheckable(True)
        self.cast_btn.setToolTip(
            "Broadcast window for OBS, TikTok Live Studio, or a second screen")
        self.cast_btn.toggled.connect(self._toggle_cast_window)
        box.addWidget(self._cell(None, self.cast_btn))

        self.start_btn = QPushButton("Start output")
        self.start_btn.clicked.connect(self.start_spout)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setProperty("variant", "quiet")
        self.stop_btn.clicked.connect(self.stop_spout)
        self.stop_btn.setEnabled(False)
        box.addWidget(self._cell(None, self.start_btn, self.stop_btn))
        return strip

    def _cell(self, label, *widgets):
        cell = QWidget()
        theme.paint(cell,f"background:transparent;border-right:1px solid {theme.SEAM};")
        box = QHBoxLayout(cell)
        box.setContentsMargins(12, 6, 12, 6)
        box.setSpacing(7)
        if label:
            text = QLabel(label)
            theme.paint(text,f"color:{theme.T3};font-size:11px;background:transparent;")
            box.addWidget(text)
        for widget in widgets:
            box.addWidget(widget)
        return cell

    def _air_style(self, state):
        """state: 'live' | 'blank' | 'idle'. Merah hanya untuk 'live'."""
        base = f"font-family:{theme.MONO};font-weight:700;font-size:11px;padding:9px 13px;"
        if state == "live":
            return base + f"background:{theme.LIVE};color:#ffffff;"
        if state == "blank":
            return base + f"background:{theme.V4};color:{theme.STANDBY};"
        return base + f"background:{theme.V4};color:{theme.T3};"

    # ---------- tabs ----------

    def _build_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.live_view = LiveView(self.player_state, self.style_config)
        self.live_view.songSelected.connect(self._goto_show_song)
        self.live_view.songStepRequested.connect(self._step_show_song)

        self.library_view = LibraryView(self.library)
        self.library_view.songLoaded.connect(self._on_song_loaded)
        self.library_view.libraryChanged.connect(self._refresh_show)
        self.library_view.addToShowRequested.connect(self._add_to_show)

        self.show_view = ShowView(self.show_session, self.show_store, self.library)
        self.show_view.showChanged.connect(self._refresh_show)

        self.style_view = StyleView(self.player_state, self.style_config,
                                    self.template_store)
        self.style_view.styleChanged.connect(self._on_style_changed)

        self.settings_view = SettingsView(self.settings)
        self.settings_view.settingsChanged.connect(self._on_settings_changed)
        self.settings_view.libraryPathChanged.connect(self._on_library_path_changed)
        self.settings_view.globalHotkeyToggled.connect(self._apply_global_hotkeys)
        self.settings_view.oscToggled.connect(self._apply_osc)
        self.settings_view.midiToggled.connect(self._apply_midi)

        self.tabs.addTab(self.live_view, "Live")
        self.tabs.addTab(self.library_view, "Library")
        self.tabs.addTab(self.show_view, "Show")
        self.tabs.addTab(self.style_view, "Style")
        self.tabs.addTab(self.settings_view, "Settings")
        self.tabs.addTab(DonateView(), "Donate")
        return self.tabs

    # ---------- hotkey (REQ-F-PLAY-06) ----------

    def _install_shortcuts(self):
        def bind(key, handler):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(handler)

        bind(Qt.Key_Space, self._toggle_play)
        bind(Qt.Key_Right, lambda: self.live_view.step_line(+1))
        bind(Qt.Key_Left, lambda: self.live_view.step_line(-1))
        bind(Qt.Key_B, self.live_view.blank_btn.toggle)

    def _toggle_play(self):
        # jangan bajak spasi saat operator sedang mengetik di kolom pencarian
        focus = QApplication.focusWidget()
        if isinstance(focus, QLineEdit):
            return
        if self.player_state.is_playing():
            self.player_state.pause()
        else:
            self.player_state.play()

    # ---------- aksi ----------

    def _on_song_loaded(self, title, lines, duration):
        """Lagu dimuat langsung dari tab Library, di luar set list."""
        self._activate_lyrics(title, lines, duration)
        self.tabs.setCurrentWidget(self.live_view)

    def _activate_lyrics(self, title, lines, duration):
        self.player_state.load_lyrics(lines, duration=duration)
        self.live_view.load_song(title, lines)
        self._song_title = title

    # ---------- navigasi Show (REQ-F-SET-03) ----------

    def _refresh_show(self):
        """Panel set list di tab Live selalu mencerminkan show yang dibuka."""
        self.live_view.set_setlist(self.show_session.songs(), self.show_session.index)

    def _add_to_show(self, song):
        """Tambah lagu dari tab Library ke show yang sedang dibuka."""
        self.show_session.add_song(song.id)
        self.show_view.refresh_songs()
        self._refresh_show()
        # sebut nama show-nya: kalau operator sedang punya beberapa show,
        # "tersimpan ke show" saja tidak cukup untuk tahu masuk ke mana
        self.library_view._show_status(
            f"“{song.title}” added to show “{self.show_session.show.name}” "
            f"(position {len(self.show_session.show.song_ids)}). "
            f"Not saved yet. Press “Save show” in the Show tab."
        )

    def _goto_show_song(self, index):
        song = self.show_session.goto(index)
        self._play_show_song(song)

    def _step_show_song(self, delta):
        song = self.show_session.step(delta)
        self._play_show_song(song)

    def _play_show_song(self, song):
        if song is None:
            return
        # Pindah lagu tidak boleh menyalakan output diam-diam: kalau operator
        # sedang BLANK, tetap BLANK sampai dia sendiri melepasnya.
        self._activate_lyrics(song.label, song.lines, song.duration_sec)
        self._refresh_show()
        self.tabs.setCurrentWidget(self.live_view)

    def _initial_style(self) -> RenderStyle:
        """
        Style awal: template default yang tersimpan (REQ-F-STYLE-02), atau
        bawaan kalau belum ada. Resolusi selalu datang dari Settings, bukan
        dari template -- memakai template dari mesin lain tidak boleh
        diam-diam mengubah resolusi output.
        """
        style = DEFAULT_STYLE
        template = self.template_store.get(self.settings.default_template_id or "")
        if template is not None:
            style = template.style
        return RenderStyle(**{
            **style.to_dict(),
            "width": self.settings.output_width,
            "height": self.settings.output_height,
        })

    def _on_style_changed(self, style):
        """Panel Style bergerak -> preview Live dan output ikut, tanpa restart."""
        self.style_config = style
        self.live_view.preview.set_style(style)
        if self.cast_window is not None:
            self.cast_window.set_style(style)
        if self.spout_thread and self.spout_thread.is_alive():
            self.spout_thread.set_style(style)      # REQ-NF-02, <100ms

    def _style_from_strip(self) -> RenderStyle:
        return RenderStyle(**{
            **self.style_config.to_dict(),
            "width": self.res_w.value(),
            "height": self.res_h.value(),
        })

    def _restore_session_windows(self):
        """
        Kembalikan keadaan yang diingat dari sesi sebelumnya (REQ-F-CFG-01):
        Operator Display terbuka, dan hotkey global aktif.

        Hotkey global dipasang belakangan lewat singleShot karena
        `RegisterHotKey` butuh window handle yang sudah benar-benar ada --
        di dalam __init__ window-nya belum ditampilkan.
        """
        if self.settings.operator_display_open:
            self.operator_btn.setChecked(True)   # memicu _toggle_operator_window
        if self.settings.cast_open:
            self.cast_btn.setChecked(True)
        if self.settings.global_hotkey_enabled:
            QTimer.singleShot(0, lambda: self._apply_global_hotkeys(True))
        if self.settings.osc_enabled:
            QTimer.singleShot(0, lambda: self._apply_osc(True, self.settings.osc_port))
        if self.settings.midi_enabled:
            QTimer.singleShot(0, lambda: self._apply_midi(
                True, self.settings.midi_port_index))

    # ---------- Operator Display (REQ-F-OPS-01/02) ----------

    def _toggle_operator_window(self, show):
        if show:
            self._open_operator_window()
        else:
            self._close_operator_window()
        self.settings.operator_display_open = show
        self.settings.save()

    def _open_operator_window(self):
        if self.operator_window is not None:
            self.operator_window.raise_()
            return
        # preview-nya mencerminkan preview tab Live, tidak merender sendiri --
        # dua render sekaligus akan menembus budget 33,3 ms (SRS §3.2)
        self.operator_window = OperatorView(
            self.player_state, self.show_session,
            mirror_of=self.live_view.preview,
        )
        self.operator_window.set_spout_thread(self.spout_thread)
        self.operator_window.closed.connect(self._on_operator_closed)
        self.operator_window.show()

    def _close_operator_window(self):
        if self.operator_window is None:
            return
        window = self.operator_window
        self.operator_window = None    # dulu, supaya closed-signal tidak berulang
        window.close()

    def _on_operator_closed(self):
        """Window ditutup lewat tombol X-nya sendiri, bukan lewat tombol strip."""
        self.operator_window = None
        if self.operator_btn.isChecked():
            self.operator_btn.blockSignals(True)
            self.operator_btn.setChecked(False)
            self.operator_btn.blockSignals(False)
        self.settings.operator_display_open = False
        self.settings.save()

    # ---------- Jendela Cast (REQ-F-OUT-09) ----------

    def _toggle_cast_window(self, show):
        if show:
            self._open_cast_window()
        else:
            self._close_cast_window()
        self.settings.cast_open = show
        self.settings.save()

    def _open_cast_window(self):
        if self.cast_window is not None:
            self.cast_window.raise_()
            return
        self.cast_window = CastWindow(
            self.player_state, self.style_config,
            background=self.settings.cast_background,
            # sumbernya sama persis dengan Operator Display: kalau output
            # jalan pakai frame kiriman, kalau tidak mencerminkan tab Live.
            # Biaya render tambahan nol (SRS §3.9).
            mirror_of=self.live_view.preview,
        )
        if self.spout_thread and self.spout_thread.is_alive():
            self.cast_window.set_mirror(None)
            self.cast_window.set_source(self.spout_thread)
        self.cast_window.closed.connect(self._on_cast_closed)
        self.cast_window.opacityFalloffFixRequested.connect(self._zero_opacity_falloff)
        self.cast_window.show()

    def _zero_opacity_falloff(self):
        """
        Diminta dari jendela Cast: nol-kan opacity falloff supaya baris konteks
        selamat melewati chroma key (lihat CastWindow._refresh_warning).

        Dijalankan lewat panel Style, bukan dengan menambal style_config
        langsung, supaya slider di tab Style ikut bergerak dan nilainya bisa
        ikut tersimpan ke Template seperti perubahan lain.
        """
        self.style_view.opacity_falloff.set_value(0.0)
        self.style_view._emit()

    def _close_cast_window(self):
        if self.cast_window is None:
            return
        window, self.cast_window = self.cast_window, None
        window.close()

    def _on_cast_closed(self):
        """Ditutup lewat tombol X-nya sendiri, bukan lewat tombol strip."""
        if self.cast_window is not None:
            self.settings.cast_background = self.cast_window.background()
        self.cast_window = None
        if self.cast_btn.isChecked():
            self.cast_btn.blockSignals(True)
            self.cast_btn.setChecked(False)
            self.cast_btn.blockSignals(False)
        self.settings.cast_open = False
        self.settings.save()

    # ---------- hotkey global (REQ-F-PLAY-07) ----------

    def _apply_global_hotkeys(self, enabled):
        self.global_hotkeys.uninstall()
        if not enabled:
            self.settings_view.show_global_hotkey_problem("")
            return
        ok, problems = self.global_hotkeys.install(self, {
            "play_pause": self._toggle_play,
            "prev_line": lambda: self.live_view.step_line(-1),
            "next_line": lambda: self.live_view.step_line(+1),
            "blank": self.live_view.blank_btn.toggle,
        })
        # Gagal daftar TIDAK boleh didiamkan: operator akan menekan tombol saat
        # live dan tidak terjadi apa-apa tanpa penjelasan (pelajaran §3.3).
        if problems:
            self.settings_view.show_global_hotkey_problem("⚠ " + "; ".join(problems))
        elif ok:
            self.settings_view.show_global_hotkey_problem("active")
        else:
            self.settings_view.show_global_hotkey_problem("⚠ registration failed")

    # ---------- remote OSC (REQ-F-RC-01) ----------

    def _remote_actions(self):
        """
        Satu daftar aksi yang dipakai bersama OSC (dan MIDI nanti), supaya
        kedua jalur remote tidak pernah menyimpang perilakunya.

        Semua ini dieksekusi di thread GUI lewat RemoteBridge -- lihat
        catatan keselamatan thread di remote/osc_listener.py.
        """
        state = self.player_state
        return {
            "play": lambda a: state.play(),
            "pause": lambda a: state.pause(),
            "play_pause": lambda a: self._toggle_play(),
            "next_line": lambda a: self.live_view.step_line(+1),
            "prev_line": lambda a: self.live_view.step_line(-1),
            "blank_toggle": lambda a: self.live_view.blank_btn.toggle(),
            "blank_on": lambda a: self.live_view.blank_btn.setChecked(True),
            "blank_off": lambda a: self.live_view.blank_btn.setChecked(False),
            "next_song": lambda a: self._step_show_song(+1),
            "prev_song": lambda a: self._step_show_song(-1),
            # controller mengirim nomor lagu 1-based; internal 0-based
            "goto_song": lambda a: self._goto_show_song(int(a[0]) - 1) if a else None,
            "set_offset": lambda a: state.nudge_offset(
                float(a[0]) - state.get_offset()) if a else None,
            "nudge_offset": lambda a: state.nudge_offset(float(a[0])) if a else None,
        }

    def _apply_osc(self, enabled, port):
        if self.osc_listener is not None:
            self.osc_listener.stop()
            self.osc_listener = None
        if self.midi_listener is not None:
            self.midi_listener.stop()
            self.midi_listener = None
        if not enabled:
            self.settings_view.show_osc_status("")
            return

        self.remote_bridge.set_actions(self._remote_actions())
        listener = OscListener(
            port=port,
            on_command=self.remote_bridge.emit_command,
            on_activity=self.remote_bridge.emit_activity,
        )
        ok, error = listener.start_listening()
        if not ok:
            # port dipakai aplikasi lain -> laporkan, jangan biarkan operator
            # mengira remote-nya aktif padahal tidak (pelajaran §3.3)
            self.settings_view.show_osc_status(f"⚠ failed: {error}")
            return
        self.osc_listener = listener
        self.settings_view.show_osc_status(f"listening on UDP {port}")

    def _apply_midi(self, enabled, port_index):
        if self.midi_listener is not None:
            self.midi_listener.stop()
            self.midi_listener = None
        if not enabled:
            self.settings_view.show_midi_status("")
            return

        # daftar aksi yang SAMA dengan OSC -- dua jalur remote tidak boleh
        # berperilaku berbeda untuk perintah yang sama
        self.remote_bridge.set_actions(self._remote_actions())
        listener = MidiListener(
            port_index=port_index,
            on_command=self.remote_bridge.emit_command,
            on_activity=self.remote_bridge.emit_activity,
        )
        ok, error = listener.start_listening()
        if not ok:
            self.settings_view.show_midi_status(f"⚠ {error}")
            return
        self.midi_listener = listener
        self.settings_view.show_midi_status(f"active: {listener.port_name}")

    # ---------- settings (REQ-F-CFG-01) ----------

    def _save_strip_to_settings(self):
        """Strip atas dan tab Settings mengedit objek Settings yang sama."""
        self.settings.spout_sender_name = self.sender_name.text().strip() or "CUEVO Lyrics"
        self.settings.output_width = self.res_w.value()
        self.settings.output_height = self.res_h.value()
        self.settings.save()
        self.settings_view.refresh_from_settings()
        # resolusi bukan milik Style; panel Style hanya perlu tahu kanvasnya
        self.style_config = self._style_from_strip()
        self.style_view.apply_resolution(self.res_w.value(), self.res_h.value())

    def _on_settings_changed(self):
        """Kebalikannya: tab Settings diubah, strip atas ikut menyesuaikan."""
        for widget, value in ((self.sender_name, self.settings.spout_sender_name),
                              (self.res_w, self.settings.output_width),
                              (self.res_h, self.settings.output_height)):
            widget.blockSignals(True)
            widget.setText(value) if isinstance(widget, QLineEdit) else widget.setValue(value)
            widget.blockSignals(False)
        self.style_config = self._style_from_strip()
        self.live_view.preview.set_style(self.style_config)

    def _on_library_path_changed(self, path):
        self.library.use_path(path)
        self.library_view.refresh_local_count()

    def start_spout(self):
        if self.spout_thread and self.spout_thread.is_alive():
            return
        self.style_config = self._style_from_strip()
        self.live_view.preview.set_style(self.style_config)
        self._save_strip_to_settings()
        self.spout_thread = SpoutOutputThread(
            self.player_state,
            sender_name=self.settings.spout_sender_name,
            style=self.style_config,
            fps=self.settings.fps,
        )
        self.spout_thread.start()
        # preview berhenti merender sendiri dan ikut menampilkan frame kiriman
        self.live_view.preview.set_source(self.spout_thread)
        if self.operator_window is not None:
            self.operator_window.set_spout_thread(self.spout_thread)
        if self.cast_window is not None:
            # pindah dari mencerminkan preview ke frame asli 1920x1080
            self.cast_window.set_mirror(None)
            self.cast_window.set_source(self.spout_thread)
        self._set_output_controls_locked(True)

    def stop_spout(self):
        self.live_view.preview.set_source(None)
        if self.operator_window is not None:
            self.operator_window.set_spout_thread(None)
        if self.cast_window is not None:
            self.cast_window.set_source(None)
            self.cast_window.set_mirror(self.live_view.preview)
        if self.spout_thread:
            self.spout_thread.stop()
            self.spout_thread.join(timeout=2)   # REQ-NF-04: berhenti bersih
            still_alive = self.spout_thread.is_alive()
            self.spout_thread = None
            if still_alive:
                QMessageBox.warning(
                    self, "Output did not stop",
                    "The Spout thread did not stop within 2 seconds.\n"
                    "Close the application if the status does not change."
                )
        self._set_output_controls_locked(False)

    def _set_output_controls_locked(self, locked):
        self.start_btn.setEnabled(SPOUT_AVAILABLE and not locked)
        self.stop_btn.setEnabled(locked)
        for widget in (self.res_w, self.res_h, self.sender_name):
            widget.setEnabled(not locked)

    # ---------- refresh strip ----------

    def _refresh_strip(self):
        running = bool(self.spout_thread and self.spout_thread.is_alive())
        blanked = self.player_state.is_blank()
        self.show_label.setText(self.show_session.position_label())

        # Lencana di tab Settings hanya boleh menampilkan keadaan yang benar-benar
        # diperiksa, jadi keadaannya didorong dari sini -- satu-satunya tempat yang
        # tahu thread Spout hidup atau tidak (SRS §3.3).
        #
        # Jumlah show butuh membaca folder dari disk, jadi hanya dihitung saat tab
        # Settings memang sedang dilihat. Timer ini berdetak 2x per detik sepanjang
        # acara; membaca disk sesering itu untuk angka yang tidak terlihat adalah
        # pemborosan yang tidak ada gunanya.
        if self.tabs.currentWidget() is self.settings_view:
            self.settings_view.refresh_state(
                output_running=running,
                song_count=len(self.library),
                show_count=len(self.show_store.list_shows()),
            )
        else:
            self.settings_view.refresh_state(output_running=running)

        if running and not blanked:
            state = "live"
            text = "ON AIR"
        elif running:
            state = "blank"
            text = "BLANK"
        else:
            state = "idle"
            text = "IDLE"
        self.air_label.setText(text)
        self.air_label.setStyleSheet(self._air_style(state))

        if running:
            self.fps_label.setText(f"{self.spout_thread.actual_fps:0.1f}")
            status = self.spout_thread.status
            if status.startswith("error") or status.startswith("SpoutGL"):
                self.song_label.setText(status)
                theme.paint(self.song_label,f"color:{theme.LIVE};background:transparent;")
                return
        else:
            self.fps_label.setText("-")

        self.song_label.setText(self._song_title or "no song loaded")
        theme.paint(self.song_label,f"color:{theme.T2};background:transparent;")

    def closeEvent(self, event):
        self.stop_spout()
        # hotkey global harus dilepas: kalau tidak, kombinasinya tetap terdaftar
        # di Windows sampai proses benar-benar mati
        self.global_hotkeys.uninstall()
        if self.osc_listener is not None:
            self.osc_listener.stop()
            self.osc_listener = None
        if self.midi_listener is not None:
            self.midi_listener.stop()
            self.midi_listener = None
        if self.cast_window is not None:
            self.settings.cast_background = self.cast_window.background()
            window, self.cast_window = self.cast_window, None
            window.close()
        if self.operator_window is not None:
            window, self.operator_window = self.operator_window, None
            window.close()
        try:
            self._save_strip_to_settings()
        except OSError:
            pass    # gagal menyimpan settings tidak boleh menghalangi aplikasi ditutup
        super().closeEvent(event)


def _set_app_icon(app):
    """
    Pasang ikon aplikasi, dan beri tahu Windows aplikasi ini berdiri sendiri.

    setWindowIcon() saja tidak cukup di Windows. Taskbar mengelompokkan
    jendela berdasarkan AppUserModelID, dan kalau tidak diisi, jendela ini
    ikut kelompok python.exe dan yang muncul di taskbar adalah ikon Python,
    bukan ikon ini. Dipanggil lewat ctypes, tidak menambah dependensi, dan
    dibungkus supaya build non-Windows tetap jalan.
    """
    icon = QIcon(resource_path("assets", "app-icon.ico"))
    if not icon.isNull():
        app.setWindowIcon(icon)

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "CUEVO.Lyrics")
        except Exception:
            pass


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CUEVO Lyrics")
    _set_app_icon(app)
    # WAJIB sebelum stylesheet() dan sebelum widget mana pun dibuat: di sinilah
    # nama font sistem diisi ke theme.SANS/theme.MONO
    theme.init_fonts()
    app.setStyleSheet(theme.stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
