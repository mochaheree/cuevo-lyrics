# design

Berkas sumber, **tidak ikut dibundel** ke .exe.

`assets/` isinya cuma yang benar-benar dibaca aplikasi saat jalan, karena
`CUEVO Lyrics.spec` menyalin seluruh isi `assets/` ke dalam build. Menaruh
file sumber di sana membuat .exe membesar tanpa guna.

| File | Dipakai untuk |
|---|---|
| `cuevo_desktop_icons_bigger.zip` | Sumber ikon. Varian `squircle-badge` yang dipakai. `assets/app-icon.ico` dibangun ulang dari PNG di dalamnya, karena `app-icon.ico` bawaan zip cuma berisi 16x16 dan Windows butuh sampai 256. |
| `qris_poster.png` | Poster QRIS utuh. `assets/qris.png` adalah potongan kode QR-nya saja, supaya cukup besar untuk dipindai dari layar. |
