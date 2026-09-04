"""
Library lagu lokal -- REQ-F-LIB-04.

Skema `Song` mengikuti SRS §5.1. Di dalam aplikasi, baris lirik dipakai
sebagai list of tuple `(time_sec, text)` (bentuk yang sudah dipakai
`lrc_parser` dan `PlayerState`); di file JSON disimpan sebagai list of
object supaya enak dibaca manusia dan aman ditambah field baru nanti.

Tanpa import PySide6 / SpoutGL (REQ-NF-06).
"""
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from store.paths import read_json, write_json_atomic, default_library_path

SCHEMA_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Song:
    title: str
    artist: str = ""
    album: str = ""
    duration_sec: float = 0.0
    source: str = "manual"            # "lrclib" | "manual" | "lrc-import"
    lrclib_id: int = None
    lines: list = field(default_factory=list)   # [(time_sec, text), ...]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def label(self) -> str:
        return f"{self.title} - {self.artist}" if self.artist else self.title

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration_sec": self.duration_sec,
            "source": self.source,
            "lrclib_id": self.lrclib_id,
            "lines": [{"time_sec": round(t, 3), "text": text} for t, text in self.lines],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Song":
        lines = []
        for item in data.get("lines") or []:
            try:
                lines.append((float(item["time_sec"]), str(item.get("text", ""))))
            except (KeyError, TypeError, ValueError):
                continue          # baris rusak dilewati, sisanya tetap terpakai
        lines.sort(key=lambda pair: pair[0])
        return cls(
            id=data.get("id") or str(uuid.uuid4()),
            title=data.get("title") or "(untitled)",
            artist=data.get("artist") or "",
            album=data.get("album") or "",
            duration_sec=float(data.get("duration_sec") or 0.0),
            source=data.get("source") or "manual",
            lrclib_id=data.get("lrclib_id"),
            lines=lines,
            created_at=data.get("created_at") or _now_iso(),
            updated_at=data.get("updated_at") or _now_iso(),
        )

    def shifted(self, delta_sec: float) -> "Song":
        """
        Semua timestamp digeser -- REQ-F-LIB-05, untuk kasus versi rekaman
        yang intronya beda panjang. Tidak boleh jadi negatif.
        """
        return replace(
            self,
            lines=[(max(0.0, t + delta_sec), text) for t, text in self.lines],
            updated_at=_now_iso(),
        )


class Library:
    """
    Koleksi lagu yang tersimpan di satu file JSON.

    Setiap operasi tulis langsung menyimpan ke disk (auto-save). Untuk
    ukuran koleksi yang realistis di sini -- ratusan lagu, bukan puluhan
    ribu -- itu jauh lebih murah daripada risiko kehilangan data karena
    lupa menekan Simpan sebelum acara mulai.
    """

    def __init__(self, path: str = None):
        self.path = path or default_library_path()
        self._songs = {}
        self.load_error = None
        self.load()

    # ---------- I/O ----------

    def load(self):
        data, error = read_json(self.path, {"version": SCHEMA_VERSION, "songs": []})
        self.load_error = error
        self._songs = {}
        for item in (data.get("songs") if isinstance(data, dict) else []) or []:
            try:
                song = Song.from_dict(item)
            except Exception:
                continue
            self._songs[song.id] = song

    def save(self):
        write_json_atomic(self.path, {
            "version": SCHEMA_VERSION,
            "songs": [song.to_dict() for song in self._songs.values()],
        })

    def use_path(self, path: str):
        """Pindah ke file library lain (REQ-F-CFG-02) dan muat isinya."""
        self.path = path
        self.load()

    # ---------- baca ----------

    def __len__(self):
        return len(self._songs)

    def get(self, song_id: str):
        return self._songs.get(song_id)

    def list_songs(self):
        """Terurut berdasarkan yang terakhir diubah -- yang baru dipakai di atas."""
        return sorted(self._songs.values(), key=lambda s: s.updated_at, reverse=True)

    def search(self, query: str):
        """
        Pencarian lokal (REQ-F-LIB-06). Mengikuti aturan yang sama dengan
        pencarian LRCLIB: satu query bebas, semua kata harus muncul di
        judul/artis/album, urutan bebas.
        """
        terms = [word for word in query.lower().split() if word]
        if not terms:
            return self.list_songs()
        results = []
        for song in self.list_songs():
            haystack = f"{song.title} {song.artist} {song.album}".lower()
            if all(term in haystack for term in terms):
                results.append(song)
        return results

    def find_by_lrclib_id(self, lrclib_id):
        if lrclib_id is None:
            return None
        for song in self._songs.values():
            if song.lrclib_id == lrclib_id:
                return song
        return None

    # ---------- tulis ----------

    def upsert(self, song: Song) -> Song:
        """
        Simpan lagu. Kalau lagu dari LRCLIB dengan id yang sama sudah ada,
        yang lama diperbarui -- bukan diduplikasi. Tanpa ini, menekan
        "Simpan ke library" dua kali menghasilkan dua entri identik.
        """
        existing = self._songs.get(song.id) or self.find_by_lrclib_id(song.lrclib_id)
        if existing is not None:
            song = replace(song, id=existing.id, created_at=existing.created_at,
                           updated_at=_now_iso())
        else:
            song = replace(song, updated_at=_now_iso())
        self._songs[song.id] = song
        self.save()
        return song

    def delete(self, song_id: str) -> bool:
        if song_id in self._songs:
            del self._songs[song_id]
            self.save()
            return True
        return False
