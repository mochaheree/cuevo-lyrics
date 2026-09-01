"""
Screen 03 di mockup -- editor lirik manual (REQ-F-LIB-03, Must).

Cara kerjanya sengaja meniru software karaoke sederhana: tempel teks
lirik, putar lagunya di aplikasi lain (Spotify/DJ set/apa pun), lalu tekan
Enter tiap kali baris berganti. Satu tombol, satu tugas -- operator tidak
perlu mengetik angka waktu sama sekali.

Jam di sini memakai `PlayerState` yang sama dengan mode live, tapi
instance-nya sendiri, supaya proses menandai waktu tidak mengganggu apa
pun yang sedang tayang.
"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QColor
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QPlainTextEdit, QListWidget, QListWidgetItem, QSlider, QFrame, QMessageBox,
    QDoubleSpinBox,
)

from lrc_parser import format_lrc
from player_state import PlayerState
from store.library import Song
from ui import theme


def format_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    return f"{int(seconds // 60):02d}:{seconds - int(seconds // 60) * 60:05.2f}"


def parse_duration(text: str) -> float:
    """Terima 'mm:ss', 'mm:ss.cc', atau detik polos."""
    text = (text or "").strip()
    if not text:
        return 0.0
    try:
        if ":" in text:
            minutes, _, seconds = text.partition(":")
            return max(0.0, int(minutes) * 60 + float(seconds))
        return max(0.0, float(text))
    except ValueError:
        return 0.0


class LyricEditor(QDialog):
    songSaved = Signal(object)   # Song

    def __init__(self, library, song=None, parent=None):
        super().__init__(parent)
        self.library = library
        self.song = song
        self.clock = PlayerState()
        self._lines = list(song.lines) if song else []   # [(time|None, text)]
        self._entries = []                                # [[time_or_None, text]]

        self.setWindowTitle("Editor lirik")
        self.setModal(True)
        self.resize(1000, 660)
        self.setStyleSheet(theme.stylesheet())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_strip())
        root.addWidget(self._build_meta_bar())
        root.addWidget(self._build_columns(), 1)
        root.addWidget(self._build_transport())

        QShortcut(QKeySequence(Qt.Key_Return), self, self.tap)
        QShortcut(QKeySequence(Qt.Key_Enter), self, self.tap)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(80)

        if song:
            self._load_song(song)
        self._rebuild_entry_list()

    # ---------- header ----------

    def _build_strip(self):
        strip = QWidget()
        theme.paint(strip,f"background:{theme.V3};border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(strip)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        tag = QLabel("EDIT")
        theme.paint(tag,
            f"background:{theme.V4};color:{theme.T3};font-family:{theme.MONO};"
            f"font-weight:700;font-size:11px;padding:9px 13px;"
        )
        box.addWidget(tag)

        self.progress_label = QLabel("0/0 baris ditandai")
        theme.paint(self.progress_label,
            f"color:{theme.T2};background:transparent;padding:9px 13px;"
        )
        box.addWidget(self.progress_label)
        box.addStretch(1)

        export_btn = QPushButton("Ekspor .lrc")
        export_btn.setProperty("variant", "quiet")
        export_btn.clicked.connect(self.export_lrc)
        cancel_btn = QPushButton("Batal")
        cancel_btn.setProperty("variant", "quiet")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Simpan ke library")
        save_btn.clicked.connect(self.save)

        wrap = QWidget()
        wb = QHBoxLayout(wrap)
        wb.setContentsMargins(12, 6, 12, 6)
        wb.setSpacing(7)
        for btn in (export_btn, cancel_btn, save_btn):
            wb.addWidget(btn)
        box.addWidget(wrap)
        return strip

    def _build_meta_bar(self):
        bar = QWidget()
        theme.paint(bar,f"background:{theme.V2};border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(bar)
        box.setContentsMargins(12, 9, 12, 9)
        box.setSpacing(7)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("judul lagu")
        self.title_input.setMinimumWidth(210)
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("artis (opsional)")
        self.artist_input.setMinimumWidth(170)
        self.duration_input = QLineEdit("03:20")
        self.duration_input.setFixedWidth(78)
        self.duration_input.editingFinished.connect(self._apply_duration)

        for label, widget in (("Judul", self.title_input),
                              ("Artis", self.artist_input),
                              ("Durasi", self.duration_input)):
            text = QLabel(label)
            text.setStyleSheet(f"color:{theme.T3};font-size:11px;")
            box.addWidget(text)
            box.addWidget(widget)
        box.addStretch(1)
        return bar

    # ---------- dua kolom ----------

    def _build_columns(self):
        wrap = QWidget()
        box = QHBoxLayout(wrap)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        box.addWidget(self._build_raw_column(), 1)

        seam = QFrame()
        seam.setFixedWidth(1)
        theme.paint(seam,f"background:{theme.SEAM};")
        box.addWidget(seam)

        box.addWidget(self._build_result_column(), 1)
        return wrap

    def _column_head(self, title, right=""):
        head = QWidget()
        theme.paint(head,f"background:{theme.V3};border-bottom:1px solid {theme.SEAM};")
        hb = QHBoxLayout(head)
        hb.setContentsMargins(12, 6, 12, 6)
        left = QLabel(title)
        theme.paint(left,f"color:{theme.T3};font-size:11px;background:transparent;")
        right_label = QLabel(right)
        theme.paint(right_label,
            f"color:{theme.T2};font-family:{theme.MONO};font-size:11px;background:transparent;"
        )
        hb.addWidget(left)
        hb.addStretch(1)
        hb.addWidget(right_label)
        return head, right_label

    def _build_raw_column(self):
        col = QWidget()
        box = QVBoxLayout(col)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        head, self.raw_count_label = self._column_head("Teks mentah", "0")
        box.addWidget(head)

        self.raw_text = QPlainTextEdit()
        self.raw_text.setPlaceholderText(
            "Tempel lirik di sini, satu baris per baris nyanyian.\n\n"
            "Lalu tekan “Pecah jadi baris”."
        )
        theme.paint(self.raw_text,
            f"background:{theme.V1};color:{theme.T2};border:1px solid {theme.V4};"
            f"padding:10px;font-size:12px;"
        )
        self.raw_text.textChanged.connect(self._update_raw_count)
        wrap = QWidget()
        wb = QVBoxLayout(wrap)
        wb.setContentsMargins(12, 10, 12, 10)
        wb.addWidget(self.raw_text)
        box.addWidget(wrap, 1)

        foot = QWidget()
        theme.paint(foot,f"background:{theme.V3};border-top:1px solid {theme.SEAM};")
        fb = QHBoxLayout(foot)
        fb.setContentsMargins(12, 7, 12, 7)
        split_btn = QPushButton("Pecah jadi baris")
        split_btn.setProperty("variant", "quiet")
        split_btn.clicked.connect(self.split_lines)
        fb.addWidget(split_btn)
        fb.addStretch(1)
        box.addWidget(foot)
        return col

    def _build_result_column(self):
        col = QWidget()
        box = QVBoxLayout(col)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        head, self.result_count_label = self._column_head("Hasil", "0/0")
        box.addWidget(head)

        self.entry_list = QListWidget()
        self.entry_list.setUniformItemSizes(True)
        self.entry_list.itemDoubleClicked.connect(self._seek_to_entry)
        box.addWidget(self.entry_list, 1)

        foot = QWidget()
        theme.paint(foot,f"background:{theme.V3};border-top:1px solid {theme.SEAM};")
        fb = QHBoxLayout(foot)
        fb.setContentsMargins(12, 7, 12, 7)
        fb.setSpacing(6)

        clear_btn = QPushButton("Hapus tanda")
        clear_btn.setProperty("variant", "quiet")
        clear_btn.setToolTip("Hapus timestamp baris yang dipilih")
        clear_btn.clicked.connect(self.clear_selected_mark)
        fb.addWidget(clear_btn)

        # REQ-F-LIB-05 -- geser semua timestamp sekaligus
        shift_label = QLabel("Geser semua")
        shift_label.setStyleSheet(f"color:{theme.T3};font-size:11px;")
        self.shift_amount = QDoubleSpinBox()
        self.shift_amount.setRange(-60.0, 60.0)
        self.shift_amount.setSingleStep(0.1)
        self.shift_amount.setValue(1.0)
        self.shift_amount.setSuffix(" s")
        self.shift_amount.setFixedWidth(78)
        minus_btn = QPushButton("−")
        plus_btn = QPushButton("+")
        for btn in (minus_btn, plus_btn):
            btn.setProperty("variant", "quiet")
            btn.setFixedWidth(28)
        minus_btn.clicked.connect(lambda: self.shift_all(-self.shift_amount.value()))
        plus_btn.clicked.connect(lambda: self.shift_all(+self.shift_amount.value()))
        fb.addWidget(shift_label)
        fb.addWidget(minus_btn)
        fb.addWidget(self.shift_amount)
        fb.addWidget(plus_btn)
        fb.addStretch(1)
        box.addWidget(foot)
        return col

    # ---------- transport + TAP ----------

    def _build_transport(self):
        panel = QWidget()
        theme.paint(panel,f"background:{theme.V1};border-top:1px solid {theme.SEAM};")
        box = QVBoxLayout(panel)
        box.setContentsMargins(12, 8, 12, 12)
        box.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(7)
        play_btn = QPushButton("Play")
        play_btn.setProperty("variant", "go")
        play_btn.clicked.connect(self.clock.play)
        pause_btn = QPushButton("Pause")
        pause_btn.setProperty("variant", "transport")
        pause_btn.clicked.connect(self.clock.pause)
        reset_btn = QPushButton("Ke awal")
        reset_btn.setProperty("variant", "quiet")
        reset_btn.clicked.connect(self.clock.stop)

        self.pos_label = QLabel("00:00.00")
        self.pos_label.setStyleSheet(f"color:{theme.T1};font-family:{theme.MONO};font-size:13px;")
        self.dur_label = QLabel("00:00.00")
        self.dur_label.setStyleSheet(f"color:{theme.T3};font-family:{theme.MONO};font-size:13px;")
        self.seek = QSlider(Qt.Horizontal)
        self.seek.setRange(0, 1000)
        self.seek.sliderReleased.connect(self._on_seek)

        for widget in (play_btn, pause_btn, reset_btn, self.pos_label):
            row.addWidget(widget)
        row.addWidget(self.seek, 1)
        row.addWidget(self.dur_label)
        box.addLayout(row)

        self.tap_btn = QPushButton("TANDAI BARIS BERIKUTNYA   ·   Enter")
        theme.paint(self.tap_btn,
            f"background:#e8e9eb;color:#0b0b0c;font-size:13px;font-weight:700;"
            f"padding:15px;border-radius:2px;"
        )
        self.tap_btn.clicked.connect(self.tap)
        box.addWidget(self.tap_btn)
        return panel

    # ---------- logika ----------

    def _load_song(self, song):
        self.title_input.setText(song.title)
        self.artist_input.setText(song.artist)
        self.duration_input.setText(format_time(song.duration_sec))
        self.raw_text.setPlainText("\n".join(text for _, text in song.lines))
        self._entries = [[time_sec, text] for time_sec, text in song.lines]
        self._apply_duration()

    def _apply_duration(self):
        duration = parse_duration(self.duration_input.text())
        self.clock.load_lyrics([], duration=duration)

    def _update_raw_count(self):
        count = len([l for l in self.raw_text.toPlainText().splitlines() if l.strip()])
        self.raw_count_label.setText(str(count))

    def split_lines(self):
        """
        Pecah teks mentah jadi entri. Timestamp yang sudah ada dipertahankan
        untuk baris yang teksnya tidak berubah, supaya memperbaiki satu typo
        tidak menghapus semua hasil menandai waktu.
        """
        texts = [line.strip() for line in self.raw_text.toPlainText().splitlines() if line.strip()]
        old = {text: time_sec for time_sec, text in self._entries if time_sec is not None}
        self._entries = [[old.get(text), text] for text in texts]
        self._rebuild_entry_list()

    def tap(self):
        """Tandai waktu baris pertama yang belum bertanda."""
        if not self._entries:
            self.split_lines()
        for entry in self._entries:
            if entry[0] is None:
                entry[0] = self.clock.get_raw_position()
                self._rebuild_entry_list()
                return
        # semua sudah bertanda -- diamkan, jangan menimpa diam-diam

    def clear_selected_mark(self):
        row = self.entry_list.currentRow()
        if 0 <= row < len(self._entries):
            self._entries[row][0] = None
            self._rebuild_entry_list()
            self.entry_list.setCurrentRow(row)

    def shift_all(self, delta):
        for entry in self._entries:
            if entry[0] is not None:
                entry[0] = max(0.0, entry[0] + delta)
        self._rebuild_entry_list()

    def _seek_to_entry(self, item):
        row = self.entry_list.row(item)
        if 0 <= row < len(self._entries) and self._entries[row][0] is not None:
            self.clock.seek(self._entries[row][0])

    def _rebuild_entry_list(self):
        current = self.entry_list.currentRow()
        self.entry_list.clear()
        marked = 0
        next_armed = True
        for time_sec, text in self._entries:
            if time_sec is None:
                if next_armed:
                    item = QListWidgetItem(f"  — siap —   {text}")
                    item.setForeground(QColor(theme.STANDBY))
                    next_armed = False
                else:
                    item = QListWidgetItem(f"  ··:··      {text}")
                    item.setForeground(QColor(theme.T3))
            else:
                marked += 1
                item = QListWidgetItem(f"  {format_time(time_sec)}   {text}")
                item.setForeground(QColor(theme.T1))
            self.entry_list.addItem(item)
        if 0 <= current < self.entry_list.count():
            self.entry_list.setCurrentRow(current)

        total = len(self._entries)
        self.result_count_label.setText(f"{marked}/{total}")
        self.progress_label.setText(f"{marked}/{total} baris ditandai")
        self.tap_btn.setEnabled(marked < total or total == 0)
        self.tap_btn.setText(
            "SEMUA BARIS SUDAH DITANDAI" if total and marked >= total
            else "TANDAI BARIS BERIKUTNYA   ·   Enter"
        )

    # ---------- simpan ----------

    def _marked_lines(self):
        return sorted(
            [(time_sec, text) for time_sec, text in self._entries if time_sec is not None],
            key=lambda pair: pair[0],
        )

    def _build_song(self):
        lines = self._marked_lines()
        duration = parse_duration(self.duration_input.text())
        if lines and duration <= lines[-1][0]:
            duration = lines[-1][0] + 5     # durasi tak boleh lebih pendek dari baris terakhir
        title = self.title_input.text().strip() or "(tanpa judul)"
        artist = self.artist_input.text().strip()
        if self.song:
            from dataclasses import replace
            return replace(self.song, title=title, artist=artist,
                           duration_sec=duration, lines=lines)
        return Song(title=title, artist=artist, duration_sec=duration,
                    lines=lines, source="manual")

    def save(self):
        lines = self._marked_lines()
        if not lines:
            QMessageBox.information(
                self, "Belum ada yang ditandai",
                "Belum ada satu pun baris yang punya timestamp.\n\n"
                "Putar lagunya, lalu tekan Enter tiap kali baris berganti."
            )
            return
        unmarked = len(self._entries) - len(lines)
        if unmarked > 0:
            answer = QMessageBox.question(
                self, "Masih ada baris tanpa tanda",
                f"{unmarked} baris belum ditandai waktunya dan tidak akan ikut tersimpan.\n\n"
                "Simpan sekarang?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        song = self.library.upsert(self._build_song())
        self.song = song
        self.songSaved.emit(song)
        self.accept()

    def export_lrc(self):
        from PySide6.QtWidgets import QFileDialog
        lines = self._marked_lines()
        if not lines:
            QMessageBox.information(self, "Kosong", "Belum ada baris bertanda waktu.")
            return
        title = self.title_input.text().strip() or "lirik"
        path, _ = QFileDialog.getSaveFileName(
            self, "Ekspor .lrc", f"{title}.lrc", "File LRC (*.lrc)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(format_lrc(lines, title, self.artist_input.text().strip()))
        except OSError as exc:
            QMessageBox.warning(self, "Gagal menulis file", str(exc))

    # ---------- jam ----------

    def _on_seek(self):
        duration = self.clock.get_duration()
        if duration > 0:
            self.clock.seek(self.seek.value() / 1000.0 * duration)

    def _refresh(self):
        position = self.clock.get_raw_position()
        duration = self.clock.get_duration()
        self.pos_label.setText(format_time(position))
        self.dur_label.setText(format_time(duration))
        if not self.seek.isSliderDown() and duration > 0:
            self.seek.setValue(int(min(1.0, position / duration) * 1000))
