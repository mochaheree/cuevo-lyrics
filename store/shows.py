"""
Show / Set list -- REQ-F-SET-01/04. Skema mengikuti SRS §5.2.

Satu Show = satu file `<id>.showproject.json` di dalam folder shows. Dipisah
per file (bukan satu file besar berisi semua show) supaya satu show yang
rusak tidak menjatuhkan yang lain, dan supaya file-nya gampang disalin atau
dikirim ke operator lain.

Show hanya menyimpan **daftar id lagu**, bukan salinan liriknya. Jadi
memperbaiki timestamp sebuah lagu langsung berlaku di semua show yang
memakainya.

Tanpa import PySide6 / SpoutGL (REQ-NF-06).
"""
import os
import re
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from store.paths import read_json, write_json_atomic, default_shows_dir

SCHEMA_VERSION = 1
SUFFIX = ".showproject.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Show:
    name: str = "Show baru"
    song_ids: list = field(default_factory=list)
    template_id: str = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "version": SCHEMA_VERSION,
            "id": self.id,
            "name": self.name,
            "song_ids": list(self.song_ids),
            "template_id": self.template_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Show":
        song_ids = [str(x) for x in (data.get("song_ids") or []) if x]
        return cls(
            id=data.get("id") or str(uuid.uuid4()),
            name=data.get("name") or "Show tanpa nama",
            song_ids=song_ids,
            template_id=data.get("template_id"),
            created_at=data.get("created_at") or _now_iso(),
            updated_at=data.get("updated_at") or _now_iso(),
        )


class ShowStore:
    def __init__(self, directory: str = None):
        self.directory = directory or default_shows_dir()
        self.load_errors = []

    def use_directory(self, directory: str):
        self.directory = directory

    def _path_for(self, show_id: str) -> str:
        # id berasal dari uuid4, tapi jangan pernah percaya begitu saja pada
        # sesuatu yang dipakai membentuk path -- file bisa saja diedit tangan
        safe = re.sub(r"[^A-Za-z0-9_-]", "", show_id) or "show"
        return os.path.join(self.directory, safe + SUFFIX)

    def list_shows(self):
        """Semua show yang terbaca, terurut dari yang terakhir diubah."""
        self.load_errors = []
        shows = []
        if not os.path.isdir(self.directory):
            return shows
        for name in sorted(os.listdir(self.directory)):
            if not name.endswith(SUFFIX):
                continue
            data, error = read_json(os.path.join(self.directory, name), None)
            if error:
                self.load_errors.append(error)
                continue
            if not isinstance(data, dict):
                self.load_errors.append(f"{name} formatnya tidak dikenali")
                continue
            shows.append(Show.from_dict(data))
        shows.sort(key=lambda s: s.updated_at, reverse=True)
        return shows

    def load(self, show_id: str):
        data, error = read_json(self._path_for(show_id), None)
        if error or not isinstance(data, dict):
            return None
        return Show.from_dict(data)

    def save(self, show: Show) -> Show:
        show = replace(show, updated_at=_now_iso())
        write_json_atomic(self._path_for(show.id), show.to_dict())
        return show

    def delete(self, show_id: str) -> bool:
        try:
            os.remove(self._path_for(show_id))
            return True
        except OSError:
            return False
