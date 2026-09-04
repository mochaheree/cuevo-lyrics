# CUEVO Lyrics UI Mockup (v0.3 draft)

> **Status: arsip.** Ini wireframe rancangan sebelum aplikasinya dibangun,
> disimpan sebagai catatan asal-usul desainnya. Yang jadi tidak persis sama:
> ada tab **Donate** yang belum terpikir waktu itu, jendela **Cast** (§3.14),
> dan seluruh teks antarmuka sekarang berbahasa Inggris. Yang berlaku
> sekarang ada di `SRS.md` dan di aplikasinya sendiri.

Turunan langsung dari `SRS.md`. Setiap panel diberi tag requirement
supaya bisa dilacak balik. Target window: **1280×800 minimum**, resizable.

Legend: `⠿` drag handle · `▶` baris/lagu aktif · `✓` sudah lewat · `●` status hidup

---

## Screen 1: LIVE (layar utama operator)

Ini layar yang dipakai 95% waktu saat show berjalan.

```
┌─ CUEVO Lyrics ─────────────────────────────────────────────────────────────────────────┐
│  ● Spout: CUEVO Lyrics · 1920×1080 · 30fps · 28.9fps aktual        [− Blank]  [■ Stop]   │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  ▌LIVE▐  Library   Show   Style   Settings                                            │
├──────────────────────┬─────────────────────────────────┬──────────────────────────────┤
│ SET LIST       3/8   │ THE CHAIN - Fleetwood Mac       │ OUTPUT PREVIEW        [live] │
│                      │                                 │ ┌──────────────────────────┐ │
│ ⠿ 1 ✓ Opening        │   [00:24.10] Listen to the wi…  │ │                          │ │
│ ⠿ 2 ✓ Great Are You  │   [00:27.93] Watch the sun ri…  │ │   ·watch the sun rise·   │ │
│ ⠿ 3 ▶ The Chain      │ ▶ [00:30.88] Run in the shadows │ │                          │ │
│ ⠿ 4   Oceans         │   [00:34.02] Damn your love     │ │  RUN IN THE SHADOWS      │ │
│ ⠿ 5   Build My Life  │   [00:36.55] Damn your lies     │ │                          │ │
│ ⠿ 6   Way Maker      │   [00:39.11] And if you don't…  │ │   ·damn your love·       │ │
│ ⠿ 7   Goodness       │   [00:42.70] Break the silence  │ │    ·damn your lies·      │ │
│ ⠿ 8   Closing        │   [00:45.33] Damn the dark      │ │                          │ │
│                      │   [00:47.90] Damn the light     │ └──────────────────────────┘ │
│ [+ Add] [Save Show]  │                                 │  ↑ persis frame ke Resolume  │
│                      │  ⓘ klik baris = lompat ke situ  │                              │
│                      │                                 │  NEXT ▸ "And if you don't…"  │
├──────────────────────┴─────────────────────────────────┴──────────────────────────────┤
│  MODE:  (●) Auto-timestamp   ( ) Manual per-baris          ⌨ Space ◂ ▸ B              │
│                                                                                        │
│  [◀◀ Prev Line]   [▶ Play]   [⏸ Pause]   [Next Line ▶▶]      offset  +0.30s           │
│                                                              [−0.5][−0.1][+0.1][+0.5]  │
│  00:31.42 ├────────────●──────────────────────────────────────────────┤ 04:31          │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Requirement coverage:** REQ-F-SET-02/03/05 (set list, drag, progres) ·
REQ-F-PLAY-01/02/03/04/05/06 (transport, seek, offset, blank, manual line, hotkey) ·
REQ-F-OPS-01/02 (preview + next line) · REQ-F-OUT-04 (preview scroll multi-baris)

---

## Screen 2: LIBRARY (cari online + library lokal)

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  LIVE   ▌Library▐  Show   Style   Settings                                            │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  Sumber:  (●) LRCLIB (online)   ( ) Library lokal (142 lagu)                           │
│                                                                                        │
│  ⌕ [ fleetwood mac the chain                    judul · artis · keduanya ]  [ Cari ]   │
│                                                       [ Import .lrc ]  [ + Lagu Manual ]│
├───────────────────────────────────────────────────────────────────────────────────────┤
│   JUDUL                     ARTIS               ALBUM         DURASI   LIRIK           │
│ ─────────────────────────────────────────────────────────────────────────────────────  │
│   The Chain                 Fleetwood Mac       Rumours        4:31    ● synced        │
│   The Chain                 Fleetwood Mac       Live           5:12    ○ plain saja    │
│   The Chain - Remaster      Fleetwood Mac       Rumours 2004   4:29    ● synced        │
│   Chain Of Fools            Aretha Franklin     Lady Soul      2:47    ● synced        │
│                                                                                        │
│                                                                                        │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  [ Muat ke Player ]   [ Simpan ke Library ]   [ + Tambah ke Show ]   [ Edit Lirik… ]   │
│                                                                                        │
│  ⚠ Offline - hasil pencarian LRCLIB tidak tersedia, library lokal tetap bisa dipakai.  │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Requirement coverage:** REQ-F-LIB-01/02/04/06/07 · REQ-NF-03 (offline tetap jalan)

> ⚠️ **SRS perlu direvisi:** REQ-F-LIB-01 masih berbunyi *"berdasarkan judul
> (+ artis opsional)"*. Ganti jadi: *"berdasarkan satu query bebas yang boleh
> berisi judul, artis, atau keduanya"*, memetakan ke param `q` LRCLIB.

---

## Screen 3: EDITOR LIRIK MANUAL (tap-to-timestamp)

Dipanggil dari tombol `Edit Lirik…` atau `+ Lagu Manual`.

```
┌─ Editor Lirik: "Lagu Tanpa Judul" ────────────────────────────────────────────────────┐
│  Judul [ Lagu Tanpa Judul       ]   Artis [                ]   Durasi [ 03:20 ]        │
├──────────────────────────────────────────┬────────────────────────────────────────────┤
│  TEKS MENTAH (tempel di sini)            │  BARIS TER-TIMESTAMP                       │
│ ┌──────────────────────────────────────┐ │   00:12.40   Aku berdiri di sini           │
│ │ Aku berdiri di sini                  │ │   00:16.10   Menatap langit yang sama      │
│ │ Menatap langit yang sama             │ │ ▶ 00:20.55   Tak ada yang berubah          │
│ │ Tak ada yang berubah                 │ │   ──────     Selain aku          ← next    │
│ │ Selain aku                           │ │   ──────     Selain aku                    │
│ │ …                                    │ │                                            │
│ └──────────────────────────────────────┘ │   [ Hapus timestamp baris ini ]            │
│  [ Pecah jadi baris → ]                  │   [ Geser SEMUA baris:  −1s  +1s  ]        │
├──────────────────────────────────────────┴────────────────────────────────────────────┤
│   ▶ Play  ⏸ Pause   00:20.55 ├──────●──────────────────────┤ 03:20                    │
│                                                                                        │
│              ╔═══════════════════════════════════════════════╗                         │
│              ║   [ TAP - tandai waktu baris berikutnya ]     ║   ⌨ Enter               │
│              ╚═══════════════════════════════════════════════╝                         │
│                                                    [ Batal ]  [ Simpan ke Library ]    │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Requirement coverage:** REQ-F-LIB-03 (editor manual, **Must**, belum ada sama sekali) ·
REQ-F-LIB-05 (geser semua timestamp)

---

## Screen 4: STYLE / TEMPLATE (panel paling berat secara teknis)

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  LIVE   Library   Show   ▌Style▐   Settings                                           │
├──────────────────────────────────────────┬────────────────────────────────────────────┤
│  Template [ Default White Outline  ▾ ]   │  LIVE PREVIEW (1920×1080 → scaled)         │
│           [Save] [Save As…] [Delete]     │ ┌────────────────────────────────────────┐ │
│                                          │ │▒▒▒▒ checkerboard = alpha transparan ▒▒▒│ │
│  Layout   (●) Scroll multiline           │ │▒▒                                    ▒▒│ │
│           ( ) Single line (lower third)  │ │▒▒        ·watch the sun rise·        ▒▒│ │
│                                          │ │▒▒                                    ▒▒│ │
│  Font     [ Inter Bold        ▾ ] [ … ]  │ │▒▒   RUN IN THE SHADOWS               ▒▒│ │
│  Size     ├────●──────────┤   64 px      │ │▒▒                                    ▒▒│ │
│  Warna    [██ #FFFFFF] Outline [██ #000] │ │▒▒        ·damn your love·            ▒▒│ │
│  Outline  ├──●────────────┤    3 px      │ │▒▒                                    ▒▒│ │
│                                          │ └────────────────────────────────────────┘ │
│  ── Scroll (REQ-F-OUT-05) ────────────   │                                            │
│  Baris sebelum  [ 2 ▾ ]  sesudah [ 2 ▾ ] │  [ ▶ Putar animasi transisi ]              │
│  Jarak baris    ├────●────┤  1.55×       │                                            │
│  Size falloff   ├──●──────┤  0.22        │  ⓘ Setiap perubahan slider harus terlihat  │
│  Opacity falloff├───●─────┤  0.32        │    di preview DAN di Resolume seketika     │
│  Edge fade      ├──●──────┤  0.18        │    (<100ms, REQ-NF-02)                     │
│  Transisi       ├─────●───┤  550 ms      │                                            │
│  Anchor Y       ├────●────┤  0.50        │                                            │
└──────────────────────────────────────────┴────────────────────────────────────────────┘
```

**Requirement coverage:** REQ-F-STYLE-01/02/03 · REQ-F-OUT-05 · Template §5.3

---

## Screen 5: SETTINGS

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  OUTPUT                                                                                │
│    Spout sender name  [ CUEVO Lyrics        ]        ● Terhubung, Resolume mendeteksi   │
│    Resolusi           [ 1920 ] × [ 1080 ]          Target FPS [ 30 ▾ ]                 │
│                                                                                        │
│  PENYIMPANAN                                                                           │
│    Library     [ C:\Users\…\CUEVO Lyrics\library.json        ]  [ Ubah… ]                │
│    Shows       [ C:\Users\…\CUEVO Lyrics\shows\              ]  [ Ubah… ]                │
│                                                                                        │
│  HOTKEY                          ☐ Aktifkan global hotkey (di luar window)  [C]        │
│    Play/Pause [ Space ]   Next [ → ]   Prev [ ← ]   Blank [ B ]                        │
│                                                                                        │
│  REMOTE (fase lanjut)            ☐ OSC listener  port [ 8000 ]   ☐ MIDI input          │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Requirement coverage:** REQ-F-CFG-01/02 · REQ-F-PLAY-07 · REQ-F-RC-01/02

---

## Screen 6: OPERATOR WINDOW (window kedua, monitor terpisah, opsional)

```
┌─ Operator Display, monitor 2 ────────────────────────────────────────────────────────┐
│                                                                                        │
│   NOW    RUN IN THE SHADOWS                                                            │
│                                                                                        │
│   NEXT   Damn your love                                                                │
│                                                                                        │
│   ───────────────────────────────────────────────────────────────────────────────      │
│   Lagu 3/8 · The Chain            00:31 / 04:31            ● LIVE      offset +0.30s   │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Requirement coverage:** REQ-F-OPS-01/02
