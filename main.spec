# -*- mode: python ; coding: utf-8 -*-

import os
import glob

# ---------- 自动查找 static 目录下的第一个 png 当作图标 ----------
current_dir = os.getcwd()
target_dir = os.path.join(current_dir, 'static')
pics = glob.glob(os.path.join(target_dir, '*.png'))

if not pics:
    raise FileNotFoundError("static 目录下没有找到任何 .png 图标文件！")
icon_path = pics[0]          # 取第一个 png

# ---------- akshare 和 mini_racer 需要额外打包的文件 ----------
AKSHARE_FILE_FOLD_SRC = r'A:\projects\money2\venv\Lib\site-packages\akshare\file_fold'
MINI_RACER_DLL_SRC = r'A:\projects\money2\venv\Lib\site-packages\py_mini_racer\mini_racer.dll'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        (MINI_RACER_DLL_SRC, '.'),
    ],
    datas=[
        (AKSHARE_FILE_FOLD_SRC, 'akshare/file_fold'),
        # 如果你还想把 static 文件夹整个带上（运行时可以用图片），取消下一行注释
        # (os.path.join(current_dir, 'static'), 'static'),
    ],
    hiddenimports=['akshare', 'akshare.utils', 'akshare.pro'],
    hookspath=['./hooks'],
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
    name='main',
    debug=False,                    # 正式打包建议 False
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                  # 无黑窗
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path                  # 正确写法：直接是字符串，不是列表！
)