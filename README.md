# CUEVO Lyrics

Aplikasi desktop (Python + PySide6) untuk menampilkan lirik lagu secara
live ke Resolume Arena lewat **Spout**. Cari lirik di [LRCLIB](https://lrclib.net),
susun jadi Show/Set list, sesuaikan tampilannya, lalu kontrol saat acara
berjalan — semuanya dari satu window.

> Riwayat lengkap keputusan desain, bug yang ditemukan, dan hasil
> pengujiannya ada di `SRS.md` (living document). README ini cuma
> ringkasan cara pakai.

Alur data:

```
[Cari di LRCLIB / library lokal / editor manual] -> [parser LRC: baris + timestamp]
        -> [Show: susun urutan lagu]           -> [kontrol Live: Play/Pause/Next/Blank]
        -> [render scroll multi-baris + animasi, RGBA transparan]
        -> [SpoutGL sendImage] -> [Resolume Arena: Sources > Spout]
```

Sync-nya **manual**: tekan Play saat lagu mulai, koreksi dengan tombol
offset (`-0.5s`/`-0.1s`/`+0.1s`/`+0.5s`) kalau lirik terasa maju/mundur.
Ada juga **mode manual per-baris** untuk lagu tanpa tempo tetap (acapella,
rubato) — baris berpindah hanya saat kamu tekan Next/Prev, jam diabaikan.

Tampilan: mode scroll multi-baris ala Musixmatch (baris aktif menonjol,
sekitarnya mengecil/memudar, berpindah dengan animasi halus) atau mode
single-line — keduanya diatur dari panel Style, tanpa edit kode.

## Kebutuhan sistem

- **Windows** untuk fitur Spout (teknologi sharing tekstur GPU khusus
  Windows). Di OS lain aplikasi tetap bisa dibuka untuk cari/susun/edit
  lirik, hanya tombol "Mulai output" yang nonaktif.
- Python 3.9+ 64-bit.
- Resolume Arena versi apa pun yang mendukung Spout receiver.

## Instalasi

```powershell
pip install -r requirements.txt
```

Kalau instalasi `SpoutGL` gagal, biasanya versi Python 32-bit vs 64-bit
tidak cocok dengan wheel yang tersedia — pastikan pakai Python 64-bit
resmi dari python.org.

## Menjalankan

```powershell
python main.py
```

Window utama punya status strip di atas (nama sender, resolusi, fps
aktual, progres show, tombol Mulai/Stop output) dan lima tab:

### Live
Layar utama saat acara berjalan. Tiga kolom: set list lagu di kiri, baris
lirik lagu yang sedang dimuat di tengah (klik = lompat ke situ), dan
preview persis apa yang dikirim ke Resolume di kanan. Transport di bawah:
Play/Pause/Next/Prev, offset sync, **BLANK** (kill switch — mengosongkan
output tanpa mengubah posisi waktu), dan toggle mode Auto/Manual.

Hotkey: `Space` play/pause, `←`/`→` baris sebelum/berikutnya, `B` blank.

### Library
Cari lirik dari dua sumber — **LRCLIB** (online, satu kolom pencarian
bebas: judul/artis/keduanya, urutan bebas) atau **Library lokal**
(tersimpan, tetap jalan offline). Dari sini juga: impor `.lrc`, buka
editor lirik manual, simpan ke library, dan **tambah ke show** yang
sedang dibuka.

### Show
Susun Show/Set list: tambah lagu dari library, urutkan lewat drag, simpan
ke file (`.showproject.json`, satu file per show), buka show tersimpan.
Navigasi lagu saat live dilakukan dari tab Live, bukan di sini — supaya
urutan tidak tersenggol tanpa sengaja saat acara jalan.

### Style
Semua pengaturan visual: layout (scroll multiline / single line), font
(dari katalog font sistem), ukuran, warna teks & outline, jarak baris,
falloff ukuran/opacity, edge fade, kecepatan transisi, jumlah baris
konteks. Perubahan langsung tayang, termasuk saat output sedang jalan.
Simpan sebagai **Template** untuk dipakai ulang, atau pilih dari 5 preset
bawaan. **Klik kanan pada kontrol mana pun untuk kembalikan ke default**
(mengikuti kebiasaan Resolume Arena); parameter yang sudah diubah ditandai
titik di labelnya.

### Settings
Nama Spout sender, resolusi & fps output, lokasi file library/shows,
daftar hotkey. Tersimpan otomatis begitu kolom ditinggalkan.

## Menghubungkan ke Resolume Arena

1. Klik kanan pada sebuah **layer/clip** (atau slot kosong) di Resolume.
2. Pilih **Sources > Spout**.
3. Pilih sender dengan nama yang sama seperti di tab Settings (default
   `CUEVO Lyrics`).
4. Lirik muncul sebagai clip berbackground transparan — tinggal ditumpuk
   di atas visual lain sesuai kebutuhan set kamu.

## Struktur kode

```
main.py                    entry point
app.py                     QMainWindow: status strip + tabs

# inti, bebas GUI & bebas Spout (testable di OS mana pun)
lrclib_client.py           panggilan HTTP ke API LRCLIB
lrc_parser.py               parse & format LRC, cari baris aktif
player_state.py             status play/pause/posisi/offset/blank, thread-safe
render_style.py             RenderStyle -- semua parameter visual, bisa di-scaled()
scroll_anim.py               ScrollAnimator -- state machine posisi scroll
show_session.py              ShowSession -- show yang sedang dipakai saat live

# render & output
spout_output.py              MultiLineLyricRenderer + SpoutOutputThread
font_catalog.py              220-an font sistem -> path yang dijamin bisa dimuat Pillow

store/                       persistence, semua di %APPDATA%\CUEVO Lyrics\
  paths.py                     lokasi file, baca/tulis JSON atomik, migrasi nama lama
  library.py                   CRUD Song
  shows.py                     CRUD Show (satu file per show)
  templates.py                 CRUD Template + 5 preset bawaan
  settings.py                  Settings per-instalasi

ui/                           PySide6, satu file per tab
  theme.py                     design token -> QSS, helper theme.paint()
  preview.py                   widget preview -- pakai frame yang sama dgn Spout
  live_view.py / library_view.py / show_view.py / style_view.py / settings_view.py
  lyric_editor.py              editor tap-to-timestamp
```

Prinsip ketergantungan (satu arah): `ui/` -> `store/` -> inti. Modul inti
dan `store/` dilarang meng-import `PySide6` maupun `SpoutGL`.

## Data & migrasi nama

Aplikasi ini sebelumnya bernama **Lyric Spout**. Kalau kamu punya data
lama di `%APPDATA%\LyricSpout\`, folder itu otomatis dipindahkan ke
`%APPDATA%\CUEVO Lyrics\` sekali saja saat pertama kali dijalankan setelah
update ini — library dan show yang sudah tersimpan tidak hilang.

## Troubleshooting

- **"SpoutGL/pygame belum terpasang..."** — jalankan ulang
  `pip install -r requirements.txt` di Windows 64-bit.
- **Resolume tidak melihat sender-nya** — pastikan "Mulai output" sudah
  ditekan (status strip berubah jadi **ON AIR**, bukan **IDLE**), dan
  window kecil pygame yang muncul belum ditutup (boleh diminimize).
- **BLANK ditekan tapi Resolume masih menampilkan lirik** — sudah pernah
  jadi bug (lihat SRS §3.3, diperbaiki v0.6); kalau muncul lagi di versi
  yang lebih baru, laporkan.
- **Lirik tidak ketemu di LRCLIB** — coba tanpa embel-embel seperti
  "(Official Video)"; kolom pencarian menerima judul/artis dalam urutan
  bebas jadi tidak perlu dipisah.
- **Font terasa berat / fps turun saat animasi** — hindari ukuran font
  efektif di bawah ~22px (lihat peringatan otomatis di panel Style);
  ada tebing performa di Pillow/FreeType pada ukuran itu (SRS §3.2).
