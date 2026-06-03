# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['os', 'sys', 'configparser', 'pandas', 'socket', 'PyQt5.QtGui', 'openpyxl', 'importlib', 'importlib.util', 'io', 'json', 'requests', 'csv', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'datetime', 'time', 'serial', 'contextlib', 'serial.tools.list_ports', 'threading', 'can', 'can.message', 'can.interfaces.pcan', 'Crypto.Cipher.AES']
hiddenimports += collect_submodules('can')


a = Analysis(
    ['TVS_NIRIX_Orbiter_RVS.py'],
    pathex=[],
    binaries=[],
    datas=[('Orbiter_RVS/*.pyd', 'Orbiter_RVS'), ('fail picture.png', '.'), ('Pass picture.png', '.'), ('TVS logo white.png', '.'), ('Nirix Logo.png', '.'), ('log_cleanup.py', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tensorflow', 'sklearn', 'nltk', 'torch', 'torchvision'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TVS_NIRIX',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TVS_NIRIX',
)
