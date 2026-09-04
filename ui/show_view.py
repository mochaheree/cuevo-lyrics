"""
Tab Show -- menyusun set list sebelum acara (REQ-F-SET-01/02/04).

Dua kolom: show yang tersimpan di kiri, isi show yang sedang dibuka di
kanan. Urutan lagu diubah dengan drag; perubahan ditandai "belum disimpan"
supaya tidak ada yang hilang tanpa sadar.

Navigasi saat live TIDAK dilakukan dari sini -- itu ada di tab Live, di
panel set list, supaya operator tidak perlu berpindah tab saat acara jalan.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QAbstractItemView,
)

from store.shows import Show
from ui import theme


class ShowView(QWidget):
    showChanged = Signal()       # isi/urutan berubah -> tab Live perlu menyegarkan

    def __init__(self, session, store, library, parent=None):
        super().__init__(parent)
        self.session = session
        self.store = store
        self.library = library

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_saved_column())
        root.addWidget(self._seam())
        root.addWidget(self._build_editor_column(), 1)

        self.refresh_saved()
        self.refresh_songs()

    def _seam(self):
        line = QWidget()
        line.setFixedWidth(1)
        theme.paint(line,f"background:{theme.SEAM};")
        return line

    def _head(self, title, right=""):
        head = QWidget()
        theme.paint(head,f"background:{theme.V3};border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(head)
        box.setContentsMargins(12, 6, 12, 6)
        left = QLabel(title)
        theme.paint(left,f"color:{theme.T3};font-size:11px;background:transparent;")
        right_label = QLabel(right)
        theme.paint(right_label,
            f"color:{theme.T2};font-family:{theme.MONO};font-size:11px;background:transparent;")
        box.addWidget(left)
        box.addStretch(1)
        box.addWidget(right_label)
        return head, right_label

    def _foot(self, *widgets):
        foot = QWidget()
        theme.paint(foot,f"background:{theme.V3};border-top:1px solid {theme.SEAM};")
        box = QHBoxLayout(foot)
        box.setContentsMargins(12, 7, 12, 7)
        box.setSpacing(6)
        for widget in widgets:
            box.addWidget(widget)
        box.addStretch(1)
        return foot

    # ---------- kiri: show tersimpan ----------

    def _build_saved_column(self):
        col = QWidget()
        col.setFixedWidth(250)
        box = QVBoxLayout(col)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        head, self.saved_count = self._head("Saved shows")
        box.addWidget(head)

        self.saved_list = QListWidget()
        self.saved_list.itemDoubleClicked.connect(self.open_selected)
        box.addWidget(self.saved_list, 1)

        new_btn = QPushButton("New show")
        new_btn.setProperty("variant", "quiet")
        new_btn.clicked.connect(self.new_show)
        open_btn = QPushButton("Open")
        open_btn.setProperty("variant", "quiet")
        open_btn.clicked.connect(self.open_selected)
        del_btn = QPushButton("Delete")
        del_btn.setProperty("variant", "quiet")
        del_btn.clicked.connect(self.delete_selected)
        box.addWidget(self._foot(new_btn, open_btn, del_btn))
        return col

    def refresh_saved(self):
        self.saved_list.clear()
        shows = self.store.list_shows()
        for show in shows:
            item = QListWidgetItem(f"  {show.name}    {len(show.song_ids)} songs")
            item.setData(Qt.UserRole, show.id)
            if show.id == self.session.show.id:
                item.setForeground(QColor(theme.T1))
            else:
                item.setForeground(QColor(theme.T2))
            self.saved_list.addItem(item)
        self.saved_count.setText(str(len(shows)))
        if self.store.load_errors:
            self.status.setText("⚠ " + "; ".join(self.store.load_errors[:2]))

    # ---------- kanan: isi show ----------

    def _build_editor_column(self):
        col = QWidget()
        box = QVBoxLayout(col)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        head, self.dirty_label = self._head("Open show")
        box.addWidget(head)

        name_bar = QWidget()
        theme.paint(name_bar,f"background:{theme.V2};border-bottom:1px solid {theme.SEAM};")
        nb = QHBoxLayout(name_bar)
        nb.setContentsMargins(12, 9, 12, 9)
        nb.setSpacing(7)
        label = QLabel("Name")
        label.setStyleSheet(f"color:{theme.T3};font-size:11px;")
        self.name_input = QLineEdit()
        self.name_input.textEdited.connect(self._on_name_edited)
        save_btn = QPushButton("Save show")
        save_btn.clicked.connect(self.save_show)
        nb.addWidget(label)
        nb.addWidget(self.name_input, 1)
        nb.addWidget(save_btn)
        box.addWidget(name_bar)

        self.song_list = QListWidget()
        self.song_list.setDragDropMode(QAbstractItemView.InternalMove)   # REQ-F-SET-02
        self.song_list.setUniformItemSizes(True)
        self.song_list.model().rowsMoved.connect(self._on_rows_moved)
        box.addWidget(self.song_list, 1)

        add_btn = QPushButton("Add from library")
        add_btn.clicked.connect(self.add_from_library)
        remove_btn = QPushButton("Remove")
        remove_btn.setProperty("variant", "quiet")
        remove_btn.clicked.connect(self.remove_selected)
        box.addWidget(self._foot(add_btn, remove_btn))

        self.status = QLabel("")
        theme.paint(self.status,
            f"color:{theme.STANDBY};padding:7px 12px;font-size:11px;"
            f"border-top:1px solid {theme.SEAM};")
        box.addWidget(self.status)
        return col

    def refresh_songs(self):
        self.name_input.blockSignals(True)
        self.name_input.setText(self.session.show.name)
        self.name_input.blockSignals(False)

        self.song_list.blockSignals(True)
        self.song_list.clear()
        for position, song in enumerate(self.session.songs()):
            duration = int(song.duration_sec)
            item = QListWidgetItem(
                f"  {position + 1:>2}   {song.label}"
                f"      {duration // 60}:{duration % 60:02d}   {len(song.lines)} lines"
            )
            item.setData(Qt.UserRole, song.id)
            item.setForeground(QColor(theme.T1 if position == self.session.index else theme.T2))
            self.song_list.addItem(item)
        self.song_list.blockSignals(False)

        self._update_dirty()
        if self.session.dropped:
            self.status.setText(
                f"⚠ {len(self.session.dropped)} song(s) removed automatically because "
                f"they are no longer in the library. Save the show to make it permanent."
            )
        elif not self.session.show.song_ids:
            self.status.setText("This show is empty. Press “Add from library” to start.")
        else:
            self.status.setText("")

    def _update_dirty(self):
        self.dirty_label.setText("unsaved" if self.session.dirty else "saved")

    # ---------- aksi ----------

    def _on_name_edited(self, text):
        self.session.set_name(text.strip() or "Untitled show")
        self._update_dirty()

    def _on_rows_moved(self, *args):
        order = [self.song_list.item(i).data(Qt.UserRole)
                 for i in range(self.song_list.count())]
        self.session.reorder(order)
        self.refresh_songs()
        self.showChanged.emit()

    def add_from_library(self):
        songs = self.library.list_songs()
        if not songs:
            QMessageBox.information(
                self, "Library is empty",
                "There are no songs in the library yet.\n\nSearch in the Library tab, then press "
                "“Save to library”, or create a manual song."
            )
            return
        labels = [f"{song.label}  ({len(song.lines)} lines)" for song in songs]
        choice, ok = QInputDialog.getItem(
            self, "Add a song to the show", "Choose a song:", labels, 0, False
        )
        if not ok:
            return
        self.session.add_song(songs[labels.index(choice)].id)
        self.refresh_songs()
        self.showChanged.emit()

    def remove_selected(self):
        row = self.song_list.currentRow()
        if row < 0:
            return
        self.session.remove_at(row)
        self.refresh_songs()
        self.showChanged.emit()

    def save_show(self):
        saved = self.store.save(self.session.show)
        self.session.mark_saved(saved)
        self.refresh_saved()
        self._update_dirty()
        self.status.setText(f"“{saved.name}” saved.")

    def new_show(self):
        if not self._confirm_discard():
            return
        self.session.load(Show())
        self.refresh_songs()
        self.refresh_saved()
        self.showChanged.emit()

    def open_selected(self):
        item = self.saved_list.currentItem()
        if item is None:
            return
        if not self._confirm_discard():
            return
        show = self.store.load(item.data(Qt.UserRole))
        if show is None:
            self.status.setText("That show file could not be read.")
            return
        self.session.load(show)
        self.refresh_songs()
        self.refresh_saved()
        self.showChanged.emit()

    def delete_selected(self):
        item = self.saved_list.currentItem()
        if item is None:
            return
        show_id = item.data(Qt.UserRole)
        if QMessageBox.question(
            self, "Delete show", f"Delete “{item.text().strip()}”?\n\nIts songs stay in the library.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self.store.delete(show_id)
        self.refresh_saved()

    def _confirm_discard(self) -> bool:
        if not self.session.dirty:
            return True
        answer = QMessageBox.question(
            self, "Unsaved changes",
            f"“{self.session.show.name}” has unsaved changes.\n\nDiscard them?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        return answer == QMessageBox.Yes
