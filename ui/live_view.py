"""
Screen 01 di mockup -- layar yang dipelototi 95% durasi show.

Tiga kolom, masing-masing menjawab satu pertanyaan:
  kiri   : apa selanjutnya      (set list)
  tengah : di mana kita sekarang (baris lirik, auto-scroll, klik = seek)
  kanan  : apa yang penonton lihat (preview + cue baris berikutnya)

Transport di bawah. Tombol besar hanya untuk aksi yang ditekan sambil live;
BLANK sengaja dipisah jauh dari Play supaya tidak salah pencet saat panik.
"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QSlider, QFrame, QSizePolicy,
)

from ui import theme
from ui.preview import PreviewWidget
from ui.segmented import SegmentedControl


def format_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"{m:02d}:{s:05.2f}"


def _seam(vertical=True) -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.VLine if vertical else QFrame.HLine)
    line.setFixedWidth(1) if vertical else line.setFixedHeight(1)
    theme.paint(line,f"background:{theme.SEAM};border:0;")
    return line


class Column(QWidget):
    """Kolom dengan header dan (opsional) footer, sesuai pola di mockup."""

    def __init__(self, title, right_text="", parent=None):
        super().__init__(parent)
        self._box = QVBoxLayout(self)
        self._box.setContentsMargins(0, 0, 0, 0)
        self._box.setSpacing(0)

        head = QWidget()
        head.setObjectName("ColHeadWrap")
        theme.paint(head,f"background:{theme.V3};border-bottom:1px solid {theme.SEAM};")
        hb = QHBoxLayout(head)
        hb.setContentsMargins(12, 6, 12, 6)
        self.title_label = QLabel(title)
        theme.paint(self.title_label,f"color:{theme.T3};font-size:11px;background:transparent;")
        self.right_label = QLabel(right_text)
        theme.paint(self.right_label,
            f"color:{theme.T2};font-family:{theme.MONO};font-size:11px;background:transparent;"
        )
        hb.addWidget(self.title_label)
        hb.addStretch(1)
        hb.addWidget(self.right_label)
        self._box.addWidget(head)

    def add(self, widget, stretch=0):
        self._box.addWidget(widget, stretch)

    def add_footer(self, *widgets, text=""):
        foot = QWidget()
        foot.setObjectName("Foot")
        fb = QHBoxLayout(foot)
        fb.setContentsMargins(12, 7, 12, 7)
        fb.setSpacing(6)
        for w in widgets:
            fb.addWidget(w)
        if text:
            label = QLabel(text)
            label.setObjectName("FootText")
            fb.addWidget(label)
        fb.addStretch(1)
        self._box.addWidget(foot)


class LiveView(QWidget):
    blankToggled = Signal(bool)
    songSelected = Signal(int)        # pindah ke lagu ke-N di set list
    songStepRequested = Signal(int)   # +1 / -1 lagu (REQ-F-SET-03)

    def __init__(self, player_state, style, parent=None):
        super().__init__(parent)
        self.player_state = player_state
        self._dragging_seek = False
        self._suppress_lyric_signal = False
        self._active_row = -1

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------- tiga kolom ----------
        cols = QWidget()
        cb = QHBoxLayout(cols)
        cb.setContentsMargins(0, 0, 0, 0)
        cb.setSpacing(0)

        cb.addWidget(self._build_setlist_column())
        cb.addWidget(_seam())
        cb.addWidget(self._build_lyrics_column(), 1)
        cb.addWidget(_seam())
        cb.addWidget(self._build_program_column(style))
        root.addWidget(cols, 1)

        root.addWidget(_seam(vertical=False))
        root.addWidget(self._build_transport())

        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._refresh)
        self._ui_timer.start(120)

    # ---------- kolom kiri ----------

    def _build_setlist_column(self):
        col = Column("Set list", "0/0")
        col.setFixedWidth(216)
        self.setlist = QListWidget()
        self.setlist.setUniformItemSizes(True)
        # Urutan diubah di tab Show, bukan di sini. Saat acara berjalan,
        # drag yang tidak sengaja di panel ini akan mengacak set list.
        self.setlist.itemDoubleClicked.connect(self._on_setlist_double_click)
        col.add(self.setlist, 1)

        self.prev_song_btn = QPushButton("◀ Song")
        self.prev_song_btn.setProperty("variant", "quiet")
        self.prev_song_btn.clicked.connect(lambda: self.songStepRequested.emit(-1))
        self.next_song_btn = QPushButton("Song ▶")
        self.next_song_btn.setProperty("variant", "quiet")
        self.next_song_btn.clicked.connect(lambda: self.songStepRequested.emit(+1))
        # Petunjuknya jadi tooltip, bukan label: kolom ini cuma 216px dan dua
        # tombol di atas sudah memakannya, jadi teks apa pun di sini pasti
        # terpotong. Ketahuan lewat pemeriksaan lebar teks vs lebar widget.
        self.setlist.setToolTip("Double-click a song to jump to it")
        col.add_footer(self.prev_song_btn, self.next_song_btn)
        self.setlist_col = col
        return col

    def _on_setlist_double_click(self, item):
        row = self.setlist.row(item)
        if row >= 0:
            self.songSelected.emit(row)

    def set_setlist(self, songs, current_index, done_before=True):
        """Dipanggil app.py tiap show berubah atau lagu berpindah."""
        self.setlist.clear()
        for position, song in enumerate(songs):
            marker = "▸" if position == current_index else " "
            item = QListWidgetItem(f" {marker} {position + 1:>2}  {song.label}")
            if position == current_index:
                item.setForeground(QColor("#ffffff"))
            elif done_before and position < current_index:
                item.setForeground(QColor(theme.T3))
            else:
                item.setForeground(QColor(theme.T2))
            self.setlist.addItem(item)
        total = len(songs)
        self.setlist_col.right_label.setText(
            f"{min(current_index + 1, total)}/{total}" if total else "0/0"
        )
        self.prev_song_btn.setEnabled(current_index > 0)
        self.next_song_btn.setEnabled(0 <= current_index < total - 1)

    # ---------- kolom tengah ----------

    def _build_lyrics_column(self):
        col = Column("Lyrics", "0 lines")
        self.lyrics = QListWidget()
        self.lyrics.setUniformItemSizes(True)
        self.lyrics.itemClicked.connect(self._on_lyric_clicked)  # klik = lompat
        col.add(self.lyrics, 1)
        col.add_footer(text="Click any line to jump there. Auto-scroll follows the active line.")
        self.lyrics_col = col
        return col

    def _on_lyric_clicked(self, item):
        if self._suppress_lyric_signal:
            return
        if self.player_state.is_manual_mode():
            self.player_state.goto_manual(self.lyrics.row(item))
            return
        time_sec = item.data(Qt.UserRole)
        if time_sec is None:
            return
        # yang di-seek adalah posisi mentah, jadi offset manual tetap berlaku
        self.player_state.seek(max(0.0, time_sec - self.player_state.get_offset()))

    # ---------- kolom kanan ----------

    def _build_program_column(self, style):
        col = Column("Program", "PGM")
        col.setFixedWidth(340)

        self.preview = PreviewWidget(self.player_state, style)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.preview.setFixedHeight(191)  # 340 - margin, mendekati 16:9
        wrap = QWidget()
        wb = QVBoxLayout(wrap)
        wb.setContentsMargins(10, 10, 10, 10)
        wb.addWidget(self.preview)
        theme.paint(wrap,f"background:{theme.V1};")
        col.add(wrap)

        bar = QLabel("same frame Resolume gets. Checkerboard means transparent.")
        theme.paint(bar,
            f"background:{theme.V3};color:{theme.T4};font-family:{theme.MONO};"
            f"font-size:10px;padding:6px 12px;border-top:1px solid {theme.SEAM};"
        )
        col.add(bar)

        cue = QWidget()
        theme.paint(cue,f"background:{theme.V2};border-top:1px solid {theme.SEAM};")
        cb = QVBoxLayout(cue)
        cb.setContentsMargins(12, 9, 12, 9)
        cb.setSpacing(5)
        key = QLabel("NEXT")
        key.setProperty("role", "cue-key")
        key.setStyleSheet(f"color:{theme.STANDBY};font-family:{theme.MONO};font-size:11px;")
        self.next_line_label = QLabel("-")
        self.next_line_label.setStyleSheet(f"color:{theme.T1};font-size:14px;font-weight:600;")
        self.next_line_label.setWordWrap(True)
        cb.addWidget(key)
        cb.addWidget(self.next_line_label)
        col.add(cue)
        col.add(QWidget(), 1)
        return col

    # ---------- transport ----------

    def _build_transport(self):
        panel = QWidget()
        theme.paint(panel,f"background:{theme.V1};")
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        # baris 1: mode + offset
        row1 = QWidget()
        r1 = QHBoxLayout(row1)
        r1.setContentsMargins(12, 8, 12, 8)
        r1.setSpacing(7)
        mode_label = QLabel("Mode")
        mode_label.setProperty("role", "dim")
        mode_label.setStyleSheet(f"color:{theme.T3};font-size:11px;")
        self.mode_seg = SegmentedControl(["Auto-timestamp", "Manual per-line"])
        self.mode_auto = self.mode_seg.button(0)
        self.mode_manual = self.mode_seg.button(1)
        self.mode_auto.setChecked(True)
        self.mode_manual.setToolTip(
            "For songs without a steady tempo (a cappella, rubato): timestamps are "
            "ignored, lines advance only when you press Next/Prev."
        )
        self.mode_manual.toggled.connect(self._on_mode_changed)

        r1.addWidget(mode_label)
        r1.addWidget(self.mode_seg)
        r1.addSpacing(14)

        off_label = QLabel("Offset")
        off_label.setStyleSheet(f"color:{theme.T3};font-size:11px;")
        self.offset_label = QLabel("+0.00s")
        self.offset_label.setStyleSheet(
            f"color:{theme.STANDBY};font-family:{theme.MONO};font-size:12px;"
        )
        r1.addWidget(off_label)
        r1.addWidget(self.offset_label)
        for text, delta in (("−0.5", -0.5), ("−0.1", -0.1), ("+0.1", 0.1), ("+0.5", 0.5)):
            btn = QPushButton(text)
            btn.setProperty("variant", "quiet")
            btn.clicked.connect(lambda _=False, d=delta: self.player_state.nudge_offset(d))
            r1.addWidget(btn)
        r1.addStretch(1)
        hint = QLabel("Space play   ← →  line   B blank")
        hint.setStyleSheet(f"color:{theme.T4};font-family:{theme.MONO};font-size:10px;")
        r1.addWidget(hint)
        box.addWidget(row1)
        box.addWidget(_seam(vertical=False))

        # baris 2: transport
        row2 = QWidget()
        r2 = QHBoxLayout(row2)
        r2.setContentsMargins(12, 8, 12, 8)
        r2.setSpacing(7)
        self.prev_btn = QPushButton("◀ Prev")
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.next_btn = QPushButton("Next ▶")
        self.prev_btn.setProperty("variant", "transport")
        self.play_btn.setProperty("variant", "go")
        self.pause_btn.setProperty("variant", "transport")
        self.next_btn.setProperty("variant", "transport")
        self.play_btn.clicked.connect(self.player_state.play)
        self.pause_btn.clicked.connect(self.player_state.pause)
        self.prev_btn.clicked.connect(lambda: self.step_line(-1))
        self.next_btn.clicked.connect(lambda: self.step_line(+1))
        for btn in (self.prev_btn, self.play_btn, self.pause_btn, self.next_btn):
            r2.addWidget(btn)
        r2.addStretch(1)

        self.blank_btn = QPushButton("BLANK")
        self.blank_btn.setProperty("variant", "kill")
        self.blank_btn.setCheckable(True)
        self.blank_btn.toggled.connect(self._on_blank)
        r2.addWidget(self.blank_btn)
        box.addWidget(row2)
        box.addWidget(_seam(vertical=False))

        # baris 3: scrub
        row3 = QWidget()
        r3 = QHBoxLayout(row3)
        r3.setContentsMargins(12, 8, 12, 10)
        r3.setSpacing(9)
        self.pos_label = QLabel("00:00.00")
        self.pos_label.setStyleSheet(f"color:{theme.T1};font-family:{theme.MONO};font-size:13px;")
        self.dur_label = QLabel("00:00.00")
        self.dur_label.setStyleSheet(f"color:{theme.T3};font-family:{theme.MONO};font-size:13px;")
        self.seek = QSlider(Qt.Horizontal)
        self.seek.setRange(0, 1000)
        self.seek.sliderPressed.connect(lambda: setattr(self, "_dragging_seek", True))
        self.seek.sliderReleased.connect(self._on_seek_released)
        r3.addWidget(self.pos_label)
        r3.addWidget(self.seek, 1)
        r3.addWidget(self.dur_label)
        box.addWidget(row3)
        return panel

    # ---------- aksi ----------

    def _on_blank(self, checked):
        # Ditulis ke PlayerState supaya thread Spout ikut mengosongkan output.
        # Sebelumnya hanya preview yang dikosongkan -- operator melihat layar
        # gelap sementara Resolume tetap menampilkan lirik (SRS §3.3).
        self.player_state.set_blank(checked)
        self.blankToggled.emit(checked)

    def _on_mode_changed(self, manual):
        self.player_state.set_manual_mode(manual)
        self.prev_btn.setText("◀ Prev" if not manual else "◀ Line")
        self.next_btn.setText("Next ▶" if not manual else "Line ▶")
        # di mode manual jam tidak menentukan apa-apa, jadi jangan beri kesan
        # transport waktu masih mengendalikan tampilan
        for widget in (self.play_btn, self.pause_btn, self.seek):
            widget.setEnabled(not manual)

    def _on_seek_released(self):
        self._dragging_seek = False
        duration = self.player_state.get_duration()
        if duration > 0:
            self.player_state.seek(self.seek.value() / 1000.0 * duration)

    def step_line(self, direction):
        """
        Prev/Next line.

        Mode auto  : jam di-seek ke timestamp baris tetangga, jadi lirik dan
                     lagu tetap sinkron setelahnya.
        Mode manual: jam tidak disentuh sama sekali -- baris aktif memang
                     ditentukan operator (REQ-F-PLAY-05).
        """
        lines = self.player_state.get_lines()
        if not lines:
            return
        if self.player_state.is_manual_mode():
            self.player_state.step_manual(direction)
            return
        index = self.player_state.get_active_index(self.player_state.get_current_time())
        target = max(0, min(len(lines) - 1, index + direction))
        self.player_state.seek(max(0.0, lines[target][0] - self.player_state.get_offset()))

    # ---------- dipanggil dari luar ----------

    def load_song(self, title, lines):
        self.lyrics_col.title_label.setText(title)
        self.lyrics_col.right_label.setText(f"{len(lines)} lines")
        self._suppress_lyric_signal = True
        self.lyrics.clear()
        for time_sec, text in lines:
            item = QListWidgetItem(f"{format_time(time_sec)}   {text}")
            item.setData(Qt.UserRole, time_sec)
            item.setSizeHint(item.sizeHint().boundedTo(item.sizeHint()))
            self.lyrics.addItem(item)
        self._suppress_lyric_signal = False
        self._active_row = -1

    # ---------- refresh berkala ----------

    def _refresh(self):
        position = self.player_state.get_raw_position()
        duration = self.player_state.get_duration()
        self.pos_label.setText(format_time(position))
        self.dur_label.setText(format_time(duration))
        if not self._dragging_seek and duration > 0:
            self.seek.setValue(int(position / duration * 1000))
        self.offset_label.setText(f"{self.player_state.get_offset():+.2f}s")

        index = self.player_state.get_active_index(self.player_state.get_current_time())
        if index != self._active_row:
            self._active_row = index
            if 0 <= index < self.lyrics.count():
                self._suppress_lyric_signal = True
                self.lyrics.setCurrentRow(index)
                self.lyrics.scrollToItem(
                    self.lyrics.item(index), QListWidget.PositionAtCenter
                )
                self._suppress_lyric_signal = False

        lines = self.player_state.get_lines()
        if 0 <= index + 1 < len(lines):
            self.next_line_label.setText(lines[index + 1][1] or "-")
        else:
            self.next_line_label.setText("-")
