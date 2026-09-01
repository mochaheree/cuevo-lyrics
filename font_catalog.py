"""
Daftar font yang bisa dipakai renderer.

Masalahnya: Qt memberi *nama keluarga* font ("Inter", "Arial"), sedangkan
Pillow butuh *path file* `.ttf`. Qt tidak mengekspos path-nya. Jadi katalog
ini memindai folder font sistem, membaca nama keluarga tiap file lewat
Pillow sendiri, dan menyimpan pemetaannya.

Kenapa dibaca lewat Pillow, bukan diambil dari Qt: yang harus bisa memuat
font itu Pillow. Kalau daftarnya berasal dari Qt, panel Style bisa
menawarkan font yang ternyata gagal dimuat saat dirender -- gagal di tengah
acara, bukan saat memilih.

Hasil pindaian di-cache ke `fonts.json` karena memindai beberapa ratus file
butuh waktu beberapa detik. Cache divalidasi dengan (ukuran, mtime) folder.

Tanpa import PySide6 (REQ-NF-06).
"""
import os
import sys

from PIL import ImageFont

from store.paths import app_data_dir, read_json, write_json_atomic

CACHE_NAME = "fonts.json"
CACHE_VERSION = 1
EXTENSIONS = (".ttf", ".otf")     # .ttc (koleksi) dilewati: indeks face-nya ambigu


def _font_dirs():
    dirs = []
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        dirs.append(os.path.join(windir, "Fonts"))
        local = os.environ.get("LOCALAPPDATA")
        if local:
            dirs.append(os.path.join(local, "Microsoft", "Windows", "Fonts"))
    elif sys.platform == "darwin":
        dirs += ["/System/Library/Fonts", "/Library/Fonts",
                 os.path.expanduser("~/Library/Fonts")]
    else:
        dirs += ["/usr/share/fonts", os.path.expanduser("~/.local/share/fonts")]

    # font yang dibundel bersama aplikasi menang atas font sistem
    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    if os.path.isdir(bundled):
        dirs.insert(0, bundled)
    return [d for d in dirs if os.path.isdir(d)]


def _scan_signature():
    """Sidik jari murah untuk tahu koleksi font berubah tanpa membacanya lagi."""
    parts = []
    for directory in _font_dirs():
        try:
            parts.append(f"{directory}:{int(os.stat(directory).st_mtime)}:"
                         f"{len(os.listdir(directory))}")
        except OSError:
            continue
    return "|".join(parts)


def _scan():
    """
    {nama keluarga: path}. Kalau satu keluarga punya banyak varian, yang
    dipilih adalah file dengan nama terpendek -- biasanya varian Regular,
    bukan "Arial Black Italic".
    """
    found = {}
    for directory in _font_dirs():
        try:
            names = sorted(os.listdir(directory))
        except OSError:
            continue
        for name in names:
            if not name.lower().endswith(EXTENSIONS):
                continue
            path = os.path.join(directory, name)
            try:
                family, style = ImageFont.truetype(path, 20).getname()
            except Exception:
                continue        # font rusak / tak didukung -- jangan ditawarkan
            if not family:
                continue
            style = (style or "").lower()
            label = family if style in ("regular", "book", "") else f"{family} {style.title()}"
            previous = found.get(label)
            if previous is None or len(os.path.basename(path)) < len(os.path.basename(previous)):
                found[label] = path
    return found


def load(force=False) -> dict:
    """Pemetaan {label font: path}. Dipindai sekali, lalu dibaca dari cache."""
    cache_path = os.path.join(app_data_dir(), CACHE_NAME)
    signature = _scan_signature()

    if not force:
        data, _ = read_json(cache_path, None)
        if (isinstance(data, dict)
                and data.get("version") == CACHE_VERSION
                and data.get("signature") == signature
                and isinstance(data.get("fonts"), dict)):
            fonts = {k: v for k, v in data["fonts"].items() if os.path.exists(v)}
            if fonts:
                return fonts

    fonts = _scan()
    try:
        write_json_atomic(cache_path, {"version": CACHE_VERSION,
                                       "signature": signature, "fonts": fonts})
    except OSError:
        pass                    # cache cuma optimasi; gagal menulis bukan error
    return fonts


def label_for_path(fonts: dict, path: str):
    """Label yang cocok untuk sebuah path, atau None kalau tidak dikenal."""
    if not path:
        return None
    target = os.path.normcase(os.path.abspath(path))
    for label, candidate in fonts.items():
        if os.path.normcase(os.path.abspath(candidate)) == target:
            return label
    return None
