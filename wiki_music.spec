# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['wiki_music\\app_gui.py'],
             pathex=['.', '.'],
             binaries=[],
             datas=[('wiki_music\\files', 'files'), ('wiki_music\\icons', 'icons'), ('wiki_music\\data', 'data'), ('wiki_music\\ui', 'ui')],
             hiddenimports=[],
             hookspath=['hooks'],
             runtime_hooks=['rhooks\\pyi_rth_nltk.py'],
             excludes=['tcl', 'tk', 'setuptools', 'pydoc_data', 'pkg_resources', 'lib2to3', 'tkinter', 'multiprocessing', 'concurrent', 'xmlrpc', 'pywin', 'Include', 'curses'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='wiki_music',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False , icon='wiki_music\\files\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=['vcruntime140.dll', 'msvcp140.dll', 'qwindows.dll', 'qwindowsvistastyle.dll'],
               name='wiki_music')
