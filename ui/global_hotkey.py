"""
Hotkey global system-wide (REQ-F-PLAY-07, prioritas Could).

Berbeda dari hotkey biasa di `app.py` yang hanya jalan saat window CUEVO
Lyrics sedang fokus, yang ini tetap jalan walau operator sedang di
Resolume, Spotify, atau aplikasi lain.

Dipakai lewat Win32 `RegisterHotKey` + `QAbstractNativeEventFilter`, bukan
library pihak ketiga: tidak menambah dependency, tidak butuh hak admin,
dan tidak memasang keyboard hook global (yang sering ditandai antivirus
dan menangkap SEMUA ketikan -- termasuk password orang).

KENAPA PAKAI MODIFIER (Ctrl+Alt+...), BUKAN Space/B POLOS
---------------------------------------------------------
Hotkey global bersifat eksklusif se-sistem: aplikasi lain tidak akan
menerima tombol itu lagi selama terdaftar. Mendaftarkan `Space` polos
secara global akan **mematikan tombol spasi di seluruh Windows** -- tidak
bisa mengetik spasi di mana pun. Makanya kombinasi di sini selalu memakai
Ctrl+Alt, dan sengaja berbeda dari hotkey dalam-window.

Modul ini Windows-only. Di OS lain `install()` mengembalikan pesan
kegagalan yang jelas, bukan crash (REQ-NF-06).
"""
import sys

from PySide6.QtCore import QAbstractNativeEventFilter

WM_HOTKEY = 0x0312

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

VK_SPACE = 0x20
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_B = 0x42

# Ctrl+Alt dipilih karena jarang dipakai aplikasi lain, dan MOD_NOREPEAT
# supaya menahan tombol tidak memicu aksi berulang-ulang.
_BASE = MOD_CONTROL | MOD_ALT | MOD_NOREPEAT

DEFAULT_BINDINGS = [
    ("play_pause", _BASE, VK_SPACE, "Ctrl+Alt+Space"),
    ("prev_line", _BASE, VK_LEFT, "Ctrl+Alt+←"),
    ("next_line", _BASE, VK_RIGHT, "Ctrl+Alt+→"),
    ("blank", _BASE, VK_B, "Ctrl+Alt+B"),
]


def is_supported() -> bool:
    return sys.platform == "win32"


class GlobalHotkeys(QAbstractNativeEventFilter):
    """
    Pemakaian:
        hk = GlobalHotkeys()
        ok, problems = hk.install(window, {"play_pause": fn, ...})
        ...
        hk.uninstall()

    `install()` mengembalikan (berhasil_sebagian, daftar_pesan_gagal).
    Kombinasi yang sudah dipakai aplikasi lain akan gagal didaftarkan --
    itu dilaporkan, bukan didiamkan. Diam-diam gagal berarti operator
    menekan tombol saat live dan tidak terjadi apa-apa tanpa penjelasan.
    """

    def __init__(self):
        super().__init__()
        self._actions = {}      # hotkey id -> callable
        self._labels = {}       # hotkey id -> label untuk pesan error
        self._installed = False
        self._app = None
        self._hwnd = None

    # ---------- pasang / lepas ----------

    def install(self, window, callbacks: dict):
        if not is_supported():
            return False, ["Hotkey global hanya tersedia di Windows."]
        if self._installed:
            return True, []

        import ctypes
        from PySide6.QtWidgets import QApplication

        user32 = ctypes.windll.user32
        hwnd = int(window.winId())

        problems = []
        registered_any = False
        for index, (name, modifiers, vk, label) in enumerate(DEFAULT_BINDINGS, start=1):
            callback = callbacks.get(name)
            if callback is None:
                continue
            if user32.RegisterHotKey(hwnd, index, modifiers, vk):
                self._actions[index] = callback
                self._labels[index] = label
                registered_any = True
            else:
                problems.append(f"{label} sedang dipakai aplikasi lain")

        if registered_any:
            self._app = QApplication.instance()
            self._app.installNativeEventFilter(self)
            self._hwnd = hwnd
            self._installed = True
        return registered_any, problems

    def uninstall(self):
        if not self._installed:
            return
        import ctypes
        user32 = ctypes.windll.user32
        for hotkey_id in list(self._actions):
            user32.UnregisterHotKey(self._hwnd, hotkey_id)
        if self._app is not None:
            self._app.removeNativeEventFilter(self)
        self._actions.clear()
        self._labels.clear()
        self._installed = False
        self._app = None
        self._hwnd = None

    @property
    def active(self) -> bool:
        return self._installed

    def labels(self):
        return [label for _, _, _, label in DEFAULT_BINDINGS]

    # ---------- penerima pesan Windows ----------

    def nativeEventFilter(self, event_type, message):
        if not self._actions:
            return False, 0
        try:
            import ctypes
            import ctypes.wintypes
            msg = ctypes.wintypes.MSG.from_address(int(message))
        except (TypeError, ValueError, OSError):
            return False, 0

        if msg.message == WM_HOTKEY:
            callback = self._actions.get(int(msg.wParam))
            if callback is not None:
                callback()
                return True, 0
        return False, 0
