"""
Parser format LRC (synced lyrics) dari LRCLIB.

Contoh baris:
    [00:17.12] I feel your breath upon my neck

Beberapa file punya multi-timestamp untuk baris yang sama:
    [00:17.12][00:45.00] teks yang sama (chorus berulang)

Baris metadata seperti [ar:...], [ti:...], [al:...], [offset:...]
diabaikan karena tidak relevan untuk keperluan tampilan real-time di sini.
"""
import re

_TIME_TAG_RE = re.compile(r"\[(\d{1,3}):(\d{2})(?:\.(\d{1,3}))?\]")
_METADATA_RE = re.compile(r"^\[[a-zA-Z]+:.*\]$")


def parse_lrc(lrc_text: str):
    """
    Mengubah teks LRC menjadi list of tuple (waktu_detik: float, teks: str),
    terurut menaik berdasarkan waktu. Baris tanpa timestamp diabaikan.
    """
    lines = []
    if not lrc_text:
        return lines

    for raw_line in lrc_text.splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        if _METADATA_RE.match(raw_line):
            continue

        tags = list(_TIME_TAG_RE.finditer(raw_line))
        if not tags:
            continue

        text = _TIME_TAG_RE.sub("", raw_line).strip()

        for tag in tags:
            minutes = int(tag.group(1))
            seconds = int(tag.group(2))
            frac_str = tag.group(3) or "0"
            # normalisasi pecahan detik (LRC kadang 2 digit, kadang 3 digit)
            frac = int(frac_str.ljust(3, "0")) / 1000.0
            total_seconds = minutes * 60 + seconds + frac
            lines.append((total_seconds, text))

    lines.sort(key=lambda item: item[0])
    return lines


def format_lrc(parsed_lines, title="", artist="") -> str:
    """
    Kebalikan dari parse_lrc(): ubah list (waktu, teks) jadi teks LRC.

    Dipakai untuk mengekspor lirik hasil ketik manual (REQ-F-LIB-03) supaya
    bisa dipakai di aplikasi lain, dan supaya lirik yang sudah susah payah
    ditandai waktunya tidak terkunci di dalam library.json saja.

    Pecahan detik ditulis 2 digit (centisecond), konvensi paling umum di
    file .lrc dan cukup presisi untuk keperluan tampilan.
    """
    out = []
    if title:
        out.append(f"[ti:{title}]")
    if artist:
        out.append(f"[ar:{artist}]")

    for time_sec, text in sorted(parsed_lines, key=lambda pair: pair[0]):
        time_sec = max(0.0, float(time_sec))
        minutes = int(time_sec // 60)
        seconds = int(time_sec % 60)
        centis = int(round((time_sec - int(time_sec)) * 100))
        if centis == 100:            # pembulatan 59.999 -> jangan jadi ":60.100"
            centis = 0
            seconds += 1
            if seconds == 60:
                seconds = 0
                minutes += 1
        out.append(f"[{minutes:02d}:{seconds:02d}.{centis:02d}]{text}")
    return "\n".join(out)


def find_current_index(parsed_lines, current_time: float) -> int:
    """
    Cari indeks baris lirik yang seharusnya aktif pada current_time (detik),
    yaitu baris berwaktu terbesar yang <= current_time.
    Mengembalikan -1 kalau belum ada baris yang waktunya tercapai,
    atau kalau parsed_lines kosong.

    Dipakai oleh tampilan multi-baris (mode scroll ala Musixmatch) yang
    butuh tahu POSISI baris aktif, bukan cuma teksnya -- supaya baris-baris
    di sekitarnya (sebelum/sesudah) bisa ikut digambar dengan gaya yang
    lebih kecil/pudar.

    Pakai pencarian biner karena parsed_lines sudah terurut menaik,
    supaya tetap ringan dipanggil puluhan kali per detik di loop Spout.
    """
    if not parsed_lines:
        return -1
    if current_time < parsed_lines[0][0]:
        return -1

    lo, hi = 0, len(parsed_lines) - 1
    result = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if parsed_lines[mid][0] <= current_time:
            result = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return result


def find_current_line(parsed_lines, current_time: float) -> str:
    """
    Versi ringkas dari find_current_index() yang langsung mengembalikan
    teksnya saja. Dipertahankan untuk kompatibilitas dengan mode single-line
    lama dan untuk keperluan preview teks di GUI.
    """
    idx = find_current_index(parsed_lines, current_time)
    if idx < 0:
        return ""
    return parsed_lines[idx][1]
