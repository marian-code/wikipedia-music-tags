# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['gui_Qt.py'],
             pathex=['C:\\Users\\Marián Rynik\\OneDrive\\Dokumenty\\Visual Studio 2017\\Projects\\Python\\wiki_music'],
             binaries=[],
             datas=[],
             hiddenimports=['os'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=True)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [('v', None, 'OPTION')],
          exclude_binaries=True,
          name='gui_Qt',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='gui_Qt')
