"""
Template style -- REQ-F-STYLE-02/03. Skema mengikuti SRS §5.3.

Satu Template = satu nama + satu `RenderStyle`. Disimpan dalam satu file
`templates.json` (berbeda dari Show yang satu file per item): template
jumlahnya sedikit, kecil, dan hampir selalu dibaca sekaligus untuk mengisi
dropdown.

Preset bawaan (REQ-F-STYLE-03) TIDAK ikut disimpan ke disk. Preset selalu
dibangkitkan dari kode supaya tetap ada walau file terhapus, dan supaya
perbaikan preset di versi berikutnya ikut terpakai. Kalau user mengubah
sebuah preset, hasilnya disimpan sebagai template baru miliknya.

Tanpa import PySide6 / SpoutGL (REQ-NF-06).
"""
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from render_style import RenderStyle, DEFAULT_STYLE
from store.paths import read_json, write_json_atomic, app_data_dir
import os

SCHEMA_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Template:
    name: str = "Template baru"
    style: RenderStyle = field(default_factory=lambda: DEFAULT_STYLE)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    builtin: bool = False
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        data = self.style.to_dict()
        # resolusi milik Settings, bukan Template -- kalau ikut disimpan,
        # memakai template dari mesin lain akan diam-diam mengubah resolusi output
        data.pop("width", None)
        data.pop("height", None)
        return {"id": self.id, "name": self.name,
                "updated_at": self.updated_at, "style": data}

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        style_data = data.get("style") or {}
        return cls(
            id=data.get("id") or str(uuid.uuid4()),
            name=data.get("name") or "Template tanpa nama",
            style=RenderStyle.from_dict(style_data),
            updated_at=data.get("updated_at") or _now_iso(),
        )


def _presets():
    """Preset bawaan (REQ-F-STYLE-03) — titik awal, bukan kurungan."""
    base = DEFAULT_STYLE
    return [
        Template(id="preset-white-outline", name="Putih Outline Tebal", builtin=True,
                 style=replace(base, active_font_size=64, outline_width=4,
                               text_color=(255, 255, 255, 255),
                               outline_color=(0, 0, 0, 255))),
        Template(id="preset-minimal", name="Minimal Tanpa Outline", builtin=True,
                 style=replace(base, active_font_size=58, outline_width=0,
                               size_falloff=0.18, opacity_falloff=0.40)),
        Template(id="preset-lower-third", name="Lower Third Satu Baris", builtin=True,
                 style=replace(base, layout="single_line", active_font_size=54,
                               outline_width=3, vertical_anchor_ratio=0.80,
                               context_before=0, context_after=0)),
        Template(id="preset-karaoke", name="Karaoke Padat", builtin=True,
                 style=replace(base, active_font_size=52, line_spacing_ratio=1.30,
                               context_before=3, context_after=3,
                               size_falloff=0.14, opacity_falloff=0.24)),
        Template(id="preset-amber", name="Amber Panggung", builtin=True,
                 style=replace(base, active_font_size=66, outline_width=4,
                               text_color=(255, 214, 140, 255),
                               outline_color=(20, 8, 0, 255))),
    ]


class TemplateStore:
    def __init__(self, path: str = None):
        self.path = path or os.path.join(app_data_dir(), "templates.json")
        self._user = {}
        self.load_error = None
        self.load()

    def load(self):
        data, error = read_json(self.path, {"version": SCHEMA_VERSION, "templates": []})
        self.load_error = error
        self._user = {}
        for item in (data.get("templates") if isinstance(data, dict) else []) or []:
            try:
                template = Template.from_dict(item)
            except Exception:
                continue
            self._user[template.id] = template

    def save(self):
        write_json_atomic(self.path, {
            "version": SCHEMA_VERSION,
            "templates": [t.to_dict() for t in self._user.values()],
        })

    def list_templates(self):
        """Preset dulu, lalu milik user yang terbaru di atas."""
        user = sorted(self._user.values(), key=lambda t: t.updated_at, reverse=True)
        return _presets() + user

    def get(self, template_id: str):
        for template in self.list_templates():
            if template.id == template_id:
                return template
        return None

    def upsert(self, template: Template) -> Template:
        if template.builtin:
            # preset tidak bisa ditimpa -- simpan sebagai salinan milik user
            template = replace(template, id=str(uuid.uuid4()), builtin=False,
                               name=f"{template.name} (salinan)")
        template = replace(template, updated_at=_now_iso())
        self._user[template.id] = template
        self.save()
        return template

    def delete(self, template_id: str) -> bool:
        if template_id in self._user:
            del self._user[template_id]
            self.save()
            return True
        return False
