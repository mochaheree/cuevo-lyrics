"""
Semua parameter visual lirik dalam satu objek.

Dipakai bersama oleh thread Spout dan widget preview di GUI. Preview
menggambar di resolusi lebih kecil supaya ringan, tapi harus menghasilkan
tampilan yang identik -- itulah gunanya `scaled()`: ukuran font dan tebal
outline ikut mengecil dengan faktor yang sama, sementara semua parameter
yang sudah berupa rasio dibiarkan apa adanya.

Tidak boleh meng-import PySide6 maupun SpoutGL (SRS REQ-NF-06/07).
Bentuk field mengikuti skema `Template` di SRS §5.3.
"""
from dataclasses import dataclass, asdict, replace


@dataclass(frozen=True)
class RenderStyle:
    # kanvas
    width: int = 1920
    height: int = 1080

    # teks
    font_path: str = None
    active_font_size: int = 64
    text_color: tuple = (255, 255, 255, 255)
    outline_color: tuple = (0, 0, 0, 255)
    outline_width: int = 3

    # tata letak scroll (REQ-F-OUT-04/05)
    layout: str = "scroll_multiline"      # atau "single_line"
    context_before: int = 2
    context_after: int = 2
    line_spacing_ratio: float = 1.55
    vertical_anchor_ratio: float = 0.5
    size_falloff: float = 0.22
    opacity_falloff: float = 0.32
    edge_fade_ratio: float = 0.18

    # animasi (REQ-F-OUT-03)
    transition_ms: int = 550

    def scaled(self, factor: float) -> "RenderStyle":
        """
        Versi lebih kecil/besar dari style ini, untuk preview.

        Hanya besaran dalam piksel yang diskalakan. Rasio (falloff, spacing,
        anchor, edge fade) sudah relatif terhadap kanvas, jadi dibiarkan --
        itu yang membuat preview tetap identik dengan output.
        """
        return replace(
            self,
            width=max(1, round(self.width * factor)),
            height=max(1, round(self.height * factor)),
            active_font_size=max(8, round(self.active_font_size * factor)),
            outline_width=max(0, round(self.outline_width * factor)),
        )

    def scaled_to_width(self, target_width: int) -> "RenderStyle":
        """Skalakan supaya lebarnya jadi `target_width`, rasio aspek terjaga."""
        if self.width <= 0:
            return self
        return self.scaled(target_width / self.width)

    # --- serialisasi untuk store/templates.py (Fase 3) ---

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RenderStyle":
        known = {f for f in cls.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in known}
        for key in ("text_color", "outline_color"):
            if key in clean and isinstance(clean[key], list):
                clean[key] = tuple(clean[key])
        return cls(**clean)


DEFAULT_STYLE = RenderStyle()
