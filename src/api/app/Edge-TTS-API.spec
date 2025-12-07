# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# 收集所有子模块
hiddenimports = [
    'pkg_resources.py2_warn',
    'xml.parsers.expat',
    'xml.parsers.pyexpat',
    'xml.parsers',
    'edge_tts',
    'flask',
    'gevent',
    'gevent.pywsgi',
    'dotenv',
    'python-dotenv',
    'asyncio',
    'subprocess',
    'tempfile',
    'pkg_resources',
]

# 收集子模块（如果可用）
try:
    hiddenimports += collect_submodules('edge_tts')
    hiddenimports += collect_submodules('flask')
    hiddenimports += collect_submodules('gevent')
except:
    pass

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[('index.html', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Edge-TTS-API',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

