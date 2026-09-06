# Software Requirements Specification (SRS)
## CUEVO Lyrics, "ProPresenter Lite" untuk Resolume Arena

> Nama produk sebelumnya: **Lyric Spout** (sampai v0.7.3). Direname jadi
> **CUEVO Lyrics** di v0.7.4, lihat changelog di bawah dan §3.8. Entri
> changelog dan log pengujian sebelum v0.7.4 sengaja **tidak** ditulis
> ulang; nama lama yang muncul di sana (termasuk transkrip pengujian
> Spout di §3.2/§3.5) adalah catatan apa yang benar-benar terjadi saat
> itu, bukan kesalahan ketik.

| | |
|---|---|
| **Versi dokumen** | 0.11.1 |
| **Status** | Living document, diperbarui seiring development di Claude Code |
| **Tanggal dibuat** | 2026-08-31 |
| **Terakhir direvisi** | 2026-09-07 (v0.11.1) |
| **Pemilik produk** | (kamu) |
| **Baseline kode saat ini** | Python, **PySide6/Qt**, LRCLIB, SpoutGL |
| **Mockup UI** | `MOCKUP.md` (wireframe teks) |

**Perubahan v0.11.1 (ringkas):**
- **Penanda bagian lagu di tab Live (REQ-F-PLAY-08).** Klik kanan baris
  lirik untuk menandainya Intro/Verse/Chorus/Bridge/dst, atau label bebas.
  Disimpan per lagu di library, ikut kalau lagu dipakai lagi (§3.18).
- Insiden saat verifikasi: skrip uji sempat menulis ke `library.json`
  pengguna sungguhan karena `settings.json` yang disalin membawa path
  absolut ke luar folder sementara. Ketahuan sendiri, langsung diperbaiki
  di data pengguna maupun di skrip ujinya (§3.18).

**Perubahan v0.11 (ringkas):**
- **Tab Donate baru (REQ-F-DON-01/02).** Saweria, QRIS, dan tautan kontak.
  Semua nilainya di satu blok konfigurasi di paling atas `ui/donate_view.py`
  supaya orang yang fork gampang menggantinya (§3.15).
- Gambar QRIS yang dipasang ternyata poster utuh, bukan kode QR-nya saja.
  Dipotong, dan hasilnya diuji dengan cara memindai ulang tangkapan layar
  aplikasi, bukan file aslinya (§3.15).
- Label kolomnya "QRIS", bukan "DANA", walaupun penerbitnya DANA. Alasannya
  di §3.15.
- **Ikon aplikasi terpasang (§3.16).** Varian squircle dipilih karena varian
  satunya tidak terbaca di 16px. `.ico` bawaan zip cuma berisi 16x16, jadi
  dibangun ulang sampai 256.
- **Persiapan rilis publik pertama (§3.17).** README ditulis ulang dalam
  bahasa Inggris, `CHANGELOG.md` dibuat, dan satu bug `.gitignore` yang
  membuat build tidak bisa diulang orang lain diperbaiki.

**Perubahan v0.10 (ringkas):**
- **REQ-F-OUT-09 baru: jendela Cast.** Satu jendela yang bisa ditangkap OBS,
  TikTok Live Studio, atau di-fullscreen di layar kedua. Ketiga permintaan
  itu ternyata satu fitur yang sama (§3.14).
- Ditemukan lewat pengukuran: **baris konteks yang memudar pakai alpha tidak
  selamat melewati chroma key.** 57 dari 76 baris berteks tercemar warna
  latar. Aplikasi sekarang mendeteksi dan menawarkan perbaikannya (§3.14).
- Biaya render tambahan nol: jendela Cast memakai sumber frame yang sama
  dengan Operator Display.

**Perubahan v0.9.3 (ringkas):**
- §3.13 baru: **daftar utang verifikasi** yang dikumpulkan jadi satu tempat.
  Sebelumnya tersebar di berbagai bagian dan mudah terlewat.
- Status REQ-F-RC-01/02 dipertegas: yang sudah terbukti adalah jalur
  perangkat lunaknya, **bukan** dengan controller fisik atau software lain.
  Pemilik produk menyatakan ini tidak mendesak.

**Perubahan v0.9.2 (ringkas):**
- Tab Settings dirancang ulang jadi "modul rak" dua kolom dengan lencana
  keadaan (§3.12). Mockup dan audit lengkap di `MOCKUP_SETTINGS.html`.
- Seluruh radio dan checkbox diganti `SegmentedControl` (§3.12).
  Penyebab akarnya: `::indicator` tidak pernah digaya sama sekali, sehingga
  yang tampil selama ini adalah kontrol native Windows.
- Mockup: `MOCKUP_TOGGLES.html`.

**Perubahan v0.9.1 (ringkas):**
- Font UI tidak lagi dipatok ke "Segoe UI"/"Consolas", kini diambil dari
  sistem lewat `theme.init_fonts()` (§3.11).
- Dua teks terpotong ditemukan lewat pemeriksaan lebar-teks-vs-widget dan
  diperbaiki; sekarang 0 label terpotong di kelima tab.

**Perubahan v0.9 (ringkas):**
- **Fase 5 sebagian:** trigger **OSC** (tanpa dependency baru, parser
  ditulis sendiri) dan **MIDI** (`python-rtmidi`, opsional), keduanya
  memakai daftar aksi yang sama.
- Tiga bug gagal-diam ditemukan & diperbaiki saat pengujian: `SO_REUSEADDR`
  menyembunyikan bentrokan port, filter tombol-dilepas memakan nilai 0.0
  yang sah, dan Note On velocity 0 memicu aksi dua kali (§3.10).
- **NDI dan multi-sender sengaja TIDAK dibangun**, evaluasi beserta
  alasannya di §3.10. Keduanya prioritas Could dan belum berbayar.

**Perubahan v0.8 (ringkas):**
- **Fase 4 selesai:** Operator Display (window kedua, NOW/NEXT ukuran
  besar, pemilih monitor, fullscreen) dan hotkey global system-wide.
- `PreviewWidget.set_mirror()` baru, Operator Display menyalin frame dari
  preview tab Live, bukan merender sendiri (§3.9).
- Hotkey global sengaja memakai Ctrl+Alt+..., BUKAN Space/B polos, alasannya di §3.9, dan itu bukan pilihan gaya.

**Perubahan v0.7.4 (ringkas):**
- **Rebranding: "Lyric Spout" → "CUEVO Lyrics"** (permintaan pemilik
  produk, murni penamaan). Judul window, applicationName, User-Agent
  LRCLIB, default sender name, dan folder data semuanya diganti.
- Folder data lama `%APPDATA%\LyricSpout\`, yang ternyata **sudah
  berisi data asli** (11 lagu), bukan hasil pengujian, dipindahkan
  otomatis ke nama baru sekali saat startup lewat `migrate_legacy_data()`.
- **Bug kedua ditemukan saat verifikasi migrasi pada data asli itu sendiri:**
  `library_path`/`shows_path` di `settings.json` adalah path absolut yang
  tidak ikut diperbarui setelah rename, sehingga aplikasi diam-diam
  terbuka dengan library kosong walau filenya utuh. Diperbaiki dengan
  `_rewrite_stored_paths()`, dibuat self-healing, dan data asli operator
  sudah dipulihkan di mesin ini. Detail lengkap di §3.8.
- README ditulis ulang total: versi sebelumnya masih mendeskripsikan
  v0.1 (Tkinter, 3 panel, kolom judul/artis terpisah) padahal sudah
  6 fase berlalu sejak itu.

**Perubahan v0.7.3 (ringkas):**
- **Bug tampilan sistemik diperbaiki:** stylesheet container ikut mengecat
  seluruh widget di dalamnya, membuat tombol Play tidak terlihat sama sekali
  meski tetap bisa diklik. 48 container di-scope ulang (§3.7).

**Perubahan v0.7.2 (ringkas):**
- REQ-F-STYLE-05 baru: **klik kanan pada kontrol = kembali ke default**,
  mengikuti kebiasaan Resolume Arena. Plus penanda titik pada parameter
  yang berbeda dari default, dan tombol "Reset semua".

**Perubahan v0.7.1 (ringkas):**
- **BLANK dikonfirmasi visual di Resolume oleh operator**, catatan
  "belum terverifikasi" di §3.3 ditutup.
- **Perbaikan kelalaian:** tombol "Tambah ke show" di tab Library masih
  mati sejak Fase 1 dengan tooltip basi, padahal Fase 2 sudah selesai.
  Lihat §3.6, dan pelajaran prosesnya.

**Perubahan v0.7 (ringkas):**
- **Fase 3 selesai:** panel Style penuh, font, ukuran, warna, outline,
  seluruh parameter scroll, plus Template & 5 preset bawaan.
- **Dua pengaturan ternyata tidak berpengaruh apa pun** dan diperbaiki
  sebelum panelnya dibangun: baris konteks dan `layout=single_line` (§3.4).
- Style bisa diganti tanpa menghentikan output; terukur 18-40 ms (§3.5).
- `font_catalog.py` baru: 220 font sistem dipetakan ke path yang dijamin
  bisa dimuat Pillow, bukan sekadar nama keluarga dari Qt.
- §3.5 mencatat pengukuran yang **salah menyimpulkan** untuk kedua kalinya.

**Perubahan v0.6 (ringkas):**
- **Fase 2 selesai:** Show/Set list (buat, urutkan via drag, simpan/buka),
  navigasi lagu dari tab Live, progres show di status strip.
- **Bug serius diperbaiki:** BLANK tidak pernah sampai ke output Spout, preview gelap tapi Resolume tetap menampilkan lirik (§3.3).
- Mode manual per-baris (REQ-F-PLAY-05) diimplementasikan.
- Modul baru: `store/shows.py`, `show_session.py`, `ui/show_view.py`.
- §3.3 mencatat pengujian yang **salah menyimpulkan** karena harness
  menempel ke sender Resolume, beserta apa yang karenanya belum terbukti.

**Perubahan v0.5 (ringkas):**
- **Output Spout terverifikasi di Windows 11** dengan Resolume aktif, ini
  menutup blocker terbesar yang menggantung sejak v0.2 (§3.2).
- Dua bug performa ditemukan & diperbaiki: outline brute-force (137 ms →
  9,3 ms) dan preview yang justru lebih mahal karena kanvas kecil (§3.2).
- Preview kini memakai `latest_frame` dari thread Spout saat live, REQ-F-OUT-08
  terpenuhi secara struktural, bukan lagi lewat kemiripan.
- **ADR-001 ditinjau: pemicu pindah ke C# TIDAK terpenuhi.** PySide6 tetap.
- Batasan baru: tebing performa font <20px, berdampak ke panel Style (§10).

**Perubahan v0.4 (ringkas):**
- **Fase 1 selesai & terverifikasi:** library lokal, impor `.lrc`, editor
  lirik manual tap-to-timestamp, geser massal timestamp, pencarian lokal,
  dan Settings tersimpan antar sesi (§3, §11).
- Lokasi data pindah ke `%APPDATA%\LyricSpout\`; penulisan JSON dibuat
  **atomik** supaya library tidak rusak kalau aplikasi mati saat menyimpan.
- `lrc_parser.format_lrc()` baru, lirik hasil ketik manual bisa diekspor
  balik ke `.lrc`, jadi tidak terkunci di `library.json` saja.
- Requirement baru REQ-F-LIB-08 (konfirmasi sebelum menimpa lirik yang
  sudah diedit), lihat §4.1.

**Perubahan v0.3 (ringkas):**
- §4.1 REQ-F-LIB-01 direvisi: pencarian **satu kolom query bebas**, bukan
  judul + artis terpisah (§4.1).
- §2.4 & §8: keputusan stack UI, **Tkinter → PySide6**, Tauri ditolak,
  C# jadi cadangan. Rasional lengkap di §13 (ADR-001).
- §3: status REQ-F-OUT-02/03 dikoreksi dari "selesai" jadi **cacat**, ditemukan bug yang mematikan animasi transisi dan cache frame (§3.1).
- Requirement baru REQ-F-OUT-08: preview dan Spout wajib satu jalur render.
- §13 baru: log keputusan arsitektur (ADR).

---

## 1. Pendahuluan

### 1.1 Tujuan Dokumen
Dokumen ini mendefinisikan kebutuhan fungsional dan non-fungsional untuk
**CUEVO Lyrics**, aplikasi desktop Windows yang menampilkan lirik lagu
secara live ke Resolume Arena (lewat Spout), dengan visi jangka panjang
menjadi versi ringan ("lite") dari software presentasi ibadah/live-event
sekelas **ProPresenter**, tapi difokuskan pada satu kasus penggunaan:
**presentasi lirik lagu untuk visual live/VJ setup**, bukan pengganti
penuh ProPresenter.

Dokumen ini ditulis supaya bisa langsung dipakai sebagai acuan kerja di
Claude Code, setiap fitur punya ID requirement, prioritas, dan kriteria
penerimaan yang bisa diturunkan jadi task/issue.

### 1.2 Ruang Lingkup Produk
**Termasuk dalam scope:**
- Pencarian & pengambilan lirik bersinkron waktu dari LRCLIB.
- Penulisan/impor lirik manual (untuk lagu yang tidak ada di LRCLIB).
- Manajemen library lagu & playlist/set list sederhana.
- Kontrol live (play/pause/next/previous/blank) dengan sinkronisasi manual.
- Rendering teks lirik sebagai layer transparan.
- Output ke Resolume Arena lewat Spout (Windows).
- Styling dasar (font, warna, posisi, outline/shadow, background).
- Penyimpanan project/show ke file lokal supaya bisa dibuka lagi.

**Di luar scope (untuk versi ini):**
- Modul non-lirik ala ProPresenter: Bible module, Announcements,
  Countdown/Clock canggih, Props, Camera input, Media playback penuh
  (video/audio player).
- Multi-user/collaborative editing, cloud sync, akun/login.
- Dukungan macOS/Linux untuk output Spout (Spout = Windows-only).
  NDI sebagai alternatif cross-platform dicatat sebagai *future option*
  (lihat §9).
- Mengkloning secara harfiah UI, file format, atau kode ProPresenter.

### 1.3 Catatan Legal & Etis (penting)
"Reverse engineering ProPresenter" di proyek ini dimaknai sebagai:
> Mempelajari **konsep dan fitur yang terlihat sebagai pengguna**
> (workflow live lyrics, playlist, stage display, dsb.) lalu
> mengimplementasikan ulang dari nol dengan arsitektur sendiri, > **bukan** mendekompilasi binary ProPresenter, membongkar protokol
> jaringan berlisensi mereka, atau mengambil aset/kode mereka.

Implikasi praktis untuk development:
- Jangan gunakan nama, logo, atau branding ProPresenter pada produk ini.
- Jangan mengimpor/mem-parsing format file `.pro6`/`.pro`/dsb. milik
  Renewed Vision tanpa spesifikasi resmi yang dipublikasikan mereka.
- Referensi fitur cukup dari dokumentasi publik/manual pengguna
  ProPresenter, bukan dari source code atau binary mereka.
- Kalau nanti mau interoperasi (mis. baca file `.pro`), itu jadi item
  riset legal tersendiri, di luar scope dokumen ini.

### 1.4 Definisi & Istilah
| Istilah | Arti |
|---|---|
| **Spout** | Teknologi Windows untuk berbagi tekstur GPU antar aplikasi (video real-time). |
| **NDI** | Network Device Interface, alternatif Spout yang jalan lintas platform lewat jaringan. |
| **LRC** | Format teks lirik dengan timestamp per baris, mis. `[00:17.12] baris lirik`. |
| **LRCLIB** | Layanan API publik penyedia lirik synced/plain, gratis tanpa API key. |
| **Show / Set list** | Kumpulan lagu yang diurutkan untuk satu sesi tampil. |
| **Slide** | Satu unit tampilan (di produk ini: satu baris/bait lirik). |
| **Operator view / Stage display** | Tampilan kontrol terpisah untuk operator (bukan yang disiarkan ke penonton). |
| **Cue** | Satu aksi trigger (next slide, blank, ganti lagu) yang bisa dipicu manual/remote. |

### 1.5 Referensi
- LRCLIB API, https://lrclib.net
- SpoutGL (Python), https://github.com/jlai/Python-SpoutGL
- Resolume Arena, dokumentasi resmi Resolume (Sources > Spout)
- Baseline kode: `README.md` di root repo ini (v0.1)

---

## 2. Deskripsi Umum

### 2.1 Perspektif Produk
Aplikasi berdiri sendiri (bukan plugin Resolume), berkomunikasi dengan
Resolume secara satu arah lewat Spout sebagai "virtual video source".
Tidak ada dependency ke internal Resolume selain protokol Spout itu
sendiri.

```
+------------------+     HTTP      +-----------+
|  CUEVO Lyrics App| <-----------> |  LRCLIB   |
|  (Windows)       |               +-----------+
|                  |
|  [GUI] [Engine]  |     Spout     +-----------------+
|  [Renderer] ------------------->| Resolume Arena    |
+------------------+   (GPU tex)  +-----------------+
```

### 2.2 Fungsi Utama Produk (ringkas)
1. Cari & muat lirik (online via LRCLIB, atau input manual/impor `.lrc`).
2. Susun playlist/set list dari lagu-lagu yang sudah dimuat.
3. Kontrol tampilan live: play/pause/next/prev/blank, koreksi sync.
4. Render & kirim frame ke Resolume lewat Spout secara kontinu.
5. Simpan & buka kembali project (show file lokal).
6. (Fase lanjut) Kontrol jarak jauh via keyboard shortcut / MIDI / OSC.

### 2.3 Kelas Pengguna
| Kelas | Kebutuhan utama |
|---|---|
| **Operator solo** (kasus utama) | Cepat cari lagu, tampil, koreksi sync sambil live, tanpa training rumit. |
| **VJ / visual artist** | Kontrol tampilan lirik menyatu dengan komposisi visual lain di Resolume. |
| **Tim ibadah/event kecil** | Siapkan set list sebelumnya, tinggal jalan pas hari-H. |

### 2.4 Lingkungan Operasi
- **OS:** Windows 10/11 64-bit (wajib untuk fitur Spout).
- **Runtime:** Python 3.9+ dengan **PySide6 (Qt 6)** untuk GUI.
  Keputusan stack sudah diambil di v0.3, lihat §13 ADR-001.
  Tkinter ditinggalkan; Tauri ditolak; C# jadi jalur cadangan yang
  dipicu hanya oleh kondisi terukur (§13).
- **Target:** Resolume Arena versi apa pun yang mendukung Spout receiver.
- **Koneksi internet:** dibutuhkan untuk pencarian LRCLIB; fitur lirik
  manual/lokal harus tetap berfungsi offline.

### 2.5 Batasan Desain & Implementasi
- Spout = Windows-only → arsitektur output harus terisolasi di satu
  modul (`spout_output.py`) supaya bagian lain (pencarian, parsing,
  playlist, UI) tetap testable di OS non-Windows.
- LRCLIB API publik, tanpa API key, **tidak ada rate limit resmi
  didokumentasikan**, tapi tetap kirim `User-Agent` yang jelas dan
  jangan polling berlebihan (hormati fair-use layanan gratis).
- Font rendering bergantung pada font TTF yang tersedia di sistem
  (fallback ke font bawaan Pillow kalau tidak ketemu, kualitas rendah,
  harus diperbaiki di fase styling).

### 2.6 Asumsi & Dependensi
- Audio/musik diputar oleh aplikasi/perangkat lain (Spotify, DJ set,
  live band, dsb.), aplikasi ini **tidak** memutar audio, hanya
  menyinkronkan teks secara manual terhadap waktu berjalan.
- Resolume Arena berjalan di komputer yang sama (Spout adalah
  local-machine texture sharing, bukan jaringan).

---

## 3. Baseline Implementasi Saat Ini (v0.1)

Sudah diimplementasikan dan berjalan (dasar untuk lanjutan development):

| Modul | Fungsi | Status |
|---|---|---|
| `lrclib_client.py` | `search()`, `get_by_id()`, `get_exact()` ke LRCLIB API | ✅ Selesai |
| `lrc_parser.py` | `parse_lrc()`, `find_current_line()` (binary search) | ✅ Selesai + teruji |
| `player_state.py` | State play/pause/seek/offset, thread-safe | ✅ Selesai + teruji |
| `store/paths.py` | Lokasi `%APPDATA%\CUEVO Lyrics\`, baca/tulis JSON **atomik**, migrasi dari folder nama lama `LyricSpout\` (§3.8) | ✅ Baru (v0.4), direname v0.7.4 |
| `store/library.py` | `Song` + `Library`, CRUD, pencarian lokal, anti-duplikat, geser timestamp | ✅ Baru (v0.4) + teruji |
| `store/settings.py` | `Settings`, persist antar sesi, clamp nilai tidak wajar | ✅ Baru (v0.4) + teruji |
| `ui/lyric_editor.py` | Screen 03, tap-to-timestamp, geser massal, ekspor `.lrc` | ✅ Baru (v0.4) |
| `ui/settings_view.py` | Screen 05, sender, resolusi, fps, lokasi file | ✅ Baru (v0.4) |
| `render_style.py` | `RenderStyle`, semua parameter visual dalam satu objek, bisa di-`scaled()` untuk preview | ✅ Baru (v0.3) |
| `scroll_anim.py` | `ScrollAnimator`, state machine posisi scroll + easing, dipakai bersama Spout & preview | ✅ Baru (v0.3) |
| `spout_output.py` | Render lirik ke RGBA transparan (Pillow) + kirim via SpoutGL | ⚠️ Mode scroll multi-baris (`MultiLineLyricRenderer`) ada, tapi **animasi & cache frame cacat**, lihat §3.1. **Belum pernah teruji di Windows nyata.** |
| `app.py` + `ui/` | GUI **PySide6**: status strip, tabs, live view, library view, preview | 🔄 Port dari Tkinter (v0.3) |

> **Perubahan v0.2 (lihat §4.4):** mode tampilan output diubah dari
> "satu baris polos" menjadi **scroll multi-baris ala Musixmatch**, > baris aktif ditonjolkan, baris sekitarnya mengecil/memudar, dan
> perpindahan antar baris dianimasikan halus. Ini menggantikan asumsi
> "single-line" pada draf SRS sebelumnya (REQ-F-OUT-03/04 kini **Must**,
> bukan lagi **Should**).

### 3.1 Bug ditemukan saat review v0.3, REQ-F-OUT-02/03 tidak benar-benar selesai

`SpoutOutputThread.run()` memakai `id(lines)` untuk mendeteksi "lagu baru
dimuat". Tapi `PlayerState.get_lines()` mengembalikan **list salinan baru
setiap pemanggilan** (`return list(self._lines)`), jadi `id()`-nya berubah
hampir tiap frame. Akibatnya, tiap frame:

- `displayed_pos` di-*snap* ke `active_index` → **animasi transisi tidak
  pernah berjalan** (REQ-F-OUT-03 gagal, walau ditandai "selesai" di v0.2);
- `force_redraw` selalu `True` → **frame digambar ulang terus-menerus**
  walau tidak ada yang berubah (REQ-F-OUT-02 gagal, ini justru kebalikan
  dari tujuan requirement-nya).

**Perbaikan (v0.3):** `PlayerState` menyimpan counter `_lines_version` yang
naik tiap `load_lyrics()`, diekspos lewat `get_lines_version()`. Deteksi
lagu baru memakai counter itu, bukan identitas objek.

> **Pelajaran untuk dokumen ini:** status "✅ selesai" hanya boleh ditulis
> setelah diverifikasi berjalan, bukan setelah kode ditulis. Status
> yang benar untuk kode yang belum dijalankan adalah **"implemented,
> unverified"**. Lihat juga §10 (risiko baru).

### 3.2 Verifikasi Spout & performa (v0.5), dijalankan di Windows 11

**Output Spout: LULUS.** Diuji dengan proses penerima terpisah yang berlaku
seperti Resolume (Resolume sendiri terdeteksi aktif di daftar sender:
`['Arena - Composition', 'LyricSpout']`).

| Yang diuji | Hasil |
|---|---|
| Sender terdaftar & bisa disambungi aplikasi lain | ✅ `LyricSpout` 1920×1080 |
| Piksel yang diterima benar | ✅ teks ter-render, alpha transparan, bbox sesuai |
| Scroll multi-baris (REQ-F-OUT-04) | ✅ baris aktif di tengah, sekitarnya mengecil & memudar |
| Animasi transisi (REQ-F-OUT-03) | ✅ posisi bergerak bertahap, bukan lompat |
| Cache frame saat diam (REQ-F-OUT-02) | ✅ 60 frame tanpa perubahan → 0 render |
| Thread berhenti bersih (REQ-NF-04) | ✅ |

**Dua bug performa ditemukan dan diperbaiki.** Keduanya tidak terlihat dari
angka fps di status strip, karena cache frame menyembunyikannya:

**(a) Outline digambar brute-force.** `render()` menggambar ulang teks di
setiap offset dalam kotak `(2*ow+1)²`, untuk `ow=3` itu **48 kali draw per
baris**, sekitar 290 draw per frame. Diganti dengan `stroke_width` bawaan
Pillow yang melakukan hal sama dalam satu lintasan:

| | ms/frame | maks fps |
|---|---|---|
| Brute-force (lama) | 137,3 | 7,3 |
| `stroke_width` (baru) | **9,3** | **107,3** |

Beda hasil hanya 0,8% piksel di tepi outline, dan justru lebih benar,
karena sudutnya membulat rapi, bukan kotak.

**(b) Preview dirender terpisah di kanvas kecil.** Ternyata **memperkecil
kanvas membuatnya lebih mahal**, bukan lebih murah. Penyebabnya tebing
performa di Pillow/FreeType sekitar 20px:

| Ukuran font | ms per 100 draw |
|---|---|
| 12 px | 815 |
| 16 px | 815 |
| **21 px** | **225** ← tebing |
| 64 px | 341 |

Preview 480×270 menghasilkan font 16px dan 12px, dua-duanya di sisi lambat,
sehingga preview (61 ms) lebih berat daripada output 1920×1080 (26 ms).

Perbaikannya bukan menyetel ukuran, melainkan **menghapus render gandanya**:
`SpoutOutputThread` sekarang menyimpan `latest_frame`, dan saat output jalan
preview memakai buffer itu langsung tanpa merender apa pun. Efek sampingnya
justru memperkuat REQ-F-OUT-08, preview dan output kini benar-benar buffer
yang sama, bukan dua hasil yang kebetulan mirip. Saat output mati, preview
merender sendiri di skala yang menjaga font terkecil tetap di atas ~22px.

**Hasil akhir (median, mesin uji Windows 11 / Python 3.13):**

```
Output 1920x1080  : 26.0 ms/frame  -> 38.5 fps   (budget 33.3 ms untuk 30 fps)
Preview mandiri   : 28.4 ms/frame  -> 35.2 fps
Preview saat live : 0 ms  (pakai frame kiriman)

Uji Spout kondisi terburuk (baris berganti tiap 0.6s, animasi nyaris
tanpa henti sehingga cache frame tidak pernah menolong):
    fps  min=29.6  rata2=29.7  maks=29.7   -> REQ-NF-01 LULUS
```

**Konsekuensi untuk ADR-001:** pemicu pindah ke C# adalah "Pillow terbukti
tidak sanggup 30 fps". Sesudah perbaikan, **pemicu itu tidak terpenuhi**, PySide6 + Pillow tetap dipakai. Tapi headroom-nya hanya sekitar 22%
(26 ms dari 33,3 ms), jadi angka ini wajib diukur ulang tiap kali renderer
disentuh.

### 3.3 BLANK tidak pernah sampai ke output (ditemukan v0.6)

Tombol BLANK sudah ada sejak v0.3 dan **terlihat** bekerja: preview gelap,
label strip berubah jadi `BLANK`. Tapi kata "blank" tidak pernah muncul
sekali pun di `spout_output.py`, dan sinyal `blankToggled` di-`emit` tanpa
pernah di-`connect`.

Akibatnya di lapangan: **operator menekan BLANK, melihat preview kosong,
dan mengira penonton tidak melihat apa-apa, sementara Resolume tetap
menampilkan lirik.** Ini mode gagal yang paling mahal dari semua yang
ditemukan sejauh ini, karena memberi rasa aman yang keliru.

**Penyebab akarnya sama dengan §3.1 dan §3.2:** keadaan yang dipakai
bersama disimpan di salah satu pemakainya, bukan di tempat bersama.
`_blank` hidup di widget preview, jadi thread Spout tidak mungkin tahu.

**Perbaikan:** `blank` pindah ke `PlayerState`, sejajar dengan posisi waktu
dan offset, satu-satunya sumber kebenaran yang dibaca thread Spout maupun
preview. Thread Spout juga wajib memicu gambar ulang saat blank berubah,
karena kalau tidak, cache frame (REQ-F-OUT-02) akan terus mengirim frame
lama yang masih berisi lirik.

**Verifikasi:** diukur pada `latest_frame`, yaitu buffer yang benar-benar
dikirim ke Spout, piksel tampak `31765 → 0 → 0 → 36487` (sebelum, saat,
selama, sesudah blank). ✅

> ⚠️ **Catatan kejujuran pengujian.** Percobaan memverifikasi ini lewat
> proses penerima Spout terpisah **gagal memberi hasil yang sah** dan
> sempat salah menyimpulkan "GAGAL". Penyebabnya di harness, bukan produk:
> `SpoutReceiver.setReceiverName()` tidak menggigit, penerima menempel ke
> `Arena - Composition` (Resolume) yang kebetulan juga 1920×1080, sehingga
> yang terukur adalah piksel Resolume, konstan apa pun yang dilakukan.
> Diagnosis: `getActiveSender()` = `Arena - Composition`,
> `getSenderName()` mengembalikan `'1920'` (sampah),
> `isFrameCountEnabled()` = `False` sehingga `isFrameNew()` tak bermakna.
>
> **Ditutup di v0.7.1:** operator sudah mengonfirmasi secara visual di
> Resolume bahwa BLANK benar-benar mengosongkan tampilan. REQ-F-PLAY-04
> kini terverifikasi end-to-end. Catatan soal harness tetap disimpan
> karena kelemahannya masih berlaku untuk pengujian berikutnya.

### 3.4 Dua pengaturan yang tidak berpengaruh apa pun (ditemukan v0.7)

Sebelum membangun panel Style, tiap kontrol yang akan dibuat diuji dulu:
apakah mengubahnya benar-benar mengubah frame? Dua di antaranya **tidak**.

| Pengaturan | Perilaku sebelum diperbaiki |
|---|---|
| `context_before` / `context_after` | context 0, 1, 2, 4 → **sama-sama 5 baris** |
| `layout = "single_line"` | tetap 5 baris; nilainya tidak pernah dibaca renderer |

Penyebabnya: `context_*` hanya melebarkan *jendela pindai*, sedangkan yang
benar-benar menentukan sebuah baris tampil atau tidak cuma `opacity_falloff`.
Dan `layout` disimpan di `RenderStyle` tapi `build_renderer()` tidak pernah
meneruskannya.

Kalau panel Style dibangun tanpa pengecekan ini, akan ada **dua kontrol lagi
yang tampak bekerja padahal tidak**, pola yang sama persis dengan bug BLANK
(§3.3), dua kali sekaligus.

**Perbaikan:** `_context_factor()` menjadikan batas konteks nyata, meredup
bertahap sampai nol di jarak (batas + 1) sehingga baris tidak muncul/hilang
mendadak saat animasi. `single_line` diwujudkan sebagai "nol baris konteks"
lewat jalur render yang sama, bukan jalur terpisah, satu jalur render,
satu tempat untuk salah.

Sesudah: context 0/1/2 → 1/3/5 baris; `single_line` → 1 baris; asimetris
(0 sebelum, 2 sesudah) → 3 baris; selama animasi transisi jumlahnya bergerak
3→4→3, bukan melompat.

**Sisa jebakan yang tidak dihilangkan, tapi ditampilkan.** Jumlah baris
dibatasi *dua* hal sekaligus, batas konteks dan `opacity_falloff`, dan
yang lebih ketat menang. Menaikkan baris konteks di atas yang diizinkan
falloff terasa tidak berefek. Ini perilaku yang benar, jadi bukan
dihilangkan melainkan dijelaskan: panel Style menampilkan "efektif 1+1"
dan menerangkan penyebabnya.

### 3.5 Ganti style tanpa menghentikan output

`SpoutOutputThread` menerima `set_style()` dari thread GUI lewat satu atribut
`_pending_style` (penugasan atribut atomik di bawah GIL, tidak ada frame
yang separuh style lama separuh baru). Renderer baru dibangun **sebelum**
ditukar, jadi style yang gagal dimuat tidak mematikan output di tengah acara.

Lebar/tinggi sengaja tidak ikut berubah: mengganti ukuran sender saat siaran
memaksa receiver Resolume menyambung ulang dan itu terlihat sebagai kedipan.
Resolusi hanya bisa diubah dari tab Settings.

**Verifikasi (diukur pada `latest_frame`, deteksi perubahan lewat cuplikan
~500 byte):**

```
context 0+0  : 18.4 ms      font 110px  : 39.7 ms
warna merah  : 36.5 ms      single_line : 31.7 ms
fps sebelum 29.6  ->  fps sesudah 29.7      REQ-NF-02 LULUS
```

> ⚠️ **Catatan kejujuran pengujian (kedua kalinya).** Pengukuran pertama
> memberi 128-171 ms dan menyimpulkan "GAGAL". Salah: fungsi pemeriksanya
> memindai 2 juta piksel per panggilan di Python, jadi yang terukur sebagian
> besar adalah biaya alat ukurnya sendiri. Sama kelasnya dengan kekeliruan
> harness di §3.3. **Setiap pengukuran latency wajib memakai detektor yang
> jauh lebih murah daripada hal yang diukur.**

### 3.6 Fitur selesai yang pintu masuknya tertinggal mati (v0.7.1)

Tombol **"Tambah ke show"** di tab Library dibuat nonaktif pada Fase 1
dengan tooltip *"Fase 2, REQ-F-SET-01 belum diimplementasikan"*. Fase 2
selesai, `ShowSession.add_song()` berfungsi, tab Show bisa menambah lagu, tapi tombol di Library tidak pernah dinyalakan. Ditemukan oleh operator,
bukan oleh pengujian.

**Kenapa lolos:** pengujian Fase 2 memverifikasi *kemampuannya*
(`add_song`, urutan, simpan, buka) lewat pemanggilan langsung, bukan lewat
**setiap pintu masuk di UI**. Requirement ditandai selesai berdasarkan
fungsi yang jalan, padahal salah satu jalur pengguna menuju fungsi itu
masih terkunci.

**Aturan tambahan untuk fase berikutnya:** setiap kali sebuah fase
diselesaikan, cari semua `setEnabled(False)` dan tooltip yang menyebut fase
itu, lalu pastikan tidak ada yang tertinggal. Kontrol yang mati harus
menyebut fase yang **benar-benar belum dikerjakan**, dan sebutan itu ikut
kedaluwarsa saat fasenya selesai.

Sekalian diperbaiki: catatan *"dipakai mulai Fase 2"* pada path Shows di tab
Settings, yang juga sudah tidak benar.

**Detail perbaikan:** lagu dari hasil pencarian LRCLIB otomatis disimpan ke
library dulu sebelum masuk show. Show menyimpan **id** lagu, bukan salinan
liriknya, tanpa langkah itu, id-nya hanya hidup di memori dan show yang
disimpan akan menunjuk lagu yang tidak ada saat dibuka besok.

### 3.7 Stylesheet container mengecat anak-anaknya (v0.7.3)

Dilaporkan operator: **tombol Play di tab Live tidak terlihat, tapi tetap
bisa diklik.**

Penyebabnya perilaku Qt yang mudah terlewat: `widget.setStyleSheet("background:#111")`
**tanpa selector** berlaku untuk widget itu *dan seluruh keturunannya*, serta
mengalahkan stylesheet aplikasi. Panel transport memakai
`panel.setStyleSheet(f"background:{V1}")`, sehingga setiap tombol di dalamnya
dipaksa berlatar `#0e0e0f`. Tombol Play memakai latar terang dengan teks
gelap `#0b0b0c`, begitu latarnya ditimpa jadi gelap, teks gelap di atas
latar gelap = tidak terlihat, tapi widget-nya tetap ada dan tetap menerima
klik.

Gejalanya cocok persis: BLANK tetap terlihat karena yang menandainya
**border** merah, bukan latar, dan border tidak ikut ditimpa.

**Ini bukan satu tombol, tapi 48 tempat.** Pola yang sama dipakai di seluruh
UI sejak v0.3. Yang lain kebetulan tidak separah itu karena teksnya terang,
jadi hanya "tombol kehilangan bentuknya", tetap terbaca, jadi tidak
dilaporkan.

**Perbaikan:** `theme.paint(widget, css)` memberi objectName unik lalu
menulis aturannya sebagai `#nama { ... }`, sehingga berhenti di widget itu
sendiri. Seluruh 48 pemanggilan diganti.

**Verifikasi (piksel, bukan kesan):** latar tombol Play `232,233,235`
(terang, sesuai spesifikasi), Pause dan "Mulai output" `35,36,39`.

> **Pelajaran, dan ini yang ketiga kalinya berpola sama** (§3.1 identitas
> objek, §3.3 keadaan bersama di tempat yang salah, sekarang cakupan CSS):
> **default sebuah mekanisme yang "berlaku lebih luas dari yang diduga"
> adalah sumber bug yang tidak terlihat.** Selalu batasi cakupan secara
> eksplisit, jangan mengandalkan tebakan tentang sejauh mana sesuatu
> merambat.
>
> Bug ini juga lolos dari semua pengujian otomatis, karena semuanya menguji
> *perilaku*, bukan *tampilan*. Pengujian berikutnya untuk hal visual perlu
> memeriksa piksel, seperti yang akhirnya dipakai untuk memverifikasi
> perbaikan ini.

### 3.8 Rebranding: Lyric Spout → CUEVO Lyrics (v0.7.4)

Nama produk diganti dari "Lyric Spout" jadi "CUEVO Lyrics" atas permintaan
pemilik produk. Ini murni penamaan, tidak ada perubahan fungsi.

**Yang diubah:** judul window (`setWindowTitle`), `QApplication.setApplicationName`,
default `spout_sender_name` di `store/settings.py`, docstring modul,
`User-Agent` yang dikirim ke LRCLIB, dan nama folder data.

**Risiko yang ditangani, data pengguna nyata sudah ada.** Sebelum
mengganti nama folder `%APPDATA%\LyricSpout\`, ditemukan folder itu **sudah
berisi data asli** (bukan hasil pengujian), 3 lagu tersimpan termasuk
"Siti Nurbaya" oleh Ria Amelia, `settings.json` terisi, dan folder `shows/`.
Kalau nama folder diganti begitu saja di kode, siapa pun yang sudah pernah
memakai aplikasi ini akan kehilangan seluruh library dan show-nya secara
diam-diam saat update.

**Perbaikan:** `store/paths.migrate_legacy_data()` dipanggil paling awal di
`MainWindow.__init__`, sebelum `Settings.load()` atau `Library(...)`
dibuat. Kalau folder baru (`CUEVO Lyrics`) belum ada tapi folder lama
(`LyricSpout`) ada, folder lama di-*rename* (bukan disalin lalu dihapus)
ke nama baru, operasi atomik di filesystem yang sama, jadi tidak ada
jendela waktu di mana data terlihat hilang. Kalau migrasi gagal (mis. file
sedang dipakai proses lain), aplikasi tetap dibuka dengan data kosong dan
folder lama dibiarkan utuh untuk dipindahkan manual, kegagalan migrasi
tidak boleh menghalangi aplikasi dibuka (semangat yang sama dengan
REQ-NF-03).

**Yang sengaja TIDAK diubah:** isi `settings.json` yang sudah tersimpan
(nilai `spout_sender_name` milik instalasi yang sudah ada tetap dipakai
apa adanya, default baru hanya berlaku untuk instalasi baru atau field
yang kosong). Kalau operator sudah mengarahkan clip di Resolume ke sender
lama, itu tetap jalan sampai operator sendiri yang mengubahnya di tab
Settings.

**Bug kedua, ditemukan saat memverifikasi migrasi pada data asli, ini
yang keempat kalinya berpola sama** (id() §3.1, keadaan bersama §3.3,
cakupan CSS §3.7, sekarang path absolut basi). `library_path` dan
`shows_path` di `settings.json` adalah **path absolut yang ditulis
lengkap saat pertama kali disimpan**, bukan dihitung ulang dari
`app_data_dir()` tiap dibaca. Begitu folder di-rename, dua field itu
masih menunjuk ke folder lama yang baru saja lenyap.

Efeknya diam-diam dan berbahaya: `Library.__init__` memanggil `read_json()`
pada path yang sudah tidak ada, dan `read_json()` menganggap "file tidak
ada" sebagai kondisi normal (bukan error), jadi aplikasi terbuka mulus,
tanpa pesan kesalahan apa pun, dengan **library kosong**. Operator yang
tidak memperhatikan akan mengira lagunya benar-benar hilang, padahal
filenya utuh, cuma terputus dari konfigurasi yang menunjuknya.

Ini terjadi pada **data asli** (bukan data uji): migrasi dijalankan pada
folder `%APPDATA%\LyricSpout\` milik operator sendiri yang berisi 11 lagu
tersimpan (termasuk "Siti Nurbaya", "Maroon 5 - Maps", dll, bukan lagu
uji manapun yang pernah dipakai di sesi ini). Setelah migrasi folder
berhasil, `library_path` di `settings.json` masih `...\LyricSpout\library.json`, path yang sudah tidak ada.

**Perbaikan:** `_rewrite_stored_paths()` dipanggil segera setelah folder
di-rename, memeriksa apakah `library_path`/`shows_path` berada tepat di
dalam folder lama (lewat perbandingan prefix path setelah dinormalisasi),
dan kalau ya menggantinya ke folder baru. Path yang sudah dikustomisasi
user ke lokasi lain sama sekali (REQ-F-CFG-02), tidak diawali folder
lama, dibiarkan apa adanya.

Fungsi ini juga dibuat **self-healing**: kalau folder baru sudah ada tapi
folder lama sudah tidak ada (persis kondisi yang sempat tertinggal di
mesin ini sebelum perbaikan ini ditulis), `migrate_legacy_data()` tetap
mencoba memperbaiki path yang nyasar. Tanpa ini, instalasi yang sempat
kena bug ini tidak akan pernah pulih sendiri di run berikutnya, `migrate_legacy_data()` sudah melihat folder baru ada dan langsung
berhenti tanpa memeriksa apa pun.

**Verifikasi (checksum, bukan kesan):** sebelum migrasi, `library.json`
asli dihitung dulu via Python, 11 lagu, judul dicatat satu per satu.
Setelah migrasi + perbaikan path, file yang sama dibaca ulang lewat
`library_path` yang sudah ter-update: 11 lagu, judul identik. Idempotent
diverifikasi (dijalankan dua kali, hasil kedua sama persis dengan yang
pertama), dan path yang dikustomisasi user ke folder di luar `%APPDATA%`
terbukti tidak tersentuh.

> **Pelajaran tambahan:** kesalahan ini nyaris lolos karena `read_json()`
> sengaja dirancang untuk tidak melempar error saat file tidak ada, desain
> yang benar untuk kasus "lagu belum pernah disimpan", tapi berbahaya untuk
> kasus "path-nya sendiri yang salah". Keduanya terlihat identik dari sisi
> `Library`: koleksi kosong. **Verifikasi migrasi data wajib memakai
> checksum isi (jumlah/nama lagu), bukan cuma "aplikasi terbuka tanpa
> error".**

### 3.9 Catatan Fase 4, Operator Display & hotkey global (v0.8)

**Operator Display sengaja read-only.** Tidak ada satu pun tombol di window
itu yang mengubah keadaan tayang. Alasannya praktis: window ini ditaruh di
monitor kedua dan ditinggal, jadi mouse yang tersenggol tidak boleh
mengubah apa pun di Resolume. Kontrol tetap hanya di tab Live. Dua tombol
yang ada (`Full screen`, `Sembunyikan preview`) hanya mengubah window itu
sendiri.

**Preview-nya mencerminkan, bukan merender ulang.** Ada dua alasan, dan
yang kedua lebih penting daripada yang pertama:

| | mirror | dua render terpisah |
|---|---|---|
| Biaya (kondisi terburuk, 1179×663, gambar ulang tiap frame) | **6,1 ms** | 11,7 ms |

Keduanya masih di bawah budget 33,3 ms, jadi ini **bukan** kasus "kalau
tidak begini akan gagal", hanya menyisakan headroom. Alasan sebenarnya:
dua renderer terpisah punya `ScrollAnimator` masing-masing, jadi posisi
animasinya bisa meleset beberapa milidetik dan operator akan melihat
Operator Display sedikit tidak sinkron dengan preview di tab Live. Sama
semangatnya dengan REQ-F-OUT-08.

> ⚠️ **Koreksi pengukuran (ketiga kalinya soal ini).** Versi pertama
> komentar kode di `set_mirror()` menulis "masing-masing ~28 ms, totalnya
> 56 ms, menembus budget", angka yang **diekstrapolasi dari §3.2, bukan
> diukur di konteks ini**. Pengukuran sebenarnya: 11,7 ms vs 6,1 ms.
> Selisihnya nyata dan desainnya tetap benar, tapi justifikasinya
> sebelumnya melebih-lebihkan. Komentar sudah dikoreksi ke angka terukur.
> Lihat juga §3.5, aturannya sudah ada, dan tetap kelanggar sekali lagi.

**Hotkey global memakai Ctrl+Alt+…, bukan Space/B polos.** Ini bukan
pilihan gaya. `RegisterHotKey` bersifat **eksklusif se-sistem**: selama
terdaftar, aplikasi lain tidak menerima tombol itu lagi. Mendaftarkan
`Space` polos secara global akan mematikan tombol spasi di seluruh
Windows, tidak bisa mengetik spasi di aplikasi mana pun. Jadi hotkey
global sengaja berbeda dari hotkey dalam-window, dan perbedaan itu
ditampilkan di tab Settings.

| | dalam window | global |
|---|---|---|
| Play/Pause | `Space` | `Ctrl+Alt+Space` |
| Baris ±1 | `←` `→` | `Ctrl+Alt+←` `Ctrl+Alt+→` |
| Blank | `B` | `Ctrl+Alt+B` |

Diimplementasikan lewat Win32 `RegisterHotKey` + `QAbstractNativeEventFilter`,
**tanpa dependency baru**: tidak butuh hak admin, dan tidak memasang
keyboard hook global (yang menangkap semua ketikan termasuk password
orang, dan sering ditandai antivirus).

**Kegagalan pendaftaran dilaporkan, tidak didiamkan.** Kombinasi yang sudah
dipakai aplikasi lain akan gagal didaftarkan; pesannya muncul di tab
Settings. Kalau didiamkan, operator menekan tombol saat live dan tidak
terjadi apa-apa tanpa penjelasan, mode gagal yang sama dengan BLANK di
§3.3.

**Verifikasi:** 4 dari 4 kombinasi terdaftar, idempotent (install 2× tidak
menggandakan), `uninstall()` bersih dan kombinasinya bisa didaftarkan lagi
sesudahnya. Yang terpenting, **jalur penerimaan pesannya diuji sungguhan**, `WM_HOTKEY` dikirim lewat `PostMessageW` ke window handle asli, dan
callback-nya terbukti terpanggil (bukan cuma "terdaftar"). Pembedaan itu
penting: di proyek ini sudah dua kali ada hal yang terlihat terpasang tapi
tidak pernah benar-benar berjalan (§3.3, §3.4).

Yang masih terbuka: menekan kombinasinya sungguhan saat aplikasi lain sedang
fokus, dan perilaku Operator Display di monitor kedua sungguhan. Mesin uji
hanya punya satu monitor, jadi pemilih monitor belum pernah melihat lebih
dari satu pilihan. Keduanya tercatat sebagai V3 dan V4 di §3.13.

### 3.10 Catatan Fase 5, Remote (OSC/MIDI), dan apa yang sengaja TIDAK dibangun

Seluruh item Fase 5 berprioritas **Could**, prioritas terendah di dokumen
ini. Karena itu keputusannya bukan "bangun semuanya", melainkan menilai
mana yang benar-benar berbayar. Dua dibangun, dua tidak.

#### Dibangun: OSC (REQ-F-RC-01)

Parser OSC 1.0 ditulis sendiri, **tanpa dependency baru**. Formatnya
sederhana dan yang dipakai cuma sebagian kecil; menambah library hanya
untuk ini tidak sepadan.

**Dua jebakan yang ditemukan lewat pengujian, keduanya menyebabkan
kesalahan diam-diam:**

**(a) `SO_REUSEADDR` menyembunyikan bentrokan port.** Awalnya opsi itu
dipasang karena kebiasaan dari server TCP. Di Windows opsi itu justru
**mengizinkan proses kedua ikut mengikat port yang sama** (berbeda dari
Linux), jadi kalau operator sudah punya aplikasi lain di port 8000,
CUEVO ikut bind dan melaporkan "aktif", padahal pesan OSC-nya bisa nyasar
ke aplikasi itu. Terbukti di pengujian: bind kedua "berhasil". Diperbaiki
dengan `SO_EXCLUSIVEADDRUSE`, sehingga bentrokan gagal secara eksplisit dan
bisa dilaporkan ke operator.

> Catatan kecil yang jujur: perbaikan pertamanya juga salah, > `SO_EXCLUSIVEADDRUSE` dihitung sebagai `~SO_REUSEADDR + 1` (= −4),
> padahal definisinya `~SO_REUSEADDR` (= −5). Akibatnya bind **pertama**
> ikut gagal dengan WinError 10022. Ketahuan karena pengujiannya memeriksa
> bind pertama juga, bukan cuma yang kedua.

**(b) Filter "tombol dilepas" memakan nilai nol yang sah.** Kebanyakan
controller (TouchOSC, Resolume, foot controller) mengirim dua pesan per
tekanan: `1.0` saat ditekan, `0.0` saat dilepas. Tanpa filter, satu
tekanan memicu aksi **dua kali**, saat live artinya lirik melompat dua
baris. Filter ditambahkan, dan ternyata memunculkan bug kedua: pesan yang
argumennya adalah **nilai**, bukan status tombol, ikut termakan.
`/cuevo/offset 0.0` artinya "set offset ke nol", nilai sah yang justru
sering dipakai untuk reset. Efeknya: satu-satunya nilai yang tidak bisa
dikirim adalah nol. Diperbaiki lewat `VALUE_COMMANDS`, dan diverifikasi
bahwa tombol tetap terfilter sementara nilai nol lolos.

#### Dibangun: MIDI (REQ-F-RC-02)

`python-rtmidi` terpasang bersih di Python 3.13 (wheel cp313 tersedia),
jadi tidak ada alasan teknis untuk menundanya. Dibuat **opsional** seperti
SpoutGL: kalau belum terpasang atau tidak ada device, kontrolnya nonaktif
dengan keterangan, aplikasi tetap jalan penuh.

Jebakan yang sama dengan OSC muncul lagi dalam bentuk berbeda: **Note On
dengan velocity 0 sebenarnya adalah Note Off**, konvensi yang dipakai
hampir semua device MIDI. Tanpa ditangani, satu injakan pedal memicu aksi
dua kali. Sudah ditangani dan diuji.

OSC dan MIDI memakai **daftar aksi yang sama persis** (`_remote_actions()`),
bukan dua implementasi paralel, diverifikasi lewat pengujian bahwa
himpunan perintah MIDI adalah subset dari perintah OSC dan keduanya ada di
daftar aksi.

**Keselamatan thread.** Listener OSC dan MIDI memanggil handler dari thread
masing-masing, bukan thread GUI. Menyentuh widget Qt dari thread lain
adalah undefined behaviour. Keduanya dijembatani lewat `RemoteBridge`
(signal Qt, otomatis di-queue ke thread GUI), pola yang sama dengan
pencarian LRCLIB.

#### TIDAK dibangun: NDI (REQ-F-OUT-06), evaluasi

Roadmap §9 menuliskan **"evaluasi NDI"**, dan evaluasi itulah hasilnya:

| | |
|---|---|
| Biaya | NDI SDK runtime harus dipasang terpisah (installer sendiri, punya syarat lisensi), plus binding Python (`ndi-python`/`cyndilib`) yang jauh kurang matang dibanding SpoutGL |
| Manfaat di kasus utama | **Nol.** Kasus utama produk ini satu mesin: CUEVO Lyrics dan Resolume di komputer yang sama. Spout sudah menanganinya lewat GPU, tanpa lewat jaringan |
| Manfaat di kasus lain | Nyata tapi belum ada: kirim lirik ke mesin lain di jaringan |

**Rekomendasi: tunda sampai ada kebutuhan nyata lintas-mesin.** Membangun
sekarang berarti menambah dependency berat, permukaan bug baru (encoding,
bandwidth, latency jaringan), dan beban perawatan, untuk kemampuan yang
belum pernah dibutuhkan sekali pun. Kalau nanti dibutuhkan, arsitekturnya
sudah siap: `spout_output.py` sudah terisolasi di satu modul (REQ-NF-07),
jadi `ndi_output.py` bisa berdampingan tanpa mengubah apa pun di atasnya.

#### TIDAK dibangun: multi Spout sender (REQ-F-OUT-07), evaluasi

Secara teknis **murah**: `SpoutOutputThread` sudah menerima `sender_name`,
jadi menjalankan dua thread hampir tidak butuh kode baru.

Masalahnya bukan teknis, tapi **tidak ada isi untuk sender kedua**. Gunanya
multi-sender adalah memisahkan lapisan, mis. teks di satu sender,
background di sender lain. Tapi background layer (REQ-F-STYLE-04, juga
prioritas Could) belum dibangun. Membangun multi-sender sekarang
menghasilkan dua sender yang menampilkan **gambar yang sama persis**.

**Rekomendasi: kerjakan REQ-F-STYLE-04 lebih dulu kalau memang diinginkan;
multi-sender baru masuk akal sesudah ada lapisan yang layak dipisah.**

#### Batas pengujian OSC dan MIDI

Yang terbukti pada keduanya adalah **jalur perangkat lunaknya**: pesan masuk,
diurai, disaring dengan benar, lalu dieksekusi di thread GUI. Yang belum
terbukti adalah ujung luarnya, yaitu controller atau software nyata yang
benar-benar mengirim. Untuk OSC, pengirimnya selama ini adalah skrip UDP
buatan sendiri di mesin yang sama; untuk MIDI, pesannya buatan, karena
Windows tidak menyediakan MIDI loopback sehingga aplikasi tidak bisa
mengirim ke dirinya sendiri.

Pemilik produk menyatakan pengujian ini **tidak mendesak**, jadi keduanya
dibiarkan terbuka dan tercatat sebagai V1 dan V2 di §3.13, lengkap dengan
cara menutupnya. Yang penting: statusnya di §4 ditulis "terpasang", bukan
"selesai", supaya tidak ada yang membangun keputusan lain di atas asumsi
bahwa keduanya sudah terbukti bekerja dengan perangkat nyata.

### 3.11 Font mengikuti sistem (v0.9.1)

Sebelumnya `theme.py` memaku `SANS = "Segoe UI"` dan `MONO = "Consolas"`.
Di mesin yang font sistemnya diganti, aplikasi jadi tidak senada dengan
aplikasi lain; dan kalau font itu tidak ada, Qt jatuh ke pengganti
sembarang. Sekarang `theme.init_fonts()` dipanggil di `main()` tepat
setelah `QApplication` dibuat, sebelum stylesheet disusun.

- **SANS: murni dari sistem** (`QApplication.font()`), tanpa preferensi.
- **MONO: ada satu pengecualian yang disengaja.** Di Windows,
  `QFontDatabase.systemFont(FixedFont)` mengembalikan **Courier New**, peninggalan lama. Diukur berdampingan pada 13px, Courier New jauh lebih
  tipis dan lebih sulit dibaca sekilas dibanding Consolas, padahal yang
  memakainya adalah **timecode** yang dibaca cepat di venue gelap.
  Keduanya sama-sama monospace (lebar digit terbukti seragam), jadi ini
  murni soal keterbacaan. `PREFER_MONO` mencoba Consolas → Cascadia Mono →
  SF Mono → DejaVu Sans Mono, lalu **jatuh ke font sistem** kalau tidak
  satu pun ada. Mengosongkan `PREFER_MONO` memberi perilaku 100% sistem.

Monospace tetap wajib untuk teks waktu: dengan font proporsional, lebar
tiap digit berbeda sehingga angka detik membuat seluruh baris bergoyang
setiap kali berubah.

**Efek di mesin uji: nol perubahan visual**, font sistemnya memang Segoe
UI dan Consolas tersedia. Manfaatnya muncul di mesin dengan font sistem
berbeda.

> ⚠️ **Jebakan pengujian yang hampir menyesatkan.** Pemeriksaan pertama
> dijalankan dengan `QT_QPA_PLATFORM=offscreen` dan melaporkan **5 label
> terpotong**. Angka itu palsu: platform offscreen tidak punya konfigurasi
> font sistem, sehingga font resolve ke "Sans Serif"/"monospace" generik
> yang metriknya berbeda. Diulang dengan platform Windows asli: **1** yang
> benar-benar terpotong. **Pengujian apa pun yang menyangkut metrik font
> tidak sah dijalankan di platform offscreen**, ini juga menjelaskan kenapa
> semua tangkapan layar offscreen di dokumen ini menampilkan kotak-kotak.

**Dua teks terpotong yang ditemukan** (keduanya sudah ada sebelum
perubahan font ini, bukan akibatnya):

1. Petunjuk "klik ganda = pindah lagu" di footer kolom set list, kolomnya
   216px dan dua tombol sudah memakannya, jadi teks apa pun di situ pasti
   terpotong. Dipindah jadi tooltip.
2. Daftar alamat OSC di tab Settings, dipecah manual dengan `
`.
   Pemenggalan tetap pasti salah di salah satu lebar panel; diganti jadi
   `setWordWrap(True)`.

Hasil akhir: **0 label terpotong di kelima tab.**

### 3.12 Redesign tab Settings dan kontrol pilihan (v0.9.2)

Dikerjakan memakai skill desain, dengan satu catatan cakupan yang jujur:
skill itu menyatakan sendiri bahwa **dense product UI dan form panel di luar
cakupannya**. Yang dipakai hanya bagian yang memang berlaku (disiplin tata
letak, hierarki, konsistensi bentuk dan warna, kontras form, daftar tanda
khas keluaran AI); bagian hero, scroll, dan strategi gambar tidak dipakai.

#### Tab Settings: dari daftar rata jadi modul rak

Audit tampilan lama menemukan enam masalah, semuanya dari tangkapan layar
yang berjalan, bukan dugaan. Yang terpenting: **sepuluh baris berirama
identik**, sehingga nama sender yang disetel sekali seumur hidup punya bobot
visual sama persis dengan tombol OSC yang berakibat langsung saat acara
berjalan; dan **keadaan hidup atau mati tidak terlihat sama sekali** tanpa
mencoba menekan sesuatu.

Dipilih opsi "modul rak": kategori lama dipertahankan (tidak ada yang perlu
dipelajari ulang, sesuai §11.F skill soal tidak mengubah navigasi diam-diam),
tapi tiap kelompok jadi modul dengan kepala dan lencana, disusun dua kolom.

**ATURAN LENCANA.** Lencana wajib mencerminkan keadaan yang benar-benar
diperiksa. `app.py` mendorongnya tiap 500ms. Lencana yang menampilkan
"aktif" tanpa memeriksa lebih buruk daripada tidak ada lencana, karena itu
persis mode gagal BLANK (§3.3). Terverifikasi: lencana OSC berubah dari
`MATI` ke `PORT 8000` **hanya setelah listener benar-benar bind**, dan jadi
`GAGAL` warna amber kalau portnya bentrok.

Dua kesalahanku sendiri yang ketahuan saat membangun:

1. **Komentar tidak cocok dengan kode.** Ditulis "dikelompokkan menurut
   fungsi", padahal fungsinya membagi 13 alamat OSC rata jadi 5/5/3 sehingga
   alamat blank tercampur alamat lagu di kolom yang sama. Diperbaiki jadi
   pengelompokan eksplisit per kolom, plus penjaga: alamat baru yang lupa
   dimasukkan akan **muncul sebagai peringatan**, bukan hilang diam-diam.
2. **Hampir membaca disk 2x per detik.** Jumlah show dihitung dengan membaca
   folder di dalam timer 500ms, sepanjang acara, untuk angka yang hanya
   terlihat di tab Settings. Sekarang hanya dihitung saat tab itu dilihat.

#### Kontrol pilihan: penyebabnya kelalaian, bukan selera

`theme.py` hanya mengatur warna teks radio dan checkbox. **`::indicator`
tidak pernah digaya sama sekali**, sehingga yang tampil selama ini adalah
indikator native Windows apa adanya: sudut membulat sekitar 4px dan centang
gaya Windows 11, di dalam panel yang seluruh sudutnya 0 sampai 2px. Kontrol
itu tidak pernah didesain, ia diwarisi karena kelalaian.

Tiga masalah lain: pilihan yang tidak aktif diwarnai T3, sama persis dengan
kontrol yang dinonaktifkan, sehingga terbaca "tidak tersedia" padahal sah;
label checkbox tidak ikut berubah, sehingga tulisan "Aktif" sama saja saat
hidup maupun mati; dan ketiga grup radio isinya tepat dua pilihan, memakai
dua baris untuk satu keputusan.

Sepuluh kontrol diganti `SegmentedControl` (`ui/segmented.py`).

**Aturan warna, dipakai bersama lencana modul:**

| | |
|---|---|
| Pilihan biasa (mode, sumber, layout) | isian netral terang. Ini preferensi, bukan keadaan hidup |
| Sambungan (OSC, MIDI, hotkey global) | hijau **hanya** saat benar-benar berjalan; amber kalau gagal |
| Merah | tidak pernah dipakai di sini. Merah hanya milik ON AIR (BLANK) |

**Dibangun dari QPushButton, bukan digambar sendiri.** Tiap segmen adalah
`QPushButton` checkable di dalam `QButtonGroup` eksklusif, sehingga sudah
punya `setChecked`, `isChecked`, `toggled`, `setEnabled`, dan `setToolTip`
persis seperti `QRadioButton`. Akibatnya `SegmentedControl.button(i)` bisa
menggantikan radio **tanpa mengubah satu pun pemanggilnya**, dan penanganan
klik, fokus keyboard, serta keadaan nonaktif tetap memakai milik Qt yang
sudah benar. Aturan `::indicator` tetap ditambahkan di `theme.py` sebagai
jaring pengaman, supaya checkbox yang muncul di tempat lain nanti tidak
kembali jadi kontrol Windows.

**Verifikasi:** seluruh perilaku lama tetap sama (mode manual, ganti sumber,
ganti layout, nyala-mati OSC beserta lencananya), dan **0 kontrol kurang
lebar** di 1280x860 maupun 1100x700.

> ⚠️ **Pengukuran pertama salah lagi, dan polanya sama.** Pemeriksaan awal
> melaporkan 22 kontrol terpotong. Angka itu palsu: lebar teks dibandingkan
> dengan lebar widget dikurangi **tebakan** padding 26px, padahal tombolnya
> berpadding 20px. Diulang memakai `sizeHint()` milik Qt, yang memang
> menghitung teks plus padding plus gaya: **0**. Ini kesalahan sejenis §3.5
> dan §3.9. Aturannya sudah ada, dan tetap terlanggar. **Jangan pernah
> menebak metrik yang toolkit-nya sudah bisa menghitung sendiri.**

### 3.13 Utang verifikasi (daftar hidup)

Dokumen ini sudah tiga kali mencatat fitur yang ditandai "selesai" padahal
belum pernah benar-benar dijalankan (§3.1 animasi, §3.3 BLANK, §3.6 tombol
Tambah ke show). Dua kali di antaranya ditemukan oleh operator, bukan oleh
pengujian. Karena itu semua yang **belum terbukti** dikumpulkan di sini,
bukan diselipkan di paragraf masing-masing bagian.

**Aturan tabel ini:** kolom "sudah terbukti" hanya boleh berisi hal yang
benar-benar dijalankan dan hasilnya dilihat. Sisanya masuk kolom "belum".

| # | Hal | Sudah terbukti | Belum terbukti | Prioritas |
|---|---|---|---|---|
| **V1** | Trigger OSC | Datagram UDP sungguhan dikirim ke aplikasi yang berjalan; ke-13 alamat memicu aksi yang benar; tekan-lepas dihitung sekali; nilai nol tetap diterima; bentrokan port dilaporkan | Dari **controller atau software nyata** (TouchOSC, Resolume OSC out, controller fisik). Termasuk: apakah Windows Firewall memblokir UDP masuk, dan apakah format alamat yang dipilih cocok dengan yang dikirim perangkat itu | Rendah, dinyatakan tidak mendesak oleh pemilik produk |
| **V2** | Trigger MIDI | Port terbuka pada APC mini mk2 sungguhan; logika callback terbukti dengan pesan buatan; Note On velocity 0 tidak memicu aksi dua kali | **Menekan pad sungguhan.** Windows tidak punya MIDI loopback bawaan, jadi tidak bisa dikirim ke diri sendiri. Termasuk: apakah note 48 sampai 53 jatuh di pad yang memang diinginkan | Rendah, dinyatakan tidak mendesak oleh pemilik produk |
| **V3** | Hotkey global | Keempat kombinasi terdaftar; `WM_HOTKEY` dikirim lewat `PostMessageW` dan callback terbukti terpanggil; lepas-pasang bersih | **Menekan tombolnya sungguhan** saat aplikasi lain sedang fokus | Rendah |
| **V4** | Operator Display di monitor kedua | Window terbuka, NOW/NEXT terisi benar, preview mencerminkan tab Live, fullscreen dan Esc jalan | Perilaku di **monitor kedua sungguhan**. Mesin uji cuma punya satu monitor, jadi pemilih monitor hanya pernah melihat satu pilihan | Sedang, ini fitur yang memang dibuat untuk dua monitor |
| **V5** | Navigasi keyboard segmented | Klik dan API-nya benar; perilaku lama semuanya utuh | Apakah Tab keliling terasa wajar saat dipakai cepat | Rendah |
| **V6** | Headroom render | 26,0 ms per frame, 22% sisa dari budget 33,3 ms (§3.2) | Angka itu **kedaluwarsa setiap kali renderer disentuh**. Wajib diukur ulang, bukan diasumsikan bertahan | Wajib, tiap perubahan renderer |

**Cara menutup V1 dan V2** kalau nanti diperlukan, masing-masing sekitar
satu menit:

- **V1:** nyalakan OSC di tab Settings, lalu dari Resolume aktifkan OSC out
  atau pakai aplikasi pengirim OSC apa pun ke `127.0.0.1` port 8000, kirim
  `/cuevo/next`. Kalau tidak ada reaksi padahal lencananya hijau,
  tersangka pertama adalah Windows Firewall.
- **V2:** nyalakan MIDI, pilih `APC mini mk2 0`, tekan pad. Kalau pad yang
  ditekan tidak melakukan apa-apa, note-nya berbeda dari 48 sampai 53;
  petanya ada di `remote/midi_listener.DEFAULT_NOTE_MAP` dan gampang diubah.

### 3.14 Jendela Cast: OBS, TikTok Live, layar kedua (v0.10)

Permintaannya "multicast ke OBS, TikTok Live, dan window baru". Ditelusuri
dulu sebelum dibangun, dan ternyata **ketiganya satu fitur yang sama**:

| Tujuan | Yang sebenarnya dibutuhkan |
|---|---|
| OBS | Window Capture atau Game Capture, menangkap jendela mana pun |
| TikTok Live Studio | hanya bisa menangkap layar atau jendela. Tidak mengenal Spout maupun NDI |
| Layar kedua | jendela yang sama, di-fullscreen di monitor lain |

Jadi yang dibangun satu: `ui/cast_window.py`. Tiga tujuan itu cuma cara
memakainya. Membangun tiga jalur terpisah akan menghasilkan tiga tempat
untuk menyimpang, tanpa satu pun kemampuan tambahan.

**Untuk OBS, jalur terbaik justru tidak memakai jendela ini.** OBS punya
plugin Spout2 yang bisa menerima sender yang sudah ada langsung, lengkap
dengan alpha asli. Itu disebutkan di dokumentasi dan di README, karena
menyembunyikannya berarti membiarkan operator memakai jalur yang lebih
buruk padahal yang lebih baik sudah tersedia sejak v0.5.

#### Temuan terukur: alpha tidak selamat lewat Window Capture

Windows menyusun jendela di atas latar buram sebelum menyerahkannya ke
Window Capture, baik lewat BitBlt maupun Windows Graphics Capture. Alpha
per-piksel tidak ikut. Ini sifat Windows, bukan sesuatu yang bisa diakali
dari sisi aplikasi.

Akibatnya khusus di aplikasi ini serius, karena baris konteks memudar
dengan **alpha**, bukan dengan warna. Diukur pada latar hijau chroma dengan
`opacity_falloff` bawaan 0.32:

| Baris | Warna hasil di atas hijau | Nasib setelah di-key |
|---|---|---|
| aktif | `255,255,255` putih murni | aman |
| ±1 | `173,255,173` | menyisakan tepi hijau |
| ±2 | `90,254,90` nyaris hijau murni | **ikut terbuang** |

Dihitung menyeluruh: **57 dari 76 baris piksel berteks tercemar warna
latar.** Artinya di latar chroma, praktis hanya baris aktif yang selamat
utuh, dan operator baru akan menyadarinya saat siaran sudah berjalan.

**Yang dilakukan:** aplikasi mendeteksi kombinasi berbahaya (latar chroma +
`opacity_falloff` > 0 + ada baris konteks) lalu menampilkan peringatan
beserta tombol perbaikan satu klik yang men-nol-kan falloff. Sesudah
diperbaiki, angkanya **0 dari 77**. Hierarki baris tetap terbaca karena
falloff ukuran tidak diubah.

Peringatan itu sengaja diletakkan di antara bilah kontrol dan area gambar,
dan ikut tersembunyi di mode bersih. Apa pun yang menimpa area gambar akan
ikut tersiar.

Tombol perbaikannya bekerja lewat panel Style, bukan menambal `style_config`
langsung, supaya slider di tab Style ikut bergerak dan nilainya bisa ikut
tersimpan ke Template seperti perubahan lain.

#### Hal lain yang dijaga

- **Teks BLANK tidak pernah ikut tersiar.** Di preview dalam aplikasi,
  blank menampilkan tulisan "BLANK" untuk mata operator. Di permukaan siar,
  blank berarti benar-benar kosong: menulis kata itu di sana sama saja
  menyiarkannya ke penonton.
- **Selalu ada jalan keluar.** Di mode bersih jendelanya tanpa bingkai dan
  tanpa tombol. Klik kanan tetap memunculkan menu, Esc selalu mengembalikan
  bilah, dan jendelanya bisa digeser dengan drag. Jendela yang bisa terkunci
  tanpa jalan keluar adalah cacat, bukan kesederhanaan.
- **Biaya render nol.** Jendela Cast tidak merender apa pun sendiri; ia
  memakai `PreviewWidget` dengan sumber yang sama seperti Operator Display
  (§3.9): frame dari thread Spout kalau output jalan, mencerminkan preview
  tab Live kalau tidak.

**Keterbatasan v0.1 yang jadi starting point requirement fase berikut:**
- Tidak ada penyimpanan/persistence (setiap buka app, mulai dari nol).
- Tidak ada playlist, hanya satu lagu aktif dalam satu waktu.
- Tidak ada input lirik manual/offline, 100% bergantung LRCLIB.
- Styling sebagian besar masih hardcoded (parameter konstruktor di kode,
  belum ada panel pengaturan visual di GUI, lihat REQ-F-STYLE-* dan
  REQ-F-OUT-05).
- Tidak ada operator/stage view terpisah, GUI kontrol == satu-satunya
  window.
- Tidak ada remote control (keyboard shortcut global, MIDI, OSC).

### 3.15 Tab Donate (v0.11)

Permintaannya: satu tab donasi berisi Saweria, QR pembayaran, dan kontak.
Yang dibangun `ui/donate_view.py`, satu file, tanpa dependensi baru.

**Semua yang perlu diganti ada di satu blok di paling atas file:**
`SAWERIA_URL`, `QRIS_FILE`, `QRIS_NAME`, `QRIS_NMID`, `CONTACTS`, `INTRO`.
Proyek ini dibagikan sebagai open source, jadi orang yang fork harus bisa
mengganti nomor donasi milik orang lain dalam hitungan detik. Kalau nilainya
tersebar ke seluruh file, sebagian pasti tertinggal, dan uang orang lain
yang masuk ke rekening yang salah adalah cacat yang mahal.

#### Kenapa labelnya "QRIS", bukan "DANA"

Payload QR-nya dibaca dan diperiksa isinya: diawali `00020101021126570011
ID.DANA.WWW`, artinya memang diterbitkan DANA. Tapi formatnya QRIS, standar
nasional, jadi bisa dipindai GoPay, OVO, ShopeePay, LinkAja, dan aplikasi
bank. Menulis "DANA" akan membuat pengguna dompet lain mengira mereka tidak
bisa ikut. Labelnya QRIS, dan daftar aplikasinya ditulis di bawahnya.

#### QR yang tidak bisa dipindai adalah QR yang tidak ada

File yang dipasang pertama kali adalah **poster QRIS utuh** 1136x1600, bukan
kode QR-nya saja. Ditampilkan dalam kotak 230px, kode QR di dalam poster itu
tinggal sekitar 80px di layar. Ada gambarnya, kelihatan benar, dan tidak
bisa dipindai.

Perbaikan pertamanya masih salah. Simbolnya dipotong dari poster, diberi
quiet zone, lalu ditampilkan 230px, dan **payload-nya sama persis** dengan
poster aslinya. Semua pemeriksaan file lolos. Yang tidak lolos: memindai
ulang tangkapan layar aplikasinya.

**Aturan ujinya, dan ini yang membedakan:** yang dipindai harus **tangkapan
layar aplikasi**, bukan file gambarnya. Orang memindai dari monitor, jadi
penskalaan Qt, ukuran kotak, dan latar panel ikut menentukan. Memeriksa file
aslinya akan selalu lolos walaupun yang tampil di layar tidak terbaca sama
sekali. Tiga percobaan berturut-turut gagal karena hanya file yang diperiksa.

Setelah diukur lewat render Qt sungguhan, sumber masalahnya jelas: kode QRIS
ini **versi 26, 121 modul**. Angka-angka yang diuji, tiap ukuran tiga kali:

| Ukuran tampil | Piksel per modul | Terbaca dari layar |
|---|---|---|
| 230 px | 1,8 | 0/3 |
| 340 px | 2,7 | 0/3 |
| 400 px | 3,2 | 0/3 |
| 460 px | 3,7 | 0/3 |
| **490 px** | 3,9 | **3/3** |
| **516 px** | 4,0 | **3/3** |

Memperkecil grid modul menimbulkan moire, dan di bawah 4 piksel per modul
kodenya berhenti terbaca. Tidak ada jalan tengah: menampilkan QR ini kecil
supaya "muat" berarti QR-nya tidak berfungsi, dan QR yang tidak bisa
dipindai sama saja tidak ada.

Yang akhirnya dikerjakan:
1. Grid 121x121 modulnya dibaca balik dari poster dengan mengambil sampel
   titik tengah tiap modul, lalu digambar ulang bersih pada 4 piksel per
   modul. **Payload-nya tidak pernah di-encode ulang**, hanya dibaca
   gridnya, karena kalau decode-nya meleset sedikit saja uang orang bisa
   masuk ke rekening yang salah.
2. Hasilnya persis 516px, dan `donate_view` menampilkannya **tanpa
   `scaled()`** sama sekali. Menskalakan ke ukuran yang sama pun tetap
   melewatkan resampling, dan itulah yang merusak gridnya.
3. Payload potongan dibandingkan dengan payload poster: identik.
4. Ukuran file ikut turun dari 534 KB jadi 16 KB, efek samping dari
   menggambar ulang alih-alih memotong citra berartefak.

Satu percobaan yang sempat dicoba dan **ditolak**: menyimpan QR sebagai PNG
1-bit. Ukurannya jadi 6 KB, tapi Qt tidak menghaluskan saat memperkecil
gambar format mono, jadi hasilnya justru lebih parah. Ketahuan hanya karena
tangkapan layarnya dipindai ulang.

Poster aslinya disimpan di `design/qris_poster.png`. Folder `design/`
sengaja di luar `assets/`, karena `assets/` disalin utuh ke dalam .exe oleh
`CUEVO Lyrics.spec` dan file sumber tidak perlu ikut.

#### Label wordWrap yang terpotong

Muncul lagi pola §3.7 dan §3.12 dalam bentuk lain. `QLabel` menghitung
sizeHint seolah teksnya satu baris, jadi label yang membungkus akan
terpotong. Ditambal `_fit_wrapped()`. Percobaan pertamanya masih salah:
tingginya dihitung dari `fontMetrics()` sebelum widget dipoles, jadi masih
memakai font bawaan Qt, bukan `font-size` dari stylesheet. Perbaikannya
`ensurePolished()` dulu, baru `heightForWidth()`.

Pemeriksaan otomatis lebar teks tidak menangkap ini, karena label yang
membungkus memang dilewati pemeriksaan lebar sementara yang kurang justru
tingginya. Pemeriksaannya sekarang mengukur keduanya, dan dijalankan di
keenam tab: 0 terpotong.

#### Tab yang bisa digulir

Konsekuensi dari 516px: QR-nya butuh 536px tinggi termasuk padding, dan di
jendela minimum 1280x800 tinggi segitu tidak muat setelah intro dan bar
kontak. Percobaan pertamanya QR-nya terpotong panel, dan QR terpotong sama
tidak bergunanya dengan QR yang terlalu kecil.

Isi tab Donate sekarang dibungkus `QScrollArea`. Ini satu-satunya tab yang
digulir, dan memang cuma tab ini yang punya satu elemen berukuran tetap
yang lebih tinggi dari jendelanya.

#### Nada halamannya

Sengaja tenang. Tidak ada popup, tidak ada pengingat berkala, tidak ada
badge di tab. Aplikasi ini dipakai orang saat show berjalan, dan halaman
donasi yang mendesak akan mengganggu pekerjaan mereka. Kalau file QR-nya
hilang saat build, tempatnya diisi kotak bertuliskan persis file apa yang
kurang, bukan ruang kosong tanpa penjelasan.

### 3.17 Persiapan rilis publik pertama (v0.11)

**Dokumen dipisah menurut pembacanya, bukan disamakan.**

| Dokumen | Bahasa | Untuk siapa |
|---|---|---|
| `README.md` | Inggris | Orang yang menemukan repo ini di GitHub |
| `CHANGELOG.md` | Inggris | Orang yang mau tahu isi rilis |
| `SRS.md` | Indonesia | Catatan kerja, pemilik produk |
| `design/README.md` | Indonesia | Yang menyentuh file sumber |

README dan CHANGELOG berbahasa Inggris karena antarmuka aplikasinya sudah
Inggris dan penontonnya global. SRS tetap Indonesia: isinya catatan
pengambilan keputusan, bukan dokumen pemasaran, dan menerjemahkannya cuma
menambah risiko salah arti tanpa menambah pembaca.

**Bug `.gitignore` yang membuat build tidak bisa diulang.** Barisnya `*.spec`,
warisan dari template gitignore Python, dan itu ikut membuang
`CUEVO Lyrics.spec`. Artinya siapa pun yang meng-clone repo ini tidak bisa
membangun .exe-nya, padahal README menyuruh menjalankan perintah yang
memakai file itu. Ditambal dengan pengecualian `!CUEVO Lyrics.spec`.

Polanya sama dengan §3.7 dan §3.8: **default yang berlaku lebih luas dari
yang dikira.** `*.spec` dibuat untuk file spec sementara, dan ikut menyapu
satu-satunya file spec yang justru harus ikut.

**Yang sengaja tidak disembunyikan di README.** Bagian "Known limitations"
menyebut apa adanya bahwa OSC dan MIDI belum pernah diuji dengan perangkat
sungguhan (§3.13), bahwa Spout cuma jalan di Windows, dan bahwa build-nya
tidak ditandatangani sehingga SmartScreen akan memperingatkan. Rilis pertama
yang menyembunyikan tiga hal itu akan langsung jadi tiga issue di hari
pertama.

**Versinya v0.11.0, bukan v1.0.0.** Masih ada utang verifikasi yang belum
lunas di §3.13. Menandai sesuatu 1.0 padahal jalur remote-nya belum pernah
disentuh perangkat asli adalah klaim yang tidak bisa didukung.

---

### 3.16 Ikon aplikasi (v0.11)

Sumbernya `design/cuevo_desktop_icons_bigger.zip`, berisi dua varian.

**Dipakai `squircle-badge`, bukan `extra-tight`.** Alasannya diukur, bukan
selera: logo `extra-tight` rasionya sekitar 2,5:1, sedangkan slot ikon
Windows persegi. Di kanvas persegi logo itu jadi pita tipis, dan pada 16px
sudah tidak terbaca bentuknya. Garis luarnya juga putih, jadi di desktop
bertema terang bagian itu hilang. Varian squircle mengisi kanvas dan tetap
kebaca di 16px, di latar gelap maupun terang.

**`app-icon.ico` bawaan zip tidak dipakai, dibangun ulang.** Isinya cuma
16x16 (652 byte). Windows memakai 32 di taskbar, 48 di desktop, dan 256 di
tampilan ikon besar; kalau ukurannya tidak ada, Windows memperbesar yang
16px dan hasilnya buram. `assets/app-icon.ico` sekarang berisi 16, 24, 32,
48, 64, 128, 256, semuanya dari PNG asli, bukan hasil perbesaran.

**`setWindowIcon()` saja tidak cukup di Windows.** Taskbar mengelompokkan
jendela berdasarkan AppUserModelID. Tanpa itu diisi, jendela ini ikut
kelompok `python.exe` dan yang muncul di taskbar adalah ikon Python.
Diperbaiki di `app._set_app_icon()` lewat `ctypes` ke
`SetCurrentProcessExplicitAppUserModelID`, tanpa dependensi baru, dan
dibungkus supaya build non-Windows tetap jalan.

Diverifikasi: setiap ukuran yang diminta (16/32/48/256) dijawab piksel
persis segitu, artinya benar-benar diambil dari .ico dan bukan hasil Qt
memperbesar satu-satunya ukuran yang ada.

### 3.18 Penanda bagian lagu: Verse/Chorus/Bridge (v0.11.1)

Permintaannya: bisa menandai Verse/Reff/Bridge di lirik tab Live.
REQ-F-PLAY-08.

**Desain: penanda per baris (chapter marker), bukan tag berkelanjutan.**
Klik kanan sebuah baris di tab Live memberinya label ("bagian ini mulai di
sini"), bukan menandai rentang baris. Ini yang dibutuhkan untuk scan cepat
saat live, dan jauh lebih sederhana daripada melacak "baris mana saja yang
termasuk chorus ini".

**Kenapa disimpan sebagai index baris, bukan timestamp.** `Song.sections`
berisi `[(line_index, label), ...]`. Kalau dikaitkan ke waktu, `shifted()`
(REQ-F-LIB-05, geser semua timestamp) harus ikut menggeser tiap penanda dan
gampang meleset. Dikaitkan ke index, `shifted()` otomatis tetap benar tanpa
disentuh sama sekali, karena jumlah dan urutan baris tidak berubah, cuma
waktunya.

**Kenapa tetap satu baris = satu item, bukan baris tambahan untuk label.**
`self.lyrics` (daftar lirik di tab Live) memakai `setUniformItemSizes(True)`
untuk performa di lagu berbaris ratusan (lihat §3.2 soal ongkos render).
Percobaan pertama menaruh label di baris terpisah sebelum barisnya sendiri,
dan itu berarti sebagian item dua baris tinggi, sebagian satu, sementara
uniform-size memaksa semuanya ke tinggi yang sama, hasilnya baris terpotong
atau ruang terbuang di semua baris lain. Diperbaiki jadi tag di depan teks
baris yang sama (`[CHORUS]  00:59.84  ...`) plus warna aksen
(`theme.STANDBY`), satu item tetap satu baris.

**Kenapa disimpan lewat `Song.sections`, bukan transient di tab Live saja.**
Operator biasanya menandai struktur lagu sekali saat latihan, lalu memakai
lagu yang sama di banyak show. Simpan sekali, konsisten di REQ-F-PLAY-08.
Tapi hasil pencarian LRCLIB yang belum disimpan ke library mendapat `id`
baru setiap kali dimuat (lihat `LibraryView._as_song`), jadi menandainya
lalu memanggil `library.upsert()` akan membuat entri duplikat, bukan
memperbarui yang dimaksud. Ditambal dengan pemeriksaan
`library.get(song.id) is not None` sebelum upsert; kalau lagunya belum
tersimpan, penanda tetap berlaku untuk sesi ini saja dan pesan status
bilang persis kenapa.

**Kenapa penanda dibuang kalau jumlah baris berubah saat re-edit.** Editor
lirik manual bisa memecah ulang teks jadi baris berbeda jumlahnya. Index
lama yang dipertahankan begitu saja lewat `dataclasses.replace()` akan
menunjuk baris yang salah setelah itu -- label yang salah tempat lebih
berbahaya daripada label yang hilang, jadi `_build_song()` di
`lyric_editor.py` membuang `sections` kalau `len(lines)` berubah, dan
mempertahankannya kalau cuma timestamp yang diperbaiki.

**Insiden saat verifikasi: skrip uji sempat menulis ke data pengguna
sungguhan.** Skrip verifikasi menyalin `settings.json` asli ke folder
`%APPDATA%` sementara supaya pengaturan lain (font cache) ikut terbawa.
`settings.json` ternyata menyimpan `library_path` sebagai **path absolut**
dari sesi nyata sebelumnya, dan path absolut itu tetap menunjuk ke file
asli walau `os.environ["APPDATA"]` sudah dialihkan ke folder sementara.
Akibatnya `library.upsert()` menulis penanda uji ("Guitar solo") ke
`library.json` pengguna yang sesungguhnya. Ketahuan dari hasil pengujian
sendiri (bukan laporan pengguna), langsung diperbaiki di file aslinya
(field `sections` yang nyasar dihapus), dan skrip ujinya diperbaiki supaya
tidak lagi menyalin `settings.json`, plus ditambah assertion yang
menghentikan pengujian seketika kalau `library_path` pernah menunjuk ke
luar folder sementara. Satu efek samping tidak bisa dipulihkan sepenuhnya:
`updated_at` lagu itu ikut ter-bump ke waktu pengujian, yang mengubah
urutannya di daftar "terakhir dipakai" pada Library lokal. Kosmetik, tidak
menghapus atau merusak data lain, tapi tetap harus dicatat karena pengguna
tidak pernah menyetujui perubahan pada datanya sendiri.

Pola akarnya sama dengan §3.8: **path absolut yang disalin mentah-mentah
ikut membawa konteks lama yang tidak lagi valid.** Pelajarannya untuk
verifikasi berikutnya: environment terisolasi harus diperiksa validitasnya
lewat assertion di awal skrip, bukan diasumsikan benar karena env var sudah
diubah.

---

## 4. Requirement Fungsional

Format ID: `REQ-F-<area>-<nomor>`. Prioritas MoSCoW: **M**ust,
**S**hould, **C**ould, **W**on't (untuk versi ini).

### 4.1 Lyrics Source & Library (`LIB`)

| ID | Requirement | Prioritas |
|---|---|---|
| REQ-F-LIB-01 | Sistem **harus** menyediakan **satu kolom pencarian bebas** yang boleh diisi judul, artis, atau keduanya dengan urutan kata bebas (dipetakan ke parameter `q` LRCLIB), dan menampilkan hasil beserta status ketersediaan synced lyrics. Operator tidak boleh dipaksa tahu bagian mana judul dan mana artis. *(v0.3, direvisi dari dua kolom terpisah)* | M |
| REQ-F-LIB-02 | Sistem **harus** bisa memuat synced lyrics dari hasil pencarian ke player aktif. | M *(selesai)* |
| REQ-F-LIB-03 | Sistem **harus** menyediakan editor lirik manual: user bisa ketik/tempel teks lirik + set timestamp per baris (atau import file `.lrc` lokal), untuk lagu yang tidak ada di LRCLIB. | M *(selesai, tap-to-timestamp, tekan Enter tiap baris berganti; ekspor `.lrc` juga tersedia)* |
| REQ-F-LIB-04 | Sistem **harus** menyimpan lagu yang sudah dimuat/diedit ke **library lokal** (file JSON), supaya tidak perlu cari ulang tiap sesi. | M *(selesai, `%APPDATA%\CUEVO Lyrics\library.json`, tulis atomik)* |
| REQ-F-LIB-05 | Sistem **harus** bisa mengedit ulang timestamp lirik yang sudah dimuat (mis. geser semua baris +N detik sekaligus, untuk kasus versi rekaman beda). | S *(selesai, di editor lirik)* |
| REQ-F-LIB-06 | Sistem **sebaiknya** punya pencarian lokal di dalam library (bukan hanya LRCLIB) berdasarkan judul/artis. | S *(selesai, aturan query bebas yang sama dengan LRCLIB, menyaring sambil mengetik)* |
| REQ-F-LIB-07 | Sistem **boleh** mendukung impor massal dari folder berisi banyak file `.lrc`. | C *(selesai, multi-select file, nama file berpola `Artis - Judul` dipecah otomatis)* |
| REQ-F-LIB-08 | Kalau menyimpan lagu LRCLIB yang **sudah ada** di library dan isi barisnya berbeda, sistem **harus** meminta konfirmasi sebelum menimpa, koreksi timestamp yang sudah dikerjakan operator tidak boleh hilang diam-diam. *(v0.4, baru, ditemukan saat pengujian)* | M *(selesai)* |

### 4.2 Show / Playlist Management (`SET`)

| ID | Requirement | Prioritas |
|---|---|---|
| REQ-F-SET-01 | Sistem **harus** bisa membuat **Show/Set list**: daftar lagu terurut untuk satu sesi tampil. | M *(selesai)* |
| REQ-F-SET-02 | Sistem **harus** bisa menambah, menghapus, dan mengurutkan ulang (drag/tombol naik-turun) lagu dalam satu Show. | M *(selesai, drag di tab Show; panel Live sengaja TIDAK bisa di-drag supaya set list tidak teracak saat acara berjalan)* |
| REQ-F-SET-03 | Sistem **harus** bisa berpindah cepat ke lagu berikutnya/sebelumnya dalam Show tanpa lewat pencarian ulang. | M *(selesai, tombol Lagu ◀/▶ dan klik ganda di panel set list)* |
| REQ-F-SET-04 | Sistem **harus** menyimpan Show ke file (`.showproject.json` atau sejenis) yang bisa dibuka kembali persis seperti terakhir disimpan. | M *(selesai, satu file per show, tulis atomik)* |
| REQ-F-SET-05 | Sistem **sebaiknya** menampilkan progres Show (lagu ke berapa dari berapa) di GUI kontrol. | S *(selesai, di status strip, terlihat dari semua tab)* |

### 4.3 Live Playback & Control (`PLAY`)

| ID | Requirement | Prioritas |
|---|---|---|
| REQ-F-PLAY-01 | Sistem **harus** mendukung Play/Pause/Stop terhadap jam internal lirik (sudah ada). | M *(selesai)* |
| REQ-F-PLAY-02 | Sistem **harus** mendukung seek ke posisi tertentu via slider (sudah ada). | M *(selesai)* |
| REQ-F-PLAY-03 | Sistem **harus** mendukung koreksi offset sync manual saat live (sudah ada, `±0.1s/±0.5s`). | M *(selesai)* |
| REQ-F-PLAY-04 | Sistem **harus** punya tombol/hotkey **"Blank"** yang langsung mengosongkan output (transparan penuh) tanpa mengubah posisi waktu, untuk jeda/transisi antar lagu. | M *(selesai, diperbaiki di v0.6 (§3.3), terverifikasi visual di Resolume v0.7.1)* |
| REQ-F-PLAY-05 | Sistem **harus** punya mode navigasi manual **per-baris** (tombol Next Line / Previous Line) sebagai alternatif dari mode auto-timestamp, untuk kasus lagu tanpa tempo tetap (acapella, rubato, dsb.), ini mirip mekanisme "klik untuk lanjut slide" ala ProPresenter. | M *(selesai, di mode manual jam diabaikan, Play/seek dinonaktifkan supaya tidak menyesatkan)* |
| REQ-F-PLAY-06 | Sistem **sebaiknya** mendukung keyboard shortcut global (spasi = play/pause, panah = next/prev line, `B` = blank) minimal saat window aplikasi fokus. | S |
| REQ-F-PLAY-07 | Sistem **boleh** mendukung shortcut global system-wide (aktif walau window lain sedang fokus), berguna kalau operator kerja dari layar berbeda. | C *(selesai, Win32 RegisterHotKey tanpa dependency baru; Ctrl+Alt+… dan alasannya di §3.9)* |
| REQ-F-PLAY-08 | Sistem **boleh** menandai baris lirik dengan bagian lagu (Verse/Chorus/Bridge/dst) supaya operator gampang mengenali struktur lagu saat scroll cepat di tab Live. | C *(selesai, §3.18)* |

### 4.4 Rendering & Output (`OUT`)

| ID | Requirement | Prioritas |
|---|---|---|
| REQ-F-OUT-01 | Sistem **harus** merender lirik ke frame RGBA transparan dan mengirimkannya ke Resolume via Spout secara kontinu. | M *(selesai, **terverifikasi di Windows**, §3.2)* |
| REQ-F-OUT-02 | Sistem **harus** hanya menggambar ulang frame saat tampilan berubah (teks/baris aktif berganti, ATAU sedang dalam animasi transisi antar baris), bukan setiap frame tanpa alasan, untuk efisiensi CPU (sudah ada, disesuaikan untuk mode scroll di v0.2). | M *(selesai)* |
| REQ-F-OUT-03 | Sistem **harus** menganimasikan perpindahan baris aktif secara halus (bukan potongan instan) dengan durasi transisi yang bisa dikonfigurasi (default ±550ms, easing ease-out), supaya terasa "hidup" di layar. | M *(v0.2, selesai)* |
| REQ-F-OUT-04 | Sistem **harus** menampilkan lirik bergaya **scroll seperti Musixmatch**: beberapa baris tampil sekaligus (default 2 baris sebelum + baris aktif + 2 baris sesudah), baris aktif ditonjolkan (ukuran font & opacity lebih besar), baris di sekitarnya mengecil dan memudar makin jauh jaraknya, dan baris yang mepet tepi atas/bawah kanvas ikut memudar (alpha) supaya tidak terpotong tegas. | M *(v0.2, selesai, direvisi dari mode single-line di v0.1)* |
| REQ-F-OUT-05 | Sistem **sebaiknya** menyediakan pengaturan dari GUI untuk jumlah baris konteks (sebelum/sesudah), kecepatan transisi, dan jarak antar baris. | S *(selesai, dan pengaturannya kini benar-benar berpengaruh, lihat §3.4)* |
| REQ-F-OUT-06 | Sistem **boleh** menambahkan output NDI sebagai alternatif Spout untuk kebutuhan lintas mesin/jaringan. | C *(dievaluasi, **ditunda**, manfaat nol di kasus satu-mesin; alasan lengkap §3.10)* |
| REQ-F-OUT-07 | Sistem **boleh** mendukung banyak Spout sender sekaligus (mis. output terpisah untuk teks vs untuk background), untuk fleksibilitas compositing di Resolume. | C *(dievaluasi, **ditunda**, murah secara teknis tapi belum ada isi untuk sender kedua; butuh REQ-F-STYLE-04 dulu, §3.10)* |
| REQ-F-OUT-09 | Sistem **harus** menyediakan jendela keluaran yang bisa ditangkap aplikasi lain (OBS, TikTok Live Studio) atau di-fullscreen di layar kedua, dengan pilihan latar hitam atau chroma key, dan mode bersih tanpa bingkai. *(v0.10, baru)* | M *(selesai, §3.14)* |
| REQ-F-OUT-08 | Preview di GUI dan frame yang dikirim ke Spout **harus** dihasilkan oleh **jalur render yang sama** (`RenderStyle` + `ScrollAnimator` + `MultiLineLyricRenderer` yang identik, beda hanya faktor skala resolusi). Dilarang membuat tiruan tampilan terpisah di sisi GUI, kalau preview dan output bisa berbeda, panel Style (§4.5) kehilangan gunanya. *(v0.3, baru)* | M |

### 4.5 Styling & Template (`STYLE`)

| ID | Requirement | Prioritas |
|---|---|---|
| REQ-F-STYLE-01 | Sistem **harus** menyediakan pengaturan dari GUI (bukan edit kode) untuk: font, ukuran, warna teks, warna outline, tebal outline, posisi vertikal teks. | M *(selesai, font dari katalog 220 font sistem; posisi horizontal tetap rata tengah, lihat catatan di bawah)* |
| REQ-F-STYLE-02 | Sistem **harus** menyimpan pengaturan style sebagai **Template** yang bisa dipakai ulang lintas Show. | S *(selesai, `templates.json`; resolusi sengaja TIDAK ikut template)* |
| REQ-F-STYLE-03 | Sistem **sebaiknya** menyediakan beberapa Template siap pakai (preset) untuk mempercepat setup pertama kali. | S *(selesai, 5 preset, dibangkitkan dari kode sehingga tidak bisa hilang atau tertimpa)* |
| REQ-F-STYLE-04 | Sistem **boleh** mendukung background layer opsional di belakang teks (warna solid/gambar) yang ikut dikirim lewat Spout yang sama atau sender terpisah. | C |
| REQ-F-STYLE-05 | **Klik kanan** pada sebuah kontrol di panel Style **harus** mengembalikan parameter itu saja ke nilai default, tanpa menyentuh parameter lain, mengikuti kebiasaan yang sudah dikenal operator dari Resolume Arena. Parameter yang berbeda dari default ditandai secara visual, dan tersedia "Reset semua" dengan konfirmasi. *(v0.7.2, baru, atas permintaan operator)* | S *(selesai)* |

### 4.6 Operator / Stage Display (`OPS`)

| ID | Requirement | Prioritas |
|---|---|---|
| REQ-F-OPS-01 | Sistem **sebaiknya** memisahkan tampilan **kontrol operator** (daftar lagu, tombol, slider) dari **preview output** (persis seperti yang dikirim ke Spout), supaya operator bisa cek visual tanpa buka Resolume. | S *(selesai, window Operator Display terpisah, bisa dipindah ke monitor lain & fullscreen; sengaja read-only)* |
| REQ-F-OPS-02 | Sistem **boleh** menampilkan baris "berikutnya" di panel operator (seperti stage display ProPresenter), supaya operator siap-siap sebelum next line/lagu. | C *(selesai, NOW/NEXT ukuran besar, dibaca dari jarak 1-2 m)* |

### 4.7 Remote Control (`RC`)

| ID | Requirement | Prioritas |
|---|---|---|
| REQ-F-RC-01 | Sistem **boleh** menerima trigger via **OSC** (Open Sound Control) untuk next/prev/blank/play/pause, memudahkan integrasi dengan controller fisik atau software lain (termasuk Resolume sendiri yang punya OSC out). | C *(terpasang, 13 alamat, parser sendiri tanpa dependency. **Terbukti dari pengirim UDP buatan sendiri; belum dari controller atau software nyata.** §3.10, utang verifikasi V1 di §3.13)* |
| REQ-F-RC-02 | Sistem **boleh** menerima trigger via **MIDI** (mis. dari MIDI foot controller) untuk aksi yang sama seperti di atas. | C *(terpasang, `python-rtmidi` opsional. Port terbuka pada device nyata dan logika callback terbukti, tapi **tekan pad sungguhan belum pernah diuji.** §3.10, utang verifikasi V2 di §3.13)* |

### 4.8 Settings & Persistence (`CFG`)

| ID | Requirement | Prioritas |
|---|---|---|
| REQ-F-CFG-01 | Sistem **harus** mengingat pengaturan terakhir (nama Spout sender, resolusi, font size default) antar sesi. | M *(selesai, `settings.json`, tersimpan otomatis tanpa tombol Simpan)* |
| REQ-F-CFG-02 | Sistem **harus** menyimpan lokasi library & show file default yang bisa dikonfigurasi user. | S *(selesai untuk library; path shows tersimpan tapi baru dipakai Fase 2)* |

### 4.9 Donasi & Kontak (`DON`)

| ID | Requirement | Prioritas |
|---|---|---|
| REQ-F-DON-01 | Sistem **boleh** menyediakan tab donasi berisi tautan Saweria dan kode QRIS yang bisa dipindai dari layar. | C *(selesai, §3.15)* |
| REQ-F-DON-02 | Semua nilai donasi dan kontak **harus** berada di satu blok konfigurasi supaya hasil fork gampang mengganti milik orang lain. | M *(selesai, bagian atas `ui/donate_view.py`)* |

---

## 5. Data Model (usulan)

Disimpan sebagai file JSON lokal (folder `data/` di root project, bisa
disesuaikan). Skema di bawah ini adalah **usulan awal**, boleh
disempurnakan saat implementasi di Claude Code.

### 5.1 `Song`
```json
{
  "id": "uuid-v4",
  "title": "The Chain",
  "artist": "Fleetwood Mac",
  "album": "Rumours",
  "duration_sec": 271,
  "source": "lrclib | manual",
  "lrclib_id": 151738,
  "lines": [
    { "time_sec": 27.93, "text": "Listen to the wind blow" },
    { "time_sec": 30.88, "text": "Watch the sun rise" }
  ],
  "created_at": "2026-08-31T10:00:00Z",
  "updated_at": "2026-08-31T10:00:00Z"
}
```

### 5.2 `Show` (Set list)
```json
{
  "id": "uuid-v4",
  "name": "Minggu Pagi - 31 Agustus",
  "song_ids": ["uuid-song-1", "uuid-song-2"],
  "template_id": "uuid-template-default",
  "created_at": "2026-08-31T10:00:00Z"
}
```

### 5.3 `Template` (Style)
```json
{
  "id": "uuid-v4",
  "name": "Default White Outline",
  "font_path": null,
  "active_font_size": 64,
  "text_color": [255, 255, 255, 255],
  "outline_color": [0, 0, 0, 255],
  "outline_width": 3,
  "layout": "scroll_multiline",
  "vertical_anchor_ratio": 0.5,
  "context_lines_before": 2,
  "context_lines_after": 2,
  "line_spacing_ratio": 1.55,
  "size_falloff": 0.22,
  "opacity_falloff": 0.32,
  "edge_fade_ratio": 0.18,
  "transition_ms": 550
}
```
Field `layout` disiapkan sebagai enum (`scroll_multiline` | `single_line`)
supaya mode single-line v0.1 tetap bisa dipilih sebagai opsi alternatif,
bukan dihapus total, beberapa operator mungkin tetap lebih suka gaya
lower-third yang lebih minimalis untuk visual tertentu.

### 5.4 `Settings` (global, per instalasi)
```json
{
  "spout_sender_name": "LyricSpout",
  "output_width": 1920,
  "output_height": 1080,
  "fps": 30,
  "default_template_id": "uuid-template-default",
  "library_path": "./data/library.json",
  "shows_path": "./data/shows/"
}
```

---

## 6. Requirement Non-Fungsional

| ID | Kategori | Requirement |
|---|---|---|
| REQ-NF-01 | Performance | Frame yang dikirim ke Spout **harus** stabil di target fps (default 30) tanpa drop terlihat, dengan CPU usage rendah saat teks tidak berubah (leverage caching frame yang sudah ada). |
| REQ-NF-02 | Latency | Perubahan baris lirik (baik dari auto-timestamp maupun manual next/prev) **harus** terlihat di Resolume dalam < 100ms. |
| REQ-NF-03 | Reliability | Jika koneksi ke LRCLIB gagal/timeout, aplikasi **tidak boleh** crash, tampilkan pesan error dan tetap bisa lanjut pakai lirik manual/library lokal. |
| REQ-NF-04 | Reliability | Thread Spout output **harus** bisa dihentikan bersih (tanpa hang) saat user klik Stop atau tutup aplikasi. |
| REQ-NF-05 | Usability | Operator baru **harus** bisa cari → muat → tampilkan lagu pertama dalam < 2 menit tanpa baca manual (target onboarding). |
| REQ-NF-06 | Portability | Modul non-Spout (pencarian, parsing, playlist, data model) **harus** tetap bisa dijalankan/diuji di non-Windows untuk kemudahan development di Claude Code, walau fitur Spout sendiri hanya aktif di Windows. |
| REQ-NF-07 | Maintainability | Setiap modul baru **harus** punya pemisahan tanggung jawab yang jelas (mengikuti pola modul v0.1: client/parser/state/renderer/UI terpisah), supaya mudah di-unit-test. |
| REQ-NF-08 | Security/Privacy | Tidak ada data pribadi yang dikirim ke pihak ketiga selain query judul lagu ke LRCLIB (publik, tanpa akun). |
| REQ-NF-09 | Legal/Compliance | Aplikasi **harus** mengirim header `User-Agent` yang jelas ke LRCLIB (sudah ada) dan tidak melakukan polling berlebihan di luar aksi user. |

---

## 7. Kebutuhan Antarmuka Eksternal

| Interface | Tipe | Detail |
|---|---|---|
| LRCLIB API | REST/HTTP, JSON | `GET /api/search`, `GET /api/get/{id}`, `GET /api/get`, tanpa API key |
| Spout (Resolume) | Local GPU texture share (SpoutGL) | Sender name dikonfigurasi user; frame RGBA |
| Filesystem | Baca/tulis JSON lokal | Library lagu, Show, Template, Settings |
| (Fase lanjut) OSC | UDP, protokol OSC | Untuk remote trigger next/prev/blank |
| (Fase lanjut) MIDI | MIDI over USB/virtual port | Untuk remote trigger dari foot controller |
| (Fase lanjut) NDI | Network video | Alternatif Spout untuk setup multi-mesin |

---

## 8. Arsitektur Modul (Target, Lanjutan dari Baseline)

```
lyric-spout-resolume/
├── main.py                 # entry point
├── app.py                  # QMainWindow: status strip + tabs
│
│   # --- inti, bebas GUI & bebas Spout (testable di OS mana pun) ---
├── lrclib_client.py        # (ada) integrasi LRCLIB
├── lrc_parser.py           # (ada) parsing & pencarian baris
├── player_state.py         # (ada) state playback + lines_version
├── render_style.py         # BARU v0.3: RenderStyle + .scaled()
├── scroll_anim.py          # BARU v0.3: ScrollAnimator (posisi + easing)
│
│   # --- render & output ---
├── spout_output.py         # MultiLineLyricRenderer + SpoutOutputThread
│
├── store/                  # BARU: persistence (bukan folder data file!)
│   ├── library.py          # CRUD Song
│   ├── shows.py            # CRUD Show/Set list
│   ├── templates.py        # CRUD Template/style
│   └── settings.py         # CRUD Settings
├── ui/                     # PySide6, satu file per layar mockup
│   ├── theme.py            # BARU v0.3: design token → QSS
│   ├── preview.py          # BARU v0.3: widget preview (REQ-F-OUT-08)
│   ├── live_view.py        # Screen 01
│   ├── library_view.py     # Screen 02
│   ├── lyric_editor.py     # Screen 03
│   ├── style_view.py       # Screen 04
│   ├── settings_view.py    # Screen 05
│   └── operator_view.py    # Screen 06 (window kedua)
└── remote/
    ├── osc_listener.py     # (fase 5)
    └── midi_listener.py    # (fase 5)
```

**Prinsip ketergantungan (satu arah, tidak boleh dilanggar):**

```
ui/  ──→  store/  ──→  inti (player_state, render_style, scroll_anim, parser, client)
 └──────────────────→  spout_output  ──→  inti
```

- `store/*`, `remote/*`, dan seluruh modul inti **dilarang** meng-import
  `PySide6` maupun `SpoutGL` (REQ-NF-06/07).
- **Catatan penamaan (v0.3):** folder kode persistence dinamai `store/`,
  bukan `data/`, karena `data/` sudah dipakai §5.4 sebagai lokasi *file*
  JSON. Dua hal berbeda tidak boleh berbagi nama.
- **Lokasi file data pindah** dari `./data/` ke
  `%APPDATA%\CUEVO Lyrics\`, supaya tetap benar setelah aplikasi
  di-package jadi `.exe` (folder instalasi biasanya read-only). Nama
  folder ini sebelumnya `LyricSpout\` (nama produk lama); `migrate_legacy_data()`
  memindahkannya otomatis sekali saat startup, lihat §3.8.

---

## 9. Roadmap & Prioritas Pengerjaan

| Fase | Fokus | Requirement terkait |
|---|---|---|
| **Fase 0, Selesai** | MVP single-song, single-line, kontrol manual, output Spout | Baseline §3 |
| **Fase 0.5, Port UI & perbaikan renderer** ✅ *selesai & terverifikasi (v0.5)* | Tkinter → PySide6, perbaikan bug §3.1, `ScrollAnimator`/`RenderStyle` dipakai bersama, preview satu jalur render, search satu kolom | ADR-001, §3.1, REQ-F-OUT-08, REQ-F-LIB-01 |
| **Fase 1, Persistence & Lirik Manual** ✅ *selesai & terverifikasi (v0.4)* | Library lokal, editor lirik manual/impor `.lrc`, Settings tersimpan | REQ-F-LIB-03/04/05/06/07/08, REQ-F-CFG-01/02 |
| **Fase 2, Show/Set list** ✅ *selesai (v0.6)* | Susun & simpan playlist, navigasi next/prev lagu, mode next-line manual | REQ-F-SET-01…05, REQ-F-PLAY-04/05 |
| **Fase 3, Styling dari GUI** ✅ *selesai (v0.7)* | Panel pengaturan visual, Template tersimpan & reusable | REQ-F-STYLE-01/02/03, REQ-F-OUT-05 |
| **Fase 4, Operator Experience** ✅ *selesai (v0.8)* | Preview terpisah, hotkey global, pengaturan scroll dari GUI | REQ-F-OPS-01/02, REQ-F-PLAY-06/07, REQ-F-OUT-05 |
| **Fase 5, Remote & Interop** 🔶 *sebagian (v0.9)* | OSC & MIDI terpasang tapi **belum diuji dengan perangkat nyata** (§3.13); NDI dan multi-sender dievaluasi lalu ditunda dengan alasan tertulis | REQ-F-RC-01/02 terpasang · REQ-F-OUT-06/07 ditunda |

Rekomendasi urutan kerja di Claude Code: selesaikan Fase 1 & 2 dulu
(paling terasa manfaatnya untuk pemakaian nyata di lapangan, bisa
nyimpen lagu & bikin set list), baru masuk ke styling dan fitur
"ProPresenter-like" lain yang sifatnya penyempurnaan pengalaman.

---

## 10. Risiko & Isu Terbuka

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Spout hanya jalan di Windows | Development di mesin non-Windows tidak bisa full-test | Isolasi modul Spout (sudah dilakukan); pertimbangkan CI/manual test checklist khusus Windows |
| LRCLIB bisa berubah skema/limit sewaktu-waktu (masih "beta") | Fitur pencarian bisa rusak mendadak | Bungkus semua panggilan API dengan error handling jelas (sudah ada `LrcLibError`); tambahkan fallback ke library lokal |
| Ketergantungan font sistem (`arial.ttf`) | Tampilan tidak konsisten di semua Windows | Fase Styling: bundel font open-source default di dalam repo |
| Scope creep menuju "ProPresenter penuh" | Timeline molor, kompleksitas naik drastis | Tetap disiplin ke scope §1.2; modul baru (Bible, media, dsb.) eksplisit di luar scope kecuali direvisi dokumen ini |
| Isu trademark/branding kalau nama produk terlalu mirip ProPresenter | Potensi masalah hukum ringan | Pilih nama produk sendiri yang jelas berbeda; hindari klaim "compatible with ProPresenter" |
| **Status "selesai" ditulis untuk kode yang belum pernah dijalankan** (terbukti di §3.1) | Requirement dianggap beres padahal cacat; keputusan lanjutan dibangun di atas asumsi salah | Status hanya boleh naik ke ✅ setelah dijalankan. Pakai status antara: `implemented, unverified`. Semua item bertanda itu wajib diverifikasi di Windows sebelum Fase 3 |
| **Preview GUI dan output Spout berpotensi menyimpang** | Panel Style jadi tidak bisa dipercaya, operator menyetel sesuatu yang berbeda dari yang tayang | REQ-F-OUT-08: saat live, preview memakai buffer yang sama persis; tidak ada render kedua (§3.2) |
| **Operator memilih font kecil di panel Style (Fase 3)** | Font ≤20px jatuh ke sisi lambat Pillow (5× lebih mahal) → fps anjlok saat animasi, padahal status strip terlihat normal | Panel Style harus memperingatkan di bawah ~22px; ukur ulang §3.2 saat Fase 3 dikerjakan |
| **Headroom performa tinggal ~22%** | Penambahan efek visual apa pun bisa langsung menembus budget 33,3 ms | Setiap perubahan renderer wajib disertai pengukuran ulang, bukan perkiraan |

---

## 11. Kriteria Penerimaan Fase 1 (contoh, siap jadi task Claude Code)

Supaya dokumen ini langsung actionable, berikut contoh breakdown untuk
fase berikutnya:

- [x] `store/library.py`: `upsert()`, `get()`, `list_songs()`, `search()`,
      `delete()`, baca/tulis atomik ke `library.json`. *(folder dinamai
      `store/`, bukan `data/`, lihat §8)*
- [x] Editor Lirik Manual: textarea untuk tempel teks + tombol TAP
      (`Enter`) untuk menandai waktu baris berikutnya sambil lagu diputar
      di aplikasi lain, cara kerja software karaoke sederhana.
- [x] Import `.lrc` lokal dari file picker (multi-select), parse pakai
      `lrc_parser.py` yang sudah ada, parser tidak diubah, hanya
      *ditambah* `format_lrc()` untuk arah sebaliknya.
- [x] `Settings` disimpan ke `settings.json`, dibaca saat start-up
      (nama sender, resolusi, fps, path library).
- [x] Tombol eksplisit "Simpan ke library" di tab Library, dengan
      konfirmasi anti-timpa (REQ-F-LIB-08).

**Hasil verifikasi (dijalankan, bukan diasumsikan):**

| Yang diuji | Hasil |
|---|---|
| Roundtrip `Song` → JSON → `Song` | ✅ isi & timestamp utuh |
| `upsert()` dua kali dengan `lrclib_id` sama | ✅ 1 entri, bukan duplikat |
| Pencarian lokal `"fleetwood chain"` vs `"chain fleetwood"` | ✅ sama-sama ketemu |
| Geser semua timestamp −100s | ✅ ter-clamp ke 0.0, tidak negatif |
| `format_lrc()` pada 59.999s | ✅ jadi `[01:00.00]`, carry benar |
| `library.json` sengaja dirusak | ✅ app tetap jalan, pesan jelas, masih bisa menulis |
| Impor 2 file `.lrc` sekaligus | ✅ `Artis - Judul.lrc` terpecah otomatis |
| Tap-to-timestamp lalu simpan | ✅ tersimpan, muncul di library |
| Restart aplikasi | ✅ lagu & settings kembali seperti terakhir |

**Catatan verifikasi (diperbarui v0.9.3).** Output Spout ke Resolume yang
dulu tercantum di sini sebagai belum diverifikasi **sudah ditutup di v0.5**
(§3.2), dan BLANK ditutup di v0.7.1 (§3.3). Daftar yang masih terbuka
sekarang ada di satu tempat: **§3.13 Utang verifikasi**. Jangan menambah
catatan "belum diverifikasi" yang berdiri sendiri di bagian lain dokumen ini,
karena catatan semacam itu jadi kedaluwarsa tanpa ada yang menyadarinya,
persis seperti kalimat yang barusan diganti ini.

---

## 12. Lampiran: Glosarium Singkat ProPresenter (untuk konteks fitur)

Untuk referensi saat menerjemahkan fitur ke versi lite:

- **Playlist** → di sini disebut **Show/Set list**.
- **Slide** → di sini satu **baris lirik**.
- **Stage Display** → panel terpisah untuk operator, lihat REQ-F-OPS-*.
- **Clear/Blank** → REQ-F-PLAY-04.
- **Trigger via MIDI/remote** → REQ-F-RC-*.
- **Themes/Templates** → REQ-F-STYLE-02/03.

Semua padanan di atas adalah **kesamaan konsep tingkat fitur**, bukan
kesamaan implementasi/kode, sesuai catatan legal di §1.3.

---

## 13. Log Keputusan Arsitektur (ADR)

### ADR-001, Stack GUI: PySide6, bukan Tauri atau C#
**Tanggal:** 2026-08-31 · **Status:** Diterima

**Konteks.** Tkinter tidak menyediakan drag-reorder, color/font picker,
maupun panel padat yang dibutuhkan Screen 01/04 di mockup. Tiga kandidat
dievaluasi terhadap mockup, bukan terhadap preferensi.

**Temuan penentu.** Dari enam layar mockup, semua widget tersedia bawaan
di ketiga kandidat **kecuali satu**: preview yang menampilkan buffer RGBA
persis sama dengan yang dikirim ke Spout, 30 fps (REQ-F-OUT-08). Widget
itulah yang memutuskan.

| Kandidat | Jalur frame renderer → widget preview | Putusan |
|---|---|---|
| **PySide6** | `PIL.Image` → `QImage` → `QLabel`; satu proses, memori sama | ✅ **Dipakai** |
| C# WPF/Avalonia | Satu GPU surface melayani preview & Spout sekaligus | ⚠️ Cadangan |
| Tauri | Encode + IPC tiap frame ke WebView2 | ❌ Ditolak |

**Kenapa Tauri ditolak, kalah dua arah:**
1. *UI → Spout:* surface WebView2 tidak bisa di-capture jadi texture Spout,
   jadi tampilan HTML/CSS tidak bisa dijadikan output. Ini blocker
   arsitektural, bukan soal effort.
2. *Renderer → UI:* frame harus di-encode dan lewat IPC 30×/detik.

Artinya renderer terpisah tetap harus ditulis, **plus** bayar overhead, tanpa satu pun keunggulan web menyentuh bagian yang sulit.

**Konsekuensi.** Hanya `app.py` yang diganti; `lrclib_client`,
`lrc_parser`, `player_state` tidak disentuh. Semua modul inti tetap bebas
GUI (REQ-NF-06).

**Pemicu peninjauan ulang (ke C#), kondisi terukur, bukan selera:**
- Pillow terbukti tidak sanggup 30 fps di Windows (REQ-NF-01 gagal), **atau**
- aplikasi perlu didistribusikan sebagai `.exe` mandiri ke pengguna lain.

Mockup di `MOCKUP.html` sengaja tidak memakai idiom khas Qt, jadi tetap
berlaku 100% kalau pemicu di atas terjadi.

### ADR-002, Preview dan Spout wajib satu jalur render
**Tanggal:** 2026-08-31 · **Status:** Diterima

Menduplikasi logika animasi di GUI dan di thread Spout akan menyimpang
seiring waktu. Karena itu state machine posisi scroll diekstrak ke
`scroll_anim.ScrollAnimator` dan seluruh parameter visual ke
`render_style.RenderStyle`. Keduanya dipakai bersama oleh `SpoutOutputThread`
dan widget preview, perbedaannya **hanya** faktor skala resolusi lewat
`RenderStyle.scaled()`. Diformalkan sebagai REQ-F-OUT-08.

### ADR-003, Pencarian satu kolom query bebas
**Tanggal:** 2026-08-31 · **Status:** Diterima

Dua kolom (judul + artis) memaksa operator mengklasifikasikan input sebelum
mencari, dan salah taruh menghasilkan nol hasil. LRCLIB sudah menyediakan
parameter `q` untuk pencarian bebas, dan `lrclib_client.search()` sudah
mendukungnya sejak v0.1, jadi perubahan ini **nol biaya di sisi backend**.
Mendukung REQ-NF-05 (onboarding <2 menit).
