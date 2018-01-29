# -*- mode: python -*-

block_cipher = None


a = Analysis(['nparse.py'],
             pathex=['D:\\nomns.github.com\\nparse'],
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
a.datas += [('data/ui/_.css', 'data/ui/_.css', '.')]
a.datas += [('data/ui/icon.png', 'data/ui/icon.png', '.')]
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
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='data/ui/icon.ico'
          )
