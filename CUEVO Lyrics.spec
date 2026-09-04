# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('assets', 'assets')]   # gambar QR donasi ikut dibundel;
                                 # tanpa ini QR hilang di build .exe
binaries = []
hiddenimports = ['pygame', 'OpenGL', 'rtmidi']
tmp_ret = collect_all('SpoutGL')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
# collect_all('PySide6') SENGAJA TIDAK DIPAKAI. Perintah itu menarik seluruh
# modul Qt (WebEngine, 3D, Charts, Quick, Designer, semua terjemahan) dan
# membuat hasil build jadi 708 MB, padahal aplikasi ini cuma meng-import
# QtCore, QtGui, dan QtWidgets. Hook bawaan PyInstaller sudah mengambil
# yang benar-benar di-import saja.
excludes = [
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineQuick', 'PySide6.QtWebChannel', 'PySide6.QtWebSockets',
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuick3D',
    'PySide6.QtQuickWidgets', 'PySide6.QtQuickControls2',
    'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput',
    'PySide6.Qt3DLogic', 'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras',
    'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'PySide6.QtGraphs',
    'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'PySide6.QtDesigner', 'PySide6.QtUiTools', 'PySide6.QtHelp',
    'PySide6.QtSql', 'PySide6.QtTest', 'PySide6.QtBluetooth',
    'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtLocation',
    'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtSensors',
    'PySide6.QtSerialPort', 'PySide6.QtSerialBus', 'PySide6.QtSpatialAudio',
    'PySide6.QtStateMachine', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets', 'PySide6.QtSvgWidgets',
    'PySide6.QtHttpServer', 'PySide6.QtNetworkAuth',
    # Bukan Qt, tapi ikut terseret dan tidak dipakai satu baris pun
    'tkinter', 'unittest', 'pydoc_data', 'test',
]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CUEVO Lyrics',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app-icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CUEVO Lyrics',
)
