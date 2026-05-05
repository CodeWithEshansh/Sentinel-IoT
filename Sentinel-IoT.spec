# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ai/anomaly_model.pkl', 'ai'),
        ('ai/scaler.pkl', 'ai'),
    ],
    hiddenimports=['ai.ai_server', 'server.app', 'device_simulator', 'device.device', 'sklearn', 'sklearn.ensemble._iforest', 'sklearn.tree._utils'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Sentinel-IoT',
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
    icon=['Sentinel.ico'],
)
