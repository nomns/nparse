# -*- mode: python -*-

block_cipher = None

from glob import glob
import os
data = [(filename, os.path.dirname(filename)) for filename in glob('data\\fonts\\*')]
data += [('data\\ui\\_.css', 'data\\ui\\')]
data += [('data\\ui\\icon.png', 'data\\ui\\')]

from PyInstaller.utils.hooks import copy_metadata
data += copy_metadata('colorhash')

a = Analysis(
    ['nparse.py'],
    pathex=[],
    binaries=[],
    datas=data,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)


pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

splash = Splash(
    'splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(10, 388),
    text_size=13,
    text_color='#666666',
    minify_script=True,
    always_on_top=False,
    max_img_size=(800, 400),
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
