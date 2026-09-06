"""
Tebak struktur lagu (Chorus/Verse/Bridge) dari lirik bertimestamp.

REQ-F-PLAY-09, pendamping penanda manual REQ-F-PLAY-08 (SRS §3.18).

Yang dipakai cuma dua sinyal, dan dua-duanya memang ada di data lirik:

1. **Pengulangan.** Chorus adalah blok baris yang berulang. Ini definisi
   struktural, bukan tebakan gaya, dan bisa dihitung persis.
2. **Jeda waktu.** Jarak antar baris yang jauh lebih besar dari biasanya
   menandai pergantian bagian. Timestamp-nya sudah ada, tinggal dipakai.

Yang **tidak** dipakai, dan tidak akan: analisis audio (aplikasi ini tidak
pernah menyentuh audio sama sekali) dan model bahasa (butuh jaringan,
dependensi, dan tetap tidak bisa dipertanggungjawabkan hasilnya).

Konsekuensinya jujur: ini **tebakan**, bukan kebenaran. Lagu dengan
struktur tidak lazim akan salah tebak. Karena itu hasilnya masuk sebagai
usulan yang bisa langsung dibetulkan operator lewat klik kanan, bukan
ditulis diam-diam ke library.

Tanpa import PySide6 / SpoutGL (REQ-NF-06).
"""
import re
from statistics import median

# Panjang blok berulang yang masuk akal untuk sebuah chorus. Di bawah 2
# baris, hampir semua lagu punya satu baris yang berulang belasan kali dan
# itu bukan chorus. Di atas 12, yang ketemu biasanya "chorus dinyanyikan
# dua kali berturut-turut", bukan chorusnya sendiri.
MIN_RUN = 2
MAX_RUN = 12

# Blok sependek satu-dua baris hampir tidak pernah verse; yang terjadi
# adalah jeda nafas di tengah bagian yang sama terbaca sebagai batas blok.
# Tanpa ambang ini, "Jireh" (137 baris) pecah jadi 10 blok dan menghasilkan
# sembilan "Verse" yang tidak satu pun benar.
MIN_VERSE_LINES = 3

_WORD = re.compile(r"[^\w\s]", re.UNICODE)


def _normalise(text: str) -> str:
    """
    Samakan bentuk baris supaya pengulangan yang "sama tapi beda tanda baca"
    tetap terdeteksi. Ad-lib dalam kurung dibuang: chorus yang diulang
    biasanya identik kecuali tambahan seperti "(oh)" atau "(sing it)", dan
    kalau itu ikut dibandingkan, pengulangannya jadi tidak terlihat.
    """
    text = re.sub(r"\([^)]*\)", " ", text or "")
    text = _WORD.sub(" ", text.lower())
    text = " ".join(text.split())
    return text


def _block_starts(lines) -> list:
    """
    Awal blok, ditandai jeda waktu yang tidak biasa.

    Ambangnya relatif terhadap median jeda lagu itu sendiri, bukan angka
    tetap: lagu cepat dan lagu lambat punya jarak antar baris yang beda
    jauh, dan ambang tetap akan salah di salah satunya.
    """
    if len(lines) < 3:
        return [0] if lines else []
    gaps = [lines[i + 1][0] - lines[i][0] for i in range(len(lines) - 1)]
    typical = median(gaps)
    threshold = max(typical * 2.0, typical + 1.5)
    starts = [0]
    for i, gap in enumerate(gaps):
        if gap > threshold:
            starts.append(i + 1)
    return starts


def _best_repeated_run(tokens, blocked=frozenset()):
    """
    Blok baris berulang terbaik: (panjang, [posisi awal, ...]).

    Skornya panjang x jumlah kemunculan, jadi blok 4 baris yang muncul 3
    kali menang dari blok 2 baris yang muncul 4 kali. Itu yang dimau:
    chorus utuh, bukan potongan pembukanya.

    `blocked` adalah index yang sudah dipakai bagian lain, supaya pencarian
    kedua (untuk pre-chorus) tidak menemukan ulang chorus yang sama.
    """
    n = len(tokens)
    best = None
    for length in range(min(MAX_RUN, n // 2), MIN_RUN - 1, -1):
        seen = {}
        for i in range(n - length + 1):
            span = range(i, i + length)
            if any(j in blocked for j in span):
                continue
            key = tuple(tokens[i:i + length])
            if not any(key):        # blok yang isinya kosong semua
                continue
            seen.setdefault(key, []).append(i)

        for positions in seen.values():
            if len(positions) < 2:
                continue
            # kemunculan yang tumpang tindih dihitung sekali saja, kalau
            # tidak, satu baris yang diulang beruntun terlihat seperti
            # puluhan kemunculan berbeda
            occurrences, last_end = [], -1
            for p in positions:
                if p > last_end:
                    occurrences.append(p)
                    last_end = p + length - 1
            if len(occurrences) < 2:
                continue
            score = length * len(occurrences)
            if best is None or score > best[0]:
                best = (score, length, occurrences)
    if best is None:
        return None
    return best[1], best[2]


def _first_real_line(lines, start, stop) -> int:
    """
    Geser penanda ke baris berteks pertama dalam rentangnya.

    Banyak lirik LRCLIB punya baris kosong sebagai jeda instrumental. Kalau
    penanda mendarat di situ, yang terlihat operator cuma tag melayang tanpa
    lirik, dan bagian yang ditandai justru baru mulai satu-dua baris
    sesudahnya. Terukur di 4 dari 11 lagu uji sebelum ini ditambahkan.
    """
    for i in range(start, min(stop, len(lines))):
        if (lines[i][1] or "").strip():
            return i
    return -1


def detect_sections(lines) -> list:
    """
    Kembalikan [(line_index, label), ...] terurut, siap dipakai
    `Song.sections`. List kosong kalau lagunya terlalu pendek atau tidak
    ada pengulangan sama sekali: lebih baik tidak menandai apa pun
    daripada menandai asal.
    """
    if not lines or len(lines) < 6:
        return []

    tokens = [_normalise(text) for _, text in lines]
    n = len(tokens)

    chorus = _best_repeated_run(tokens)
    if chorus is None:
        return []
    chorus_len, chorus_starts = chorus
    chorus_covered = {i for start in chorus_starts
                      for i in range(start, start + chorus_len)}

    marks = {start: "Chorus" for start in chorus_starts}

    # Pre-chorus: blok berulang lain yang SELALU berhenti tepat sebelum
    # chorus. Kalau tidak selalu, itu bukan pre-chorus, cuma kebetulan.
    second = _best_repeated_run(tokens, blocked=chorus_covered)
    pre_covered = set()
    if second is not None:
        pre_len, pre_starts = second
        if all(start + pre_len in chorus_starts for start in pre_starts):
            for start in pre_starts:
                marks[start] = "Pre-Chorus"
                pre_covered.update(range(start, start + pre_len))

    # Sisanya: blok yang tidak berulang. Dipotong menurut jeda waktu, lalu
    # dinomori sebagai Verse sesuai urutan kemunculan.
    used = chorus_covered | pre_covered
    verse_no = 0
    plain_starts = []
    starts = _block_starts(lines)
    for start in starts:
        if start in used or start in marks:
            continue
        block_end = next((s for s in starts if s > start), n)
        free = [i for i in range(start, block_end) if i not in used]
        # blok yang seluruhnya tenggelam di dalam chorus bukan blok sendiri,
        # dan blok terlalu pendek bukan verse (lihat MIN_VERSE_LINES)
        if len(free) < MIN_VERSE_LINES:
            continue
        plain_starts.append(start)

    # Bridge: blok unik terakhir yang muncul setelah chorus kedua, dan
    # bukan blok penutup. Posisi itu yang membedakan bridge dari verse;
    # tanpa syarat "setelah chorus kedua", verse 3 ikut tertandai bridge.
    bridge_start = None
    if len(chorus_starts) >= 2:
        after_second = [s for s in plain_starts if s > chorus_starts[1]]
        if after_second:
            bridge_start = after_second[0]

    for start in plain_starts:
        if start == bridge_start:
            marks[start] = "Bridge"
        else:
            verse_no += 1
            marks[start] = f"Verse {verse_no}"

    # Pindahkan tiap penanda ke baris berteks terdekat sesudahnya, dan buang
    # yang jadi bertabrakan setelah digeser (dua penanda tidak boleh
    # menempati baris yang sama; yang lebih dulu menang).
    final = {}
    for start, label in sorted(marks.items()):
        stop = next((s for s in sorted(marks) if s > start), n)
        target = _first_real_line(lines, start, max(stop, start + 1))
        if target >= 0 and target not in final:
            final[target] = label

    return sorted(final.items())
