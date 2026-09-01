"""
Show yang sedang dipakai dalam satu sesi tampil.

Menjembatani `Show` (daftar id lagu di disk) dengan `Library` (isi lagunya),
dan melacak lagu ke berapa yang sedang tayang -- REQ-F-SET-03/05.

Sengaja terpisah dari `store/shows.py`: yang itu urusan file, yang ini
keadaan saat berjalan. Tidak menyentuh disk sama sekali.

Tanpa import PySide6 / SpoutGL (REQ-NF-06).
"""
from store.shows import Show


class ShowSession:
    def __init__(self, library, show: Show = None):
        self.library = library
        self.show = Show()
        self.index = -1
        self.dirty = False
        self.dropped = []          # id yang dibuang karena lagunya sudah tidak ada
        self.load(show or Show())

    # ---------- muat / ganti ----------

    def load(self, show: Show):
        """
        Muat show, sambil membuang id yang lagunya sudah tidak ada di library.

        Pembuangan dilakukan SEKALI di sini, bukan disaring tiap kali daftar
        dibaca. Kalau disaring belakangan, `index` akan menunjuk ke posisi di
        daftar hasil saring sementara operasi tambah/hapus/urutkan menunjuk ke
        `song_ids` mentah -- dua ruang indeks berbeda yang diam-diam meleset
        begitu ada satu lagu terhapus.
        """
        self.show = show
        self.dropped = [sid for sid in show.song_ids if self.library.get(sid) is None]
        if self.dropped:
            show.song_ids = [sid for sid in show.song_ids if sid not in self.dropped]
            self.dirty = True      # perubahan ini perlu disimpan agar permanen
        else:
            self.dirty = False
        self.index = 0 if show.song_ids else -1

    def mark_saved(self, show: Show):
        self.show = show
        self.dirty = False

    # ---------- baca ----------

    def songs(self):
        """Lagu-lagu show ini, terurut. Sejajar 1:1 dengan `show.song_ids`."""
        return [self.library.get(sid) for sid in self.show.song_ids
                if self.library.get(sid) is not None]

    def __len__(self):
        return len(self.songs())

    def current(self):
        songs = self.songs()
        if 0 <= self.index < len(songs):
            return songs[self.index]
        return None

    def peek(self, offset: int):
        songs = self.songs()
        target = self.index + offset
        if 0 <= target < len(songs):
            return songs[target]
        return None

    def position_label(self) -> str:
        total = len(self.songs())
        if total == 0:
            return "0/0"
        return f"{min(self.index + 1, total)}/{total}"

    # ---------- navigasi (REQ-F-SET-03) ----------

    def goto(self, index: int):
        songs = self.songs()
        if not songs:
            self.index = -1
            return None
        self.index = max(0, min(len(songs) - 1, index))
        return songs[self.index]

    def step(self, delta: int):
        return self.goto(self.index + delta)

    def has_next(self) -> bool:
        return self.index + 1 < len(self.songs())

    def has_prev(self) -> bool:
        return self.index > 0

    # ---------- ubah isi (REQ-F-SET-02) ----------

    def add_song(self, song_id: str):
        self.show.song_ids.append(song_id)
        if self.index < 0:
            self.index = 0
        self.dirty = True

    def remove_at(self, position: int):
        if not (0 <= position < len(self.show.song_ids)):
            return
        del self.show.song_ids[position]
        self.dirty = True
        if self.index >= len(self.show.song_ids):
            self.index = len(self.show.song_ids) - 1

    def reorder(self, song_ids):
        """
        Urutan baru dari drag di GUI. Lagu yang sedang tayang tetap yang itu
        walau posisinya bergeser -- operator memindahkan lagu lain, bukan
        mengganti yang sedang jalan.
        """
        current_id = None
        if 0 <= self.index < len(self.show.song_ids):
            current_id = self.show.song_ids[self.index]
        self.show.song_ids = list(song_ids)
        self.dirty = True
        if current_id in self.show.song_ids:
            self.index = self.show.song_ids.index(current_id)

    def set_name(self, name: str):
        if name != self.show.name:
            self.show.name = name
            self.dirty = True
