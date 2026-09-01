"""
Lapisan persistence.

Modul di folder ini DILARANG meng-import PySide6 maupun SpoutGL, supaya
tetap bisa diuji di OS mana pun (SRS REQ-NF-06/07).

Catatan penamaan: folder ini bernama `store/`, bukan `data/`, karena
SRS §5.4 sudah memakai `data/` sebagai lokasi *file* JSON. Dua hal berbeda
tidak boleh berbagi nama.
"""
