"""
Screen 04 -- panel Style (REQ-F-STYLE-01/02/03, REQ-F-OUT-05).

Setiap perubahan langsung tayang: tidak ada tombol Apply. Kalau output
sedang jalan, style dikirim ke thread Spout lewat `set_style()` dan terlihat
di frame berikutnya (REQ-NF-02, <100ms).

Dua peringatan yang sengaja ditampilkan, karena keduanya adalah jebakan
yang tidak terlihat dari layar:
  - font di bawah ~22px menjatuhkan performa render 5x (SRS §3.2);
  - jumlah baris konteks tidak berarti apa-apa kalau opacity falloff sudah
    memudarkan baris itu lebih dulu -- ditampilkan sebagai "efektif N baris".
"""
from dataclasses import replace

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSlider, QColorDialog, QSpinBox, QMessageBox,
    QInputDialog, QScrollArea, QSizePolicy,
)

import font_catalog
from render_style import RenderStyle, DEFAULT_STYLE
from store.templates import Template
from ui import theme
from ui.preview import PreviewWidget, MIN_SAFE_FONT_PX
from ui.segmented import SegmentedControl


class Row(QWidget):
    """
    Satu baris kontrol: label kiri, isi kanan.

    Label ikut menandai apakah parameternya sudah diubah dari default --
    itu yang membuat fitur klik-kanan-reset bisa ditemukan sendiri, tanpa
    harus dibaca di manual.
    """

    def __init__(self, label, *widgets, parent=None):
        super().__init__(parent)
        box = QHBoxLayout(self)
        box.setContentsMargins(16, 4, 16, 4)
        box.setSpacing(10)
        self.name = QLabel(label)
        self.name.setFixedWidth(104)
        self.name.setToolTip("Klik kanan pada kontrolnya untuk kembali ke default")
        box.addWidget(self.name)
        for widget in widgets:
            box.addWidget(widget)
        self.set_modified(False)

    def set_modified(self, modified):
        # titik kecil, bukan warna mencolok: ini penanda, bukan peringatan
        self.name.setStyleSheet(
            f"color:{theme.T2 if modified else theme.T3};font-size:11px;")
        base = self.name.text().lstrip("• ").rstrip()
        self.name.setText(f"• {base}" if modified else f"  {base}")


class FloatSlider(QWidget):
    """QSlider bilangan bulat + label nilai, dipakai untuk parameter pecahan."""
    changed = Signal(float)

    def __init__(self, low, high, value, decimals=2, suffix="", parent=None):
        super().__init__(parent)
        self._low, self._high = low, high
        self._scale = 10 ** decimals
        self._decimals, self._suffix = decimals, suffix

        box = QHBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(10)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(low * self._scale), int(high * self._scale))
        self.slider.setValue(int(value * self._scale))
        self.slider.valueChanged.connect(self._on_change)
        self.value_label = QLabel()
        self.value_label.setFixedWidth(62)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet(f"color:{theme.T1};font-family:{theme.MONO};font-size:11px;")
        box.addWidget(self.slider, 1)
        box.addWidget(self.value_label)
        self._refresh_label()

    def value(self):
        return self.slider.value() / self._scale

    def set_value(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(int(value * self._scale))
        self.slider.blockSignals(False)
        self._refresh_label()

    def _on_change(self):
        self._refresh_label()
        self.changed.emit(self.value())

    def _refresh_label(self):
        self.value_label.setText(f"{self.value():.{self._decimals}f}{self._suffix}")


class SwatchButton(QPushButton):
    """Kotak warna yang membuka QColorDialog. Alpha ikut bisa diatur."""
    colorPicked = Signal(tuple)

    def __init__(self, rgba, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 22)
        self._rgba = tuple(rgba)
        self._apply()
        self.clicked.connect(self._pick)

    def set_rgba(self, rgba):
        self._rgba = tuple(rgba)
        self._apply()

    def _apply(self):
        r, g, b, a = self._rgba
        theme.paint(self,
            f"background:rgba({r},{g},{b},{a / 255:.2f});"
            f"border:1px solid #46525f;border-radius:2px;"
        )
        self.setToolTip(f"#{r:02X}{g:02X}{b:02X}  alpha {a}")

    def _pick(self):
        color = QColorDialog.getColor(
            QColor(*self._rgba), self, "Pilih warna",
            QColorDialog.ShowAlphaChannel,
        )
        if color.isValid():
            self.set_rgba((color.red(), color.green(), color.blue(), color.alpha()))
            self.colorPicked.emit(self._rgba)


class StyleView(QWidget):
    styleChanged = Signal(object)     # RenderStyle

    def __init__(self, player_state, style, store, parent=None):
        super().__init__(parent)
        self.player_state = player_state
        self.store = store
        self.style = style
        self._loading = False
        self._fonts = font_catalog.load()

        # Registry untuk klik-kanan-reset ala Resolume:
        #   widget kontrol -> nama field di RenderStyle
        #   widget anak    -> widget kontrol pemiliknya
        # Dipakai lewat event filter, bukan dengan men-subclass tiap jenis
        # widget -- QSlider, QComboBox, QSpinBox, dan QPushButton warna semuanya
        # berbeda, tapi perlakuan klik kanannya sama.
        self._field_of = {}
        self._owner_of = {}
        self._row_of_field = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_controls(), 1)

        seam = QWidget()
        seam.setFixedWidth(1)
        theme.paint(seam,f"background:{theme.SEAM};")
        root.addWidget(seam)
        root.addWidget(self._build_preview(), 1)

        self.refresh_templates()
        self._load_into_controls(self.style)

    # ---------- kanan: preview ----------

    def _build_preview(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        head = QLabel("  Program — apa yang tayang")
        theme.paint(head,
            f"background:{theme.V3};color:{theme.T3};font-size:11px;padding:6px 12px;"
            f"border-bottom:1px solid {theme.SEAM};")
        box.addWidget(head)

        wrap = QWidget()
        theme.paint(wrap,f"background:{theme.V1};")
        wb = QVBoxLayout(wrap)
        wb.setContentsMargins(14, 14, 14, 14)
        self.preview = PreviewWidget(self.player_state, self.style)
        wb.addWidget(self.preview)
        box.addWidget(wrap)

        self.warning = QLabel("")
        self.warning.setWordWrap(True)
        theme.paint(self.warning,
            f"color:{theme.STANDBY};font-size:11px;padding:9px 14px;"
            f"border-top:1px solid {theme.SEAM};background:{theme.V2};")
        self.warning.hide()
        box.addWidget(self.warning)

        note = QLabel(
            "Perubahan langsung tayang — tidak ada tombol Apply.\n"
            "Kalau output sedang jalan, Resolume ikut berubah seketika."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{theme.T3};font-size:11px;padding:10px 14px;")
        box.addWidget(note)
        box.addStretch(1)
        return panel

    # ---------- kiri: kontrol ----------

    def _build_controls(self):
        inner = QWidget()
        box = QVBoxLayout(inner)
        box.setContentsMargins(0, 0, 0, 12)
        box.setSpacing(0)

        box.addWidget(self._template_bar())

        box.addWidget(self._group("Tampilan"))
        self.layout_seg = SegmentedControl(["Scroll multiline", "Single line"])
        self.layout_scroll = self.layout_seg.button(0)
        self.layout_single = self.layout_seg.button(1)
        self.layout_scroll.toggled.connect(self._emit)
        box.addWidget(self._bind(Row("Layout", self.layout_seg, _stretch()),
                                 (self.layout_seg, "layout")))

        self.font_combo = QComboBox()
        self.font_combo.addItem("(bawaan sistem)", None)
        for label in sorted(self._fonts):
            self.font_combo.addItem(label, self._fonts[label])
        self.font_combo.currentIndexChanged.connect(self._emit)
        box.addWidget(self._bind(Row("Font", self.font_combo), (self.font_combo, "font_path")))

        self.size_slider = FloatSlider(16, 200, 64, decimals=0, suffix=" px")
        self.size_slider.changed.connect(self._emit)
        box.addWidget(self._bind(Row("Ukuran", self.size_slider),
                                 (self.size_slider, "active_font_size")))

        self.text_color = SwatchButton((255, 255, 255, 255))
        self.text_color.colorPicked.connect(self._emit)
        self.text_hex = QLabel()
        self.text_hex.setStyleSheet(f"color:{theme.T2};font-family:{theme.MONO};font-size:11px;")
        box.addWidget(self._bind(Row("Warna teks", self.text_color, self.text_hex, _stretch()),
                                 (self.text_color, "text_color")))

        self.outline_color = SwatchButton((0, 0, 0, 255))
        self.outline_color.colorPicked.connect(self._emit)
        self.outline_slider = FloatSlider(0, 12, 3, decimals=0, suffix=" px")
        self.outline_slider.changed.connect(self._emit)
        box.addWidget(self._bind(Row("Outline", self.outline_color, self.outline_slider),
                                 (self.outline_color, "outline_color"),
                                 (self.outline_slider, "outline_width")))

        box.addWidget(self._group("Scroll — REQ-F-OUT-05"))
        self.before_spin = QSpinBox()
        self.after_spin = QSpinBox()
        for spin in (self.before_spin, self.after_spin):
            spin.setRange(0, 6)
            spin.setFixedWidth(56)
            spin.valueChanged.connect(self._emit)
        self.context_hint = QLabel()
        self.context_hint.setStyleSheet(f"color:{theme.T3};font-size:11px;")
        box.addWidget(self._bind(Row("Baris konteks", _tag("sebelum"), self.before_spin,
                                     _tag("sesudah"), self.after_spin, self.context_hint, _stretch()),
                                 (self.before_spin, "context_before"),
                                 (self.after_spin, "context_after")))

        self.spacing_slider = FloatSlider(0.8, 3.0, 1.55, suffix="×")
        self.size_falloff = FloatSlider(0.0, 0.6, 0.22)
        self.opacity_falloff = FloatSlider(0.0, 0.9, 0.32)
        self.edge_fade = FloatSlider(0.0, 0.5, 0.18)
        self.anchor = FloatSlider(0.0, 1.0, 0.50)
        self.transition = FloatSlider(0, 2000, 550, decimals=0, suffix=" ms")
        for label, widget, field in (("Jarak baris", self.spacing_slider, "line_spacing_ratio"),
                                     ("Size falloff", self.size_falloff, "size_falloff"),
                                     ("Opacity falloff", self.opacity_falloff, "opacity_falloff"),
                                     ("Edge fade", self.edge_fade, "edge_fade_ratio"),
                                     ("Anchor Y", self.anchor, "vertical_anchor_ratio"),
                                     ("Transisi", self.transition, "transition_ms")):
            widget.changed.connect(self._emit)
            box.addWidget(self._bind(Row(label, widget), (widget, field)))

        box.addStretch(1)

        area = QScrollArea()
        area.setWidget(inner)
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.NoFrame)
        return area

    def _group(self, title):
        label = QLabel(title)
        theme.paint(label,
            f"color:{theme.T3};font-size:11px;padding:14px 16px 6px;"
            f"border-top:1px solid {theme.SEAM};")
        return label

    # ---------- klik kanan = kembali ke default (ala Resolume) ----------

    def _bind(self, row, *pairs):
        """
        Daftarkan kontrol-kontrol di sebuah Row ke field RenderStyle-nya, lalu
        pasang event filter ke kontrol itu beserta seluruh anaknya (klik
        sebenarnya diterima anak: QSlider di dalam FloatSlider, QLineEdit di
        dalam QSpinBox, dan seterusnya).
        """
        for widget, field in pairs:
            self._field_of[widget] = field
            self._row_of_field[field] = row
            widget.installEventFilter(self)
            for child in widget.findChildren(QWidget):
                self._owner_of[child] = widget
                child.installEventFilter(self)
                # matikan menu konteks bawaan Qt, kalau tidak menu itu yang
                # muncul alih-alih parameter ter-reset
                child.setContextMenuPolicy(Qt.NoContextMenu)
            widget.setContextMenuPolicy(Qt.NoContextMenu)
        return row

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.MouseButtonPress
                and event.button() == Qt.RightButton):
            owner = self._owner_of.get(obj, obj)
            field = self._field_of.get(owner)
            if field is not None:
                self.reset_field(field)
                return True     # jangan diteruskan; klik kanan cuma untuk ini
        return super().eventFilter(obj, event)

    def reset_field(self, field):
        """Kembalikan satu parameter ke nilai bawaan, lalu langsung tayang."""
        default = getattr(DEFAULT_STYLE, field)
        self._loading = True
        self._apply_field(field, default)
        self._loading = False
        self._emit()

    def _apply_field(self, field, value):
        if field == "layout":
            (self.layout_single if value == "single_line" else self.layout_scroll).setChecked(True)
        elif field == "font_path":
            index = self.font_combo.findData(value)
            self.font_combo.setCurrentIndex(index if index >= 0 else 0)
        elif field == "active_font_size":
            self.size_slider.set_value(value)
        elif field == "text_color":
            self.text_color.set_rgba(value)
        elif field == "outline_color":
            self.outline_color.set_rgba(value)
        elif field == "outline_width":
            self.outline_slider.set_value(value)
        elif field == "context_before":
            self.before_spin.setValue(value)
        elif field == "context_after":
            self.after_spin.setValue(value)
        elif field == "line_spacing_ratio":
            self.spacing_slider.set_value(value)
        elif field == "size_falloff":
            self.size_falloff.set_value(value)
        elif field == "opacity_falloff":
            self.opacity_falloff.set_value(value)
        elif field == "edge_fade_ratio":
            self.edge_fade.set_value(value)
        elif field == "vertical_anchor_ratio":
            self.anchor.set_value(value)
        elif field == "transition_ms":
            self.transition.set_value(value)

    def reset_all(self):
        self._loading = True
        for field in self._row_of_field:
            self._apply_field(field, getattr(DEFAULT_STYLE, field))
        self._loading = False
        self._emit()

    def _template_bar(self):
        bar = QWidget()
        theme.paint(bar,f"background:{theme.V2};border-bottom:1px solid {theme.SEAM};")
        box = QHBoxLayout(bar)
        box.setContentsMargins(16, 10, 16, 10)
        box.setSpacing(7)
        self.template_combo = QComboBox()
        self.template_combo.currentIndexChanged.connect(self._on_template_selected)
        save_btn = QPushButton("Simpan")
        save_btn.clicked.connect(self.save_template)
        saveas_btn = QPushButton("Simpan sbg…")
        saveas_btn.setProperty("variant", "quiet")
        saveas_btn.clicked.connect(self.save_template_as)
        del_btn = QPushButton("Hapus")
        del_btn.setProperty("variant", "quiet")
        del_btn.clicked.connect(self.delete_template)
        reset_btn = QPushButton("Reset semua")
        reset_btn.setProperty("variant", "quiet")
        reset_btn.setToolTip("Kembalikan SEMUA parameter ke default.\n"
                             "Untuk satu parameter saja: klik kanan pada kontrolnya.")
        reset_btn.clicked.connect(self._confirm_reset_all)
        box.addWidget(self.template_combo, 1)
        for btn in (save_btn, saveas_btn, del_btn, reset_btn):
            box.addWidget(btn)
        return bar

    def _confirm_reset_all(self):
        # reset satu parameter cukup diklik kanan lagi kalau salah; reset semua
        # bisa menghapus penyetelan panjang, jadi yang ini ditanya dulu
        changed = sum(1 for field in self._row_of_field
                      if getattr(self.style, field) != getattr(DEFAULT_STYLE, field))
        if not changed:
            return
        if QMessageBox.question(
            self, "Reset semua parameter",
            f"{changed} parameter berbeda dari default dan akan dikembalikan.\n\n"
            f"Lanjutkan?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) == QMessageBox.Yes:
            self.reset_all()

    # ---------- template ----------

    def refresh_templates(self, select_id=None):
        self._loading = True
        self.template_combo.clear()
        for template in self.store.list_templates():
            prefix = "◆ " if template.builtin else "   "
            self.template_combo.addItem(prefix + template.name, template.id)
        self._loading = False
        if select_id:
            index = self.template_combo.findData(select_id)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)

    def _on_template_selected(self):
        if self._loading:
            return
        template = self.store.get(self.template_combo.currentData())
        if template is None:
            return
        # resolusi tidak ikut template -- itu milik Settings
        self._load_into_controls(replace(template.style,
                                         width=self.style.width,
                                         height=self.style.height))
        self._emit()

    def save_template(self):
        current = self.store.get(self.template_combo.currentData())
        name = current.name if current else "Template baru"
        saved = self.store.upsert(Template(name=name, style=self.style,
                                           id=current.id if current else None,
                                           builtin=bool(current and current.builtin)))
        self.refresh_templates(saved.id)

    def save_template_as(self):
        name, ok = QInputDialog.getText(self, "Simpan template", "Nama template:")
        if not ok or not name.strip():
            return
        saved = self.store.upsert(Template(name=name.strip(), style=self.style))
        self.refresh_templates(saved.id)

    def delete_template(self):
        template = self.store.get(self.template_combo.currentData())
        if template is None:
            return
        if template.builtin:
            QMessageBox.information(
                self, "Preset bawaan",
                f"“{template.name}” adalah preset bawaan dan tidak bisa dihapus.\n\n"
                "Pakai “Simpan sbg…” untuk membuat versimu sendiri."
            )
            return
        if QMessageBox.question(
            self, "Hapus template", f"Hapus “{template.name}”?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) == QMessageBox.Yes:
            self.store.delete(template.id)
            self.refresh_templates()

    # ---------- sinkron kontrol <-> style ----------

    def _load_into_controls(self, style):
        self._loading = True
        self.style = style
        (self.layout_single if style.layout == "single_line" else self.layout_scroll).setChecked(True)
        index = self.font_combo.findData(style.font_path)
        self.font_combo.setCurrentIndex(index if index >= 0 else 0)
        self.size_slider.set_value(style.active_font_size)
        self.text_color.set_rgba(style.text_color)
        self.outline_color.set_rgba(style.outline_color)
        self.outline_slider.set_value(style.outline_width)
        self.before_spin.setValue(style.context_before)
        self.after_spin.setValue(style.context_after)
        self.spacing_slider.set_value(style.line_spacing_ratio)
        self.size_falloff.set_value(style.size_falloff)
        self.opacity_falloff.set_value(style.opacity_falloff)
        self.edge_fade.set_value(style.edge_fade_ratio)
        self.anchor.set_value(style.vertical_anchor_ratio)
        self.transition.set_value(style.transition_ms)
        self._loading = False
        self._refresh_hints()

    def _style_from_controls(self) -> RenderStyle:
        return replace(
            self.style,
            layout="single_line" if self.layout_single.isChecked() else "scroll_multiline",
            font_path=self.font_combo.currentData(),
            active_font_size=int(self.size_slider.value()),
            text_color=self.text_color._rgba,
            outline_color=self.outline_color._rgba,
            outline_width=int(self.outline_slider.value()),
            context_before=self.before_spin.value(),
            context_after=self.after_spin.value(),
            line_spacing_ratio=self.spacing_slider.value(),
            size_falloff=self.size_falloff.value(),
            opacity_falloff=self.opacity_falloff.value(),
            edge_fade_ratio=self.edge_fade.value(),
            vertical_anchor_ratio=self.anchor.value(),
            transition_ms=int(self.transition.value()),
        )

    def _emit(self):
        if self._loading:
            return
        self.style = self._style_from_controls()
        self.preview.set_style(self.style)
        self._refresh_hints()
        self.styleChanged.emit(self.style)

    def apply_resolution(self, width, height):
        """Resolusi diubah dari tab Settings, bukan dari sini."""
        self.style = replace(self.style, width=width, height=height)
        self.preview.set_style(self.style)

    # ---------- peringatan ----------

    def _visible_context(self, direction):
        """
        Berapa baris konteks yang BENAR-BENAR terlihat ke arah tertentu.

        Baris dibatasi dua hal sekaligus: jumlah baris konteks, dan opacity
        falloff. Yang lebih ketat menang. Tanpa ditampilkan, menaikkan
        "baris konteks" bisa terasa tidak berefek apa-apa.
        """
        limit = self.before_spin.value() if direction < 0 else self.after_spin.value()
        falloff = self.opacity_falloff.value()
        visible = 0
        for distance in range(1, limit + 1):
            opacity = max(0.0, 1.0 - distance * falloff)
            opacity *= max(0.0, min(1.0, (limit + 1) - distance))
            if opacity > 0.02:
                visible += 1
        return visible

    def _refresh_modified_marks(self):
        """
        Tandai parameter yang berbeda dari default.

        Tanpa ini, klik-kanan-reset tidak akan pernah ditemukan orang, dan
        saat menyetel style sambil live tidak ada cara cepat menjawab
        "yang mana tadi yang aku ubah?".
        """
        for field, row in self._row_of_field.items():
            row.set_modified(getattr(self.style, field) != getattr(DEFAULT_STYLE, field))

    def _refresh_hints(self):
        self._refresh_modified_marks()
        r, g, b, a = self.text_color._rgba
        self.text_hex.setText(f"#{r:02X}{g:02X}{b:02X}")

        before, after = self._visible_context(-1), self._visible_context(+1)
        asked = self.before_spin.value() + self.after_spin.value()
        self.context_hint.setText(f"efektif {before}+{after}")
        self.context_hint.setStyleSheet(
            f"color:{theme.STANDBY if (before + after) < asked else theme.T3};font-size:11px;")

        messages = []
        size = int(self.size_slider.value())
        smallest = size * max(0.0, 1.0 - 2 * self.size_falloff.value())
        if size < MIN_SAFE_FONT_PX or (smallest and smallest < MIN_SAFE_FONT_PX):
            messages.append(
                f"⚠ Font efektif turun sampai ~{smallest:.0f}px. Di bawah "
                f"{MIN_SAFE_FONT_PX}px, render jadi sekitar 5× lebih lambat dan fps "
                f"bisa anjlok saat animasi — padahal angka fps di strip atas "
                f"tetap terlihat normal (SRS §3.2)."
            )
        if (before + after) < asked:
            messages.append(
                f"⚠ Kamu meminta {asked} baris konteks tapi hanya {before + after} "
                f"yang terlihat — opacity falloff sudah memudarkan sisanya. "
                f"Turunkan “Opacity falloff” kalau ingin lebih banyak baris tampak."
            )
        if messages:
            self.warning.setText("\n\n".join(messages))
            self.warning.show()
        else:
            self.warning.hide()


def _stretch():
    widget = QWidget()
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return widget


def _tag(text):
    label = QLabel(text)
    label.setStyleSheet(f"color:{theme.T4};font-size:11px;")
    return label
