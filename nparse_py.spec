# -*- mode: python -*-

block_cipher = None


a = Analysis(
    ['nparse.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

from glob import glob
a.datas += [(filename, filename, '.') for filename in glob('data/fonts/*')]
a.datas += [('data/ui/_.css', 'data/ui/_.css', '.')]
a.datas += [('data/ui/icon.png', 'data/ui/icon.png', '.')]
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

splash = Splash(
    'splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(5, 20),
    text_size=12,
    text_color='black',
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash,
    splash.binaries,
    name='nparse',
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
    icon='data/ui/icon.ico'
)
