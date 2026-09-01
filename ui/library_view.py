"""
Screen 02 di mockup -- pencarian lirik, dua sumber.

  LRCLIB        : pencarian online, satu kolom query bebas (REQ-F-LIB-01)
  Library lokal : koleksi yang sudah disimpan, tetap jalan offline
                  (REQ-F-LIB-04/06, REQ-NF-03)

Aturan pencariannya sengaja sama untuk kedua sumber: ketik apa saja,
urutan bebas. Operator tidak perlu berganti cara berpikir saat pindah
sumber.

Impor `.lrc` dan editor lirik manual masuk lewat sini juga
(REQ-F-LIB-03/07).
"""
import os
import threading

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox,
)

import lrclib_client
from lrc_parser import parse_lrc
from store.library import Song
from ui import theme
from ui.lyric_editor import LyricEditor
from ui.segmented import SegmentedControl

SOURCE_ONLINE = "lrclib"
SOURCE_LOCAL = "local"


class _SearchBridge(QObject):
    """Hasil dari thread pencarian dipindahkan ke thread GUI lewat signal."""
    done = Signal(list)
    failed = Signal(str)


class LibraryView(QWidget):
    songLoaded = Signal(str, list, float)   # judul, lines, durasi
    libraryChanged = Signal()               # isi library berubah -> Show perlu menyegarkan
    addToShowRequested = Signal(object)     # Song -> ditambahkan ke show yang dibuka

    def __init__(self, library, parent=None):
        super().__init__(parent)
        self.library = library
        self._rows = []                 # dict LRCLIB atau Song, sebaris per baris tabel
        self._source = SOURCE_ONLINE

        self._bridge = _SearchBridge()
        self._bridge.done.connect(self._on_results)
        self._bridge.failed.connect(self._on_failed)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_source_bar())
        root.addWidget(self._build_search_bar())
        root.addWidget(self._build_table(), 1)
        root.addWidget(self._build_action_bar())

        self.status = QLabel("")
        theme.paint(self.status,
            f"color:{theme.STANDBY};padding:7px 12px;font-size:11px;"
            f"border-top:1px solid {theme.SEAM};"
        )
        self.status.hide()
        root.addWidget(self.status)

        if self.library.load_error:
            self._show_status(f"{self.library.load_error} — mulai dari library kosong.")
        # notify=False: saat konstruktor, ShowView belum tersambung
        self.refresh_local_count(notify=False)

    # ---------- bar sumber ----------

    def _build_source_bar(self):
        bar = QWidget()
        theme.paint(bar,f"background:{theme.V2};border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(bar)
        box.setContentsMargins(12, 8, 12, 8)
        box.setSpacing(14)

        self.source_seg = SegmentedControl(["LRCLIB", "Library lokal"])
        self.online_radio = self.source_seg.button(0)
        self.local_radio = self.source_seg.button(1)
        self.online_radio.setChecked(True)
        self.online_radio.toggled.connect(self._on_source_changed)
        box.addWidget(self.source_seg)

        self.local_count = QLabel("0")
        self.local_count.setStyleSheet(f"color:{theme.T4};font-family:{theme.MONO};font-size:11px;")
        box.addWidget(self.local_count)
        box.addStretch(1)

        import_btn = QPushButton("Import .lrc")
        import_btn.setProperty("variant", "quiet")
        import_btn.clicked.connect(self.import_lrc)
        manual_btn = QPushButton("Lagu manual")
        manual_btn.setProperty("variant", "quiet")
        manual_btn.clicked.connect(self.new_manual_song)
        box.addWidget(import_btn)
        box.addWidget(manual_btn)
        return bar

    def _on_source_changed(self, online):
        self._source = SOURCE_ONLINE if online else SOURCE_LOCAL
        self.query.setPlaceholderText(
            "judul, artis, atau keduanya — urutan bebas" if online
            else "saring library lokal — kosongkan untuk melihat semua"
        )
        self.search_btn.setVisible(online)
        self.status.hide()
        if online:
            self.table.setRowCount(0)
            self._rows = []
        else:
            self._show_local()
        self._update_action_state()

    # ---------- pencarian ----------

    def _build_search_bar(self):
        bar = QWidget()
        theme.paint(bar,f"background:{theme.V2};border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(bar)
        box.setContentsMargins(12, 10, 12, 10)
        box.setSpacing(7)

        self.query = QLineEdit()
        self.query.setProperty("role", "search")
        self.query.setPlaceholderText("judul, artis, atau keduanya — urutan bebas")
        self.query.returnPressed.connect(self.search)
        self.query.textChanged.connect(self._on_query_changed)
        box.addWidget(self.query, 1)

        self.search_btn = QPushButton("Cari")
        self.search_btn.setMinimumWidth(72)
        self.search_btn.clicked.connect(self.search)
        box.addWidget(self.search_btn)
        return bar

    def _on_query_changed(self, text):
        # library lokal disaring langsung sambil mengetik; LRCLIB menunggu Enter
        # supaya tidak membanjiri layanan gratis mereka (REQ-NF-09)
        if self._source == SOURCE_LOCAL:
            self._show_local()

    def _build_table(self):
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Judul", "Artis", "Album", "Durasi", "Lirik"])
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.doubleClicked.connect(self.load_selected)
        self.table.itemSelectionChanged.connect(self._update_action_state)

        header = self.table.horizontalHeader()
        for column in (0, 1, 2):
            header.setSectionResizeMode(column, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 100)
        return self.table

    def _build_action_bar(self):
        bar = QWidget()
        theme.paint(bar,f"background:{theme.V2};border-top:1px solid {theme.SEAM};")
        box = QHBoxLayout(bar)
        box.setContentsMargins(12, 8, 12, 8)
        box.setSpacing(7)

        self.load_btn = QPushButton("Muat ke player")
        self.load_btn.clicked.connect(self.load_selected)
        self.save_btn = QPushButton("Simpan ke library")
        self.save_btn.setProperty("variant", "quiet")
        self.save_btn.clicked.connect(self.save_selected)
        self.edit_btn = QPushButton("Edit lirik")
        self.edit_btn.setProperty("variant", "quiet")
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn = QPushButton("Hapus")
        self.delete_btn.setProperty("variant", "quiet")
        self.delete_btn.clicked.connect(self.delete_selected)

        for btn in (self.load_btn, self.save_btn, self.edit_btn, self.delete_btn):
            box.addWidget(btn)

        self.show_btn = QPushButton("Tambah ke show")
        self.show_btn.setProperty("variant", "quiet")
        self.show_btn.clicked.connect(self.add_to_show)
        box.addWidget(self.show_btn)
        box.addStretch(1)
        return bar

    def _update_action_state(self):
        item = self.current_item()
        local = self._source == SOURCE_LOCAL
        self.load_btn.setEnabled(item is not None)
        self.edit_btn.setEnabled(item is not None)
        self.show_btn.setEnabled(item is not None)
        self.delete_btn.setEnabled(item is not None and local)
        self.save_btn.setEnabled(item is not None and not local)

    # ---------- LRCLIB ----------

    def search(self):
        if self._source == SOURCE_LOCAL:
            self._show_local()
            return

        query = self.query.text().strip()
        if not query:
            self._show_status("Ketik dulu sesuatu untuk dicari.")
            return

        self.search_btn.setEnabled(False)
        self.search_btn.setText("Mencari…")
        self.status.hide()

        def worker():
            try:
                results = lrclib_client.search(query=query)
            except Exception as exc:
                self._bridge.failed.emit(str(exc))
                return
            self._bridge.done.emit(results)

        threading.Thread(target=worker, daemon=True).start()

    def _reset_search_button(self):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Cari")

    def _on_results(self, results):
        self._reset_search_button()
        self._rows = results
        self._fill_table([self._online_cells(item) for item in results])
        if not results:
            self._show_status("Tidak ada hasil. Coba kata kunci lain.")

    def _on_failed(self, message):
        self._reset_search_button()
        # REQ-NF-03: gagal jaringan tidak boleh mematikan aplikasi
        self._show_status(
            f"LRCLIB tidak terjangkau ({message}). "
            f"Library lokal tetap bisa dipakai — pindah ke sumber “Library lokal”."
        )

    def _online_cells(self, item):
        duration = int(item.get("duration") or 0)
        if item.get("syncedLyrics"):
            lyric, color = "● synced", theme.OK
        elif item.get("plainLyrics"):
            lyric, color = "○ plain", theme.T3
        else:
            lyric, color = "— kosong", theme.T4
        saved = self.library.find_by_lrclib_id(item.get("id")) is not None
        return [
            (item.get("trackName") or "?", theme.T1),
            (item.get("artistName") or "?", theme.T2),
            (item.get("albumName") or "—", theme.T2),
            (f"{duration // 60}:{duration % 60:02d}", theme.T3),
            (lyric + ("  ✓" if saved else ""), color),
        ]

    # ---------- library lokal ----------

    def _show_local(self):
        songs = self.library.search(self.query.text().strip())
        self._rows = songs
        self._fill_table([self._local_cells(song) for song in songs])
        if not songs:
            self._show_status(
                "Library masih kosong." if len(self.library) == 0
                else "Tidak ada yang cocok di library lokal."
            )
        else:
            self.status.hide()

    def _local_cells(self, song):
        duration = int(song.duration_sec)
        return [
            (song.title, theme.T1),
            (song.artist or "—", theme.T2),
            (song.album or "—", theme.T2),
            (f"{duration // 60}:{duration % 60:02d}", theme.T3),
            (f"{len(song.lines)} baris", theme.OK if song.lines else theme.T4),
        ]

    def refresh_local_count(self, notify=True):
        self.local_count.setText(str(len(self.library)))
        if self._source == SOURCE_LOCAL:
            self._show_local()
        if notify:
            self.libraryChanged.emit()

    # ---------- tabel ----------

    def _fill_table(self, rows):
        self.table.setRowCount(len(rows))
        for row, cells in enumerate(rows):
            for column, (text, color) in enumerate(cells):
                cell = QTableWidgetItem(text)
                cell.setForeground(QColor(color))
                cell.setToolTip(text)
                if column == 3:
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, column, cell)
        if rows:
            self.table.selectRow(0)
        self._update_action_state()

    def current_item(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def _show_status(self, message):
        self.status.setText(message)
        self.status.show()

    # ---------- aksi ----------

    def _as_song(self, item):
        """Ubah baris terpilih jadi Song, dari sumber mana pun."""
        if isinstance(item, Song):
            return item
        synced = item.get("syncedLyrics")
        lines = parse_lrc(synced) if synced else []
        duration = float(item.get("duration") or (lines[-1][0] + 5 if lines else 0))
        return Song(
            title=item.get("trackName") or "(tanpa judul)",
            artist=item.get("artistName") or "",
            album=item.get("albumName") or "",
            duration_sec=duration,
            source="lrclib",
            lrclib_id=item.get("id"),
            lines=lines,
        )

    def load_selected(self):
        item = self.current_item()
        if item is None:
            self._show_status("Pilih salah satu baris dulu.")
            return
        song = self._as_song(item)
        if not song.lines:
            self._show_status(
                "Lagu ini belum punya lirik bersinkron waktu. "
                "Pakai “Edit lirik” untuk menandai waktunya sendiri."
            )
            return
        self.status.hide()
        self.songLoaded.emit(song.label, song.lines, song.duration_sec)

    def save_selected(self):
        item = self.current_item()
        if item is None:
            return
        incoming = self._as_song(item)

        # Menyimpan ulang lagu LRCLIB yang sama akan menimpa entri lama.
        # Kalau timestamp-nya sudah pernah diedit manual, hasil kerja itu
        # hilang tanpa jejak -- jadi tanya dulu.
        existing = self.library.find_by_lrclib_id(incoming.lrclib_id)
        if existing is not None and existing.lines != incoming.lines:
            answer = QMessageBox.question(
                self, "Sudah ada di library",
                f"“{existing.label}” sudah ada di library dengan {len(existing.lines)} baris.\n\n"
                f"Menyimpan lagi akan menggantinya dengan versi LRCLIB "
                f"({len(incoming.lines)} baris). Koreksi timestamp yang pernah kamu buat "
                f"akan hilang.\n\nTimpa?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        song = self.library.upsert(incoming)
        self.refresh_local_count()
        if self._source == SOURCE_ONLINE:
            self._on_results(self._rows)   # gambar ulang supaya tanda ✓ muncul
        self._show_status(f"“{song.title}” tersimpan ke library.")

    def add_to_show(self):
        """
        REQ-F-SET-01/02 dari sisi Library.

        Show menyimpan id lagu, bukan salinan liriknya. Jadi hasil pencarian
        LRCLIB harus masuk library dulu -- kalau tidak, id-nya hanya hidup di
        memori dan show yang disimpan akan menunjuk lagu yang tidak ada saat
        dibuka lagi besok.
        """
        item = self.current_item()
        if item is None:
            self._show_status("Pilih salah satu baris dulu.")
            return
        song = self._as_song(item)
        if not isinstance(item, Song):
            song = self.library.upsert(song)
            self.refresh_local_count()
        self.addToShowRequested.emit(song)

    def edit_selected(self):
        item = self.current_item()
        if item is None:
            return
        song = self._as_song(item)
        if not isinstance(item, Song):
            song = self.library.upsert(song)   # harus ada di library dulu supaya bisa diedit
        self._open_editor(song)

    def delete_selected(self):
        song = self.current_item()
        if not isinstance(song, Song):
            return
        answer = QMessageBox.question(
            self, "Hapus dari library",
            f"Hapus “{song.label}” dari library?\n\nTindakan ini tidak bisa dibatalkan.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.library.delete(song.id)
        self.refresh_local_count()

    def new_manual_song(self):
        self._open_editor(None)

    def _open_editor(self, song):
        editor = LyricEditor(self.library, song, parent=self)
        editor.songSaved.connect(self._on_song_saved)
        editor.exec()

    def _on_song_saved(self, song):
        self.refresh_local_count()
        self.local_radio.setChecked(True)
        self._show_status(f"“{song.title}” tersimpan — {len(song.lines)} baris bertanda waktu.")

    # ---------- impor .lrc (REQ-F-LIB-03/07) ----------

    def import_lrc(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Impor file .lrc", "", "File LRC (*.lrc *.txt);;Semua file (*)"
        )
        if not paths:
            return

        imported, skipped = 0, []
        for path in paths:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    lines = parse_lrc(handle.read())
            except OSError as exc:
                skipped.append(f"{os.path.basename(path)} ({exc})")
                continue
            if not lines:
                skipped.append(f"{os.path.basename(path)} (tidak ada baris bertimestamp)")
                continue

            title = os.path.splitext(os.path.basename(path))[0]
            artist = ""
            if " - " in title:      # konvensi umum nama file: "Artis - Judul.lrc"
                artist, _, title = title.partition(" - ")
            self.library.upsert(Song(
                title=title.strip() or "(tanpa judul)",
                artist=artist.strip(),
                duration_sec=lines[-1][0] + 5,
                source="lrc-import",
                lines=lines,
            ))
            imported += 1

        self.refresh_local_count()
        self.local_radio.setChecked(True)
        message = f"{imported} file diimpor ke library."
        if skipped:
            message += f" {len(skipped)} dilewati: " + "; ".join(skipped[:3])
            if len(skipped) > 3:
                message += f" (+{len(skipped) - 3} lagi)"
        self._show_status(message)
