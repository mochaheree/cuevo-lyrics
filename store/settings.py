"""
Pengaturan yang diingat antar sesi -- REQ-F-CFG-01/02.

Skema mengikuti SRS §5.4. Field style TIDAK disimpan di sini; itu urusan
Template (§5.3, Fase 3). Yang di sini hanya hal yang sifatnya per-instalasi:
nama sender, resolusi output, fps, dan lokasi file data.
"""
from dataclasses import dataclass, asdict, field

from store.paths import (
    read_json, write_json_atomic, settings_path,
    default_library_path, default_shows_dir,
)


@dataclass
class Settings:
    spout_sender_name: str = "CUEVO Lyrics"
    output_width: int = 1920
    output_height: int = 1080
    fps: int = 30
    library_path: str = field(default_factory=default_library_path)
    shows_path: str = field(default_factory=default_shows_dir)
    default_template_id: str = None
    global_hotkey_enabled: bool = False     # REQ-F-PLAY-07, default mati
    osc_enabled: bool = False               # REQ-F-RC-01, default mati
    osc_port: int = 8000
    midi_enabled: bool = False              # REQ-F-RC-02, default mati
    midi_port_index: int = 0
    operator_display_open: bool = False     # REQ-F-OPS-01, dibuka lagi saat startup
    cast_open: bool = False                 # REQ-F-OUT-09, jendela siar
    cast_background: str = "#000000"

    # --- diisi saat load, tidak ikut disimpan ---
    load_error: str = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop("load_error", None)
        return data

    def save(self):
        write_json_atomic(settings_path(), self.to_dict())

    @classmethod
    def load(cls) -> "Settings":
        """
        Selalu mengembalikan Settings yang valid. File hilang atau rusak
        tidak boleh menghalangi aplikasi dibuka -- pakai default dan
        sampaikan masalahnya lewat `load_error`.
        """
        data, error = read_json(settings_path(), {})
        if not isinstance(data, dict):
            data, error = {}, "settings.json format not recognised"

        known = {f for f in cls.__dataclass_fields__ if f != "load_error"}
        clean = {}
        for key, value in data.items():
            if key not in known:
                continue
            clean[key] = value

        settings = cls(**clean)
        settings.load_error = error
        settings._clamp()
        return settings

    def _clamp(self):
        """
        Nilai di luar akal (hasil edit manual atau file rusak sebagian)
        dikembalikan ke rentang wajar, bukan diteruskan ke renderer.
        """
        self.output_width = max(160, min(7680, int(self.output_width or 1920)))
        self.output_height = max(90, min(4320, int(self.output_height or 1080)))
        self.fps = max(1, min(120, int(self.fps or 30)))
        self.spout_sender_name = (self.spout_sender_name or "CUEVO Lyrics").strip() or "CUEVO Lyrics"
        self.library_path = self.library_path or default_library_path()
        self.shows_path = self.shows_path or default_shows_dir()
        self.global_hotkey_enabled = bool(self.global_hotkey_enabled)
        self.osc_enabled = bool(self.osc_enabled)
        self.osc_port = max(1024, min(65535, int(self.osc_port or 8000)))
        self.midi_enabled = bool(self.midi_enabled)
        self.midi_port_index = max(0, int(self.midi_port_index or 0))
        self.operator_display_open = bool(self.operator_display_open)
        self.cast_open = bool(self.cast_open)
        self.cast_background = (self.cast_background or "#000000").strip() or "#000000"
