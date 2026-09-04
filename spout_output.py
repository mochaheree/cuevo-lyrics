"""
Output ke Resolume Arena lewat Spout.

Cara kerja:
  1. Bikin OpenGL context lewat pygame (Spout butuh context GL aktif di
     thread yang memanggilnya). Window-nya dibuat kecil (256x256) dan
     TIDAK ditutup selama proses berjalan -- window ini cuma "wadah"
     context GPU, ukurannya tidak ada hubungannya dengan resolusi frame
     lirik yang dikirim.
  2. Render BEBERAPA baris lirik sekaligus ke gambar RGBA transparan
     pakai Pillow, bergaya scroll seperti Musixmatch: baris aktif
     ditonjolkan (besar, tegas), baris-baris di sekitarnya mengecil dan
     memudar sesuai jaraknya, dan posisinya berpindah dengan animasi
     halus (bukan potong instan) tiap kali baris aktif berganti.
  3. Kirim buffer gambar itu ke Spout sender lewat SpoutGL.sendImage().
  4. Di Resolume Arena: klik kanan pada layer/clip -> Sources -> Spout,
     lalu pilih nama sender ini (default "CUEVO Lyrics").

CATATAN PENTING: modul ini hanya benar-benar bisa mengirim ke Spout di
Windows, karena Spout adalah teknologi sharing tekstur GPU khusus
Windows. Kalau SpoutGL/pygame belum terpasang atau kamu bukan di
Windows, SPOUT_AVAILABLE akan False dan aplikasi akan kasih tahu lewat
GUI -- tapi pencarian lirik & logika playback tetap bisa dites di OS
apa pun.
"""
import threading
import time

from PIL import Image, ImageDraw, ImageFont

from dataclasses import replace

from render_style import RenderStyle, DEFAULT_STYLE
from scroll_anim import ScrollAnimator, ease_out_cubic

try:
    import pygame
    import SpoutGL
    from OpenGL import GL
    SPOUT_AVAILABLE = True
except ImportError:
    SPOUT_AVAILABLE = False


# dipertahankan sebagai alias supaya kode lama yang memanggilnya tetap jalan;
# sumber kebenarannya sekarang ada di scroll_anim.py (dipakai bersama preview)
_ease_out_cubic = ease_out_cubic


def build_renderer(style: RenderStyle) -> "MultiLineLyricRenderer":
    """
    Bikin renderer dari sebuah RenderStyle. Ini satu-satunya jalan yang
    dipakai baik oleh thread Spout maupun widget preview di GUI, supaya
    keduanya dijamin menghasilkan tampilan yang sama (REQ-F-OUT-08).
    """
    # Mode single_line (gaya lower-third v0.1) diwujudkan sebagai "nol baris
    # konteks", bukan sebagai jalur render terpisah. Satu jalur render lebih
    # sedikit tempat untuk menyimpang -- semangat yang sama dengan REQ-F-OUT-08.
    single = style.layout == "single_line"
    return MultiLineLyricRenderer(
        style.width, style.height,
        font_path=style.font_path,
        active_font_size=style.active_font_size,
        text_color=style.text_color,
        outline_color=style.outline_color,
        outline_width=style.outline_width,
        context_before=0 if single else style.context_before,
        context_after=0 if single else style.context_after,
        line_spacing_ratio=style.line_spacing_ratio,
        vertical_anchor_ratio=style.vertical_anchor_ratio,
        edge_fade_ratio=style.edge_fade_ratio,
        size_falloff=style.size_falloff,
        opacity_falloff=style.opacity_falloff,
    )


class MultiLineLyricRenderer:
    """
    Menggambar beberapa baris lirik sekaligus ke buffer RGBA transparan,
    dengan baris aktif di posisi `displayed_pos` ditonjolkan dan baris
    lain di sekitarnya mengecil/memudar sesuai jarak -- gaya scroll ala
    Musixmatch. `displayed_pos` boleh berupa angka pecahan (mis. 2.4)
    saat sedang dalam animasi transisi antar baris.
    """

    def __init__(self, width, height, font_path=None, active_font_size=64,
                 text_color=(255, 255, 255, 255), outline_color=(0, 0, 0, 255),
                 outline_width=3, context_before=2, context_after=2,
                 line_spacing_ratio=1.55, vertical_anchor_ratio=0.5,
                 edge_fade_ratio=0.18, size_falloff=0.22, opacity_falloff=0.32):
        self.width = width
        self.height = height
        self.text_color = text_color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.context_before = context_before
        self.context_after = context_after
        self.line_spacing = int(active_font_size * line_spacing_ratio)
        self.vertical_anchor_y = height * vertical_anchor_ratio
        self.edge_fade_px = height * edge_fade_ratio
        self.size_falloff = size_falloff
        self.opacity_falloff = opacity_falloff
        self.active_font_size = active_font_size

        candidates = [font_path] if font_path else ["arial.ttf", "Arial.ttf", "DejaVuSans-Bold.ttf"]
        self._font_path = None
        for candidate in candidates:
            if not candidate:
                continue
            try:
                ImageFont.truetype(candidate, active_font_size)
                self._font_path = candidate
                break
            except OSError:
                continue
        if self._font_path is None:
            print("[MultiLineLyricRenderer] No TrueType font found, falling back to Pillow's "
                  "built-in font (fixed small size). Set font_path to a valid .ttf if needed.")
        self._font_cache = {}

    def _font(self, size: int):
        size = max(8, size)
        font = self._font_cache.get(size)
        if font is None:
            if self._font_path:
                font = ImageFont.truetype(self._font_path, size)
            else:
                font = ImageFont.load_default()
            self._font_cache[size] = font
        return font

    def _style_at_distance(self, dist: float):
        """
        dist = jarak (boleh pecahan) antara indeks baris ini dan posisi
        baris aktif saat ini. dist=0 -> baris aktif (paling besar/terang).
        """
        d = abs(dist)
        size = max(12, int(self.active_font_size * max(0.0, 1.0 - d * self.size_falloff)))
        opacity = max(0.0, 1.0 - d * self.opacity_falloff)
        weight_bold = d < 0.5
        return size, opacity, weight_bold

    def _context_factor(self, dist: float) -> float:
        """
        Seberapa tampak sebuah baris berdasarkan batas jumlah baris konteks
        (REQ-F-OUT-05), terpisah dari opacity falloff.

        Dulu `context_before`/`context_after` hanya melebarkan jendela pindai,
        sementara yang benar-benar menentukan baris tampil atau tidak cuma
        `opacity_falloff` -- artinya kedua pengaturan itu tidak berpengaruh
        apa pun. Terbukti: context 0, 1, 2, dan 4 sama-sama menampilkan 5
        baris. Lihat SRS §3.4.

        Nilainya meredup bertahap sampai nol di jarak (batas + 1), bukan
        memotong tegas, supaya baris tidak muncul/hilang mendadak saat
        animasi transisi sedang berjalan.
        """
        limit = self.context_before if dist < 0 else self.context_after
        return max(0.0, min(1.0, (limit + 1) - abs(dist)))

    def _edge_fade(self, y: float) -> float:
        """Baris yang mepet tepi atas/bawah kanvas ikut memudar (alpha), supaya
        tidak terpotong tegas di batas frame."""
        top_dist = y
        bottom_dist = self.height - y
        nearest = min(top_dist, bottom_dist)
        if nearest >= self.edge_fade_px:
            return 1.0
        return max(0.0, nearest / self.edge_fade_px)

    def render(self, lines, displayed_pos: float) -> bytes:
        """
        lines: list of (time_sec, text) -- hasil parse_lrc().
        displayed_pos: indeks baris yang sedang berada di tengah (pecahan
        saat animasi berjalan; -1 kalau belum ada baris yang aktif).
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        if not lines:
            return img.tobytes("raw", "RGBA")

        draw = ImageDraw.Draw(img)
        window = self.context_before + self.context_after + 2  # buffer ekstra utk animasi
        center_idx = round(displayed_pos)
        lo = max(0, center_idx - window)
        hi = min(len(lines) - 1, center_idx + window)

        for i in range(lo, hi + 1):
            dist = i - displayed_pos
            size, opacity, bold = self._style_at_distance(dist)
            opacity *= self._context_factor(dist)
            if opacity <= 0.02:
                continue

            y_center = self.vertical_anchor_y + dist * self.line_spacing
            if y_center < -size or y_center > self.height + size:
                continue

            opacity *= self._edge_fade(y_center)
            if opacity <= 0.02:
                continue

            text = lines[i][1]
            if not text:
                continue

            font = self._font(size)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (self.width - text_w) / 2 - bbox[0]
            y = y_center - text_h / 2 - bbox[1]

            alpha = int(255 * opacity)
            fill = (*self.text_color[:3], min(self.text_color[3], alpha))
            outline_fill = (*self.outline_color[:3], min(self.outline_color[3], alpha))

            ow = self.outline_width if dist == 0 or abs(dist) < 1 else max(1, self.outline_width - 1)

            # Pakai stroke_width bawaan Pillow, JANGAN menggambar teks berkali-kali
            # dengan offset. Cara manual itu butuh (2*ow+1)^2 - 1 = 48 kali draw per
            # baris untuk ow=3 -- sekitar 290 draw per frame -- dan itulah yang bikin
            # satu frame 1920x1080 makan ~137ms (maks 7 fps). stroke_width melakukan
            # hal yang sama dalam satu lintasan: ~9ms, dan outline-nya membulat rapi
            # di sudut, bukan kotak. Diukur, bukan diperkirakan -- lihat SRS §3.2.
            draw.text((x, y), text, font=font, fill=fill,
                      stroke_width=ow, stroke_fill=outline_fill)

        return img.tobytes("raw", "RGBA")


class SpoutOutputThread(threading.Thread):
    """
    Thread terpisah yang membuka koneksi Spout dan terus mengirim frame
    lirik (mode scroll multi-baris) berdasarkan PlayerState yang
    di-share dengan GUI Tkinter.
    """

    def __init__(self, player_state, sender_name="CUEVO Lyrics", style=None, fps=30):
        super().__init__(daemon=True)
        self.player_state = player_state
        self.sender_name = sender_name
        self.style = style or DEFAULT_STYLE
        self.fps = fps
        self._stop_event = threading.Event()
        self.status = "not started"
        self.actual_fps = 0.0

        # Frame terakhir yang dikirim, supaya preview di GUI bisa menampilkan
        # buffer yang SAMA PERSIS tanpa merendernya ulang (REQ-F-OUT-08).
        # Berupa tuple (bytes, width, height) dan hanya pernah diganti utuh --
        # penugasan satu atribut bersifat atomik di bawah GIL, jadi pembaca
        # tidak akan pernah melihat gambar setengah jadi.
        self.latest_frame = None

        # Style yang menunggu dipasang. Panel Style menulis ke sini dari thread
        # GUI; loop render mengambilnya di awal frame berikutnya. Satu penugasan
        # atribut, atomik di bawah GIL -- tidak perlu lock, dan tidak ada frame
        # yang dirender separuh style lama separuh baru.
        self._pending_style = None

    @property
    def width(self):
        return self.style.width

    @property
    def height(self):
        return self.style.height

    def set_style(self, style):
        """
        Ganti style tanpa menghentikan output (REQ-NF-02: terlihat <100ms).

        Lebar/tinggi TIDAK ikut diganti: mengubah ukuran sender di tengah
        siaran membuat receiver di sisi Resolume harus menyambung ulang, dan
        itu terlihat sebagai kedipan. Resolusi hanya bisa diubah dari tab
        Settings, saat output berhenti.
        """
        self._pending_style = replace(style, width=self.style.width,
                                      height=self.style.height)

    def stop(self):
        self._stop_event.set()

    def run(self):
        if not SPOUT_AVAILABLE:
            self.status = ("SpoutGL/pygame not installed, or not running on Windows. "
                            "Run: pip install SpoutGL pygame PyOpenGL")
            return

        try:
            pygame.init()
            # window kecil cuma buat pegang context OpenGL -- jangan ditutup manual
            pygame.display.set_mode((256, 256), pygame.OPENGL | pygame.DOUBLEBUF)
            pygame.display.set_caption(f"CUEVO Lyrics running - do not close ({self.sender_name})")

            renderer = build_renderer(self.style)
            animator = ScrollAnimator(self.style.transition_ms)

            with SpoutGL.SpoutSender() as sender:
                sender.setSenderName(self.sender_name)
                self.status = f"sending to Resolume as Spout sender '{self.sender_name}'"

                frame_interval = 1.0 / self.fps
                frame_bytes = renderer.render([], -1.0)
                last_blank = False

                while not self._stop_event.is_set():
                    start = time.perf_counter()
                    pygame.event.pump()  # supaya window kecil tidak dianggap "not responding"

                    pending = self._pending_style
                    if pending is not None and pending != self.style:
                        # bangun renderer baru DULU, baru tukar -- kalau font
                        # yang dipilih ternyata gagal dimuat, output lama tetap
                        # jalan alih-alih thread mati di tengah acara
                        try:
                            renderer = build_renderer(pending)
                            self.style = pending
                            animator.set_transition_ms(pending.transition_ms)
                            animator.force_redraw()
                        except Exception as exc:
                            self.status = f"style rejected: {exc}"
                        self._pending_style = None

                    lines = self.player_state.get_lines()
                    current_time = self.player_state.get_current_time()
                    active_index = self.player_state.get_active_index(current_time)

                    # REQ-F-PLAY-04: BLANK harus mengosongkan yang TAYANG, bukan
                    # cuma preview di GUI. Waktu tetap berjalan, jadi saat blank
                    # dilepas lirik langsung menyambung di posisi yang benar.
                    blank = self.player_state.is_blank()
                    if blank:
                        lines = []
                    if blank != last_blank:
                        # tanpa ini, cache frame (REQ-F-OUT-02) akan terus
                        # mengirim frame lama yang masih berisi lirik
                        animator.force_redraw()
                        last_blank = blank

                    # ScrollAnimator memakai lines_version, BUKAN id(lines).
                    # id() berubah tiap frame karena get_lines() mengembalikan
                    # salinan baru -- itu bug yang mematikan animasi sekaligus
                    # cache frame (SRS §3.1).
                    displayed_pos, need_redraw = animator.update(
                        active_index, self.player_state.get_lines_version()
                    )
                    if need_redraw:
                        frame_bytes = renderer.render(lines, displayed_pos)
                        self.latest_frame = (frame_bytes, self.width, self.height)

                    sender.sendImage(frame_bytes, self.width, self.height, GL.GL_RGBA, False, 0)
                    sender.setFrameSync(self.sender_name)

                    elapsed = time.perf_counter() - start
                    time.sleep(max(0.0, frame_interval - elapsed))

                    # fps diukur dari periode frame penuh (termasuk sleep),
                    # bukan dari lama render -- kalau diukur dari render saja
                    # angkanya akan jauh di atas target dan tidak ada artinya.
                    period = time.perf_counter() - start
                    self.actual_fps = self.actual_fps * 0.9 + (1.0 / max(period, 1e-6)) * 0.1

            pygame.quit()
            self.status = "stopped"
        except Exception as exc:  # tampilkan error apapun ke GUI lewat status, bukan crash diam-diam
            self.status = f"error: {exc}"
