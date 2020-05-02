# -*- mode: python -*-

block_cipher = None


a = Analysis(['nparse.py'],
             pathex=['./'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher
)
from glob import glob
a.datas += [(filename, filename, '.') for filename in glob('data/fonts/*')]
a.datas += [('data/ui/icon.png', 'data/ui/icon.png', '.')]
a.datas += [('data/ui/folder.png', 'data/ui/folder.png', '.')]
a.datas += [('data/ui/settings.ui', 'data/ui/settings.ui', '.')]
a.datas += [('data/ui/triggereditor.ui', 'data/ui/triggereditor.ui', '.')]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='nparse',
          debug=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=False,
          icon='data/ui/icon.ico'
          )
