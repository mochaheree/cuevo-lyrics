"""
Penerima trigger MIDI -- REQ-F-RC-02.

Untuk foot controller, pad controller, atau apa pun yang mengirim Note On /
Control Change. Aksinya persis sama dengan OSC; yang berbeda cuma jalurnya.

`python-rtmidi` bersifat opsional: kalau belum terpasang, `MIDI_AVAILABLE`
False dan tab Settings menonaktifkan kontrolnya dengan keterangan --
aplikasi tetap jalan penuh (pola yang sama dengan SpoutGL).

Tidak meng-import PySide6 (REQ-NF-06). Callback dipanggil dari thread
internal rtmidi, jadi pemanggil WAJIB menjembatani ke thread GUI --
lihat catatan di remote/osc_listener.py.
"""
import threading

try:
    import rtmidi
    MIDI_AVAILABLE = True
except ImportError:
    MIDI_AVAILABLE = False

NOTE_ON = 0x90
NOTE_OFF = 0x80
CONTROL_CHANGE = 0xB0

# Peta default: note number -> perintah.
#
# Dipilih di oktaf C3-B3 (48-59) karena itu rentang yang dipakai kebanyakan
# foot controller murah dan pad kiri Launchpad/APC -- jadi kemungkinan besar
# langsung cocok tanpa perlu di-remap.
DEFAULT_NOTE_MAP = {
    48: "play_pause",
    49: "prev_line",
    50: "next_line",
    51: "blank_toggle",
    52: "prev_song",
    53: "next_song",
}


def note_map_help():
    return [(note, command) for note, command in sorted(DEFAULT_NOTE_MAP.items())]


def available_ports():
    """Nama port MIDI input yang terdeteksi. List kosong kalau tidak ada."""
    if not MIDI_AVAILABLE:
        return []
    try:
        probe = rtmidi.MidiIn()
        names = list(probe.get_ports())
        del probe
        return names
    except Exception:
        return []


class MidiListener:
    """
    Pemakaian:
        listener = MidiListener(port_index, on_command)
        ok, error = listener.start_listening()
        ...
        listener.stop()

    rtmidi memanggil callback dari thread-nya sendiri.
    """

    def __init__(self, port_index=0, on_command=None, on_activity=None,
                 note_map=None):
        self.port_index = port_index
        self.on_command = on_command
        self.on_activity = on_activity
        self.note_map = dict(note_map or DEFAULT_NOTE_MAP)
        self.status = "not started"
        self.port_name = None
        self._midi_in = None
        self._lock = threading.Lock()

    def start_listening(self):
        if not MIDI_AVAILABLE:
            self.status = "python-rtmidi not installed"
            return False, "python-rtmidi not installed (pip install python-rtmidi)"
        try:
            self._midi_in = rtmidi.MidiIn()
            ports = self._midi_in.get_ports()
            if not ports:
                self._midi_in = None
                self.status = "no MIDI device"
                return False, "no MIDI device detected"
            if not (0 <= self.port_index < len(ports)):
                self.port_index = 0
            self._midi_in.open_port(self.port_index)
            self.port_name = ports[self.port_index]
            # abaikan pesan yang tidak dipakai supaya callback tidak dibanjiri
            # clock (0xF8) yang datang 24x per beat dari device apa pun
            self._midi_in.ignore_types(sysex=True, timing=True, active_sense=True)
            self._midi_in.set_callback(self._on_midi)
        except Exception as exc:
            self._midi_in = None
            self.status = f"failed: {exc}"
            return False, str(exc)

        self.status = f"listening: {self.port_name}"
        return True, None

    def stop(self):
        with self._lock:
            if self._midi_in is not None:
                try:
                    self._midi_in.cancel_callback()
                    self._midi_in.close_port()
                except Exception:
                    pass
                self._midi_in = None
        self.status = "stopped"

    # --- dipanggil DARI THREAD rtmidi ---

    def _on_midi(self, event, data=None):
        message, _delta = event
        if len(message) < 3:
            return
        status, number, velocity = message[0], message[1], message[2]
        kind = status & 0xF0

        if self.on_activity is not None:
            self.on_activity(f"{kind:#04x} n{number} v{velocity}", [])

        # Note On dengan velocity 0 sebenarnya Note Off -- konvensi MIDI yang
        # dipakai hampir semua device. Kalau tidak ditangani, satu injakan
        # pedal memicu aksi DUA KALI (masalah yang sama dengan tombol-dilepas
        # di OSC, lihat is_release di osc_listener.py).
        if kind == NOTE_OFF or (kind == NOTE_ON and velocity == 0):
            return
        if kind == NOTE_ON:
            command = self.note_map.get(number)
        elif kind == CONTROL_CHANGE:
            command = self.note_map.get(number) if velocity > 0 else None
        else:
            return

        if command and self.on_command is not None:
            self.on_command(command, [])
