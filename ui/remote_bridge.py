"""
Jembatan antara listener remote (OSC/MIDI) dan thread GUI.

`OscListener` memanggil handler-nya dari thread socket. Menyentuh widget Qt
dari thread selain thread GUI adalah undefined behaviour -- bisa crash,
bisa juga diam-diam salah tanpa gejala sampai suatu saat di tengah acara.

Kelas ini memancarkan signal Qt dari thread socket; Qt otomatis meng-queue
signal lintas-thread sehingga slot-nya dieksekusi di thread GUI. Pola yang
sama sudah dipakai untuk pencarian LRCLIB (`_SearchBridge`).

Perintah yang ditangani sengaja dipetakan di satu tempat (`dispatch`),
supaya OSC dan MIDI nanti berbagi daftar aksi yang sama persis.
"""
from PySide6.QtCore import QObject, Signal


class RemoteBridge(QObject):
    commandReceived = Signal(str, object)   # (nama_perintah, args)
    activitySeen = Signal(str)              # alamat OSC apa pun, untuk indikator

    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions = {}

    def set_actions(self, actions: dict):
        """actions: {nama_perintah: callable(args)}"""
        self._actions = actions

    # --- dipanggil DARI THREAD LISTENER ---

    def emit_command(self, command, args):
        self.commandReceived.emit(command, args)

    def emit_activity(self, address, args):
        self.activitySeen.emit(address)

    # --- dieksekusi DI THREAD GUI ---

    def dispatch(self, command, args):
        action = self._actions.get(command)
        if action is None:
            return
        action(args or [])
