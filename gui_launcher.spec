# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['desktop_agent.py'],
    pathex=[],
    binaries=[],
    datas=[('static', 'static'), ('templates', 'templates')],
    hiddenimports=[
        'webview', 'uvicorn', 'qrcode', 'qrcode.image.pil', 'PIL',
        'pystray', 'pystray._win32', 'comtypes',
    ] + collect_submodules('pystray'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='PCController',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
