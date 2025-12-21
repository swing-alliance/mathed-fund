# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import glob

# 1. 获取当前脚本所在目录的绝对路径，确保路径在任何位置运行都一致
# 使用 os.path.abspath(os.getcwd()) 可能随执行路径改变，这里建议使用脚本所在目录
current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
target_dir = os.path.join(current_dir, 'static')

# 自动查找图标
pics = glob.glob(os.path.join(target_dir, 'infinite.png'))
if not pics:
    # 如果没找到，建议给一个默认提示，或者手动指定一个 ico 路径
    icon_path = None 
else:
    icon_path = os.path.abspath(pics[0])

# ---------- 外部依赖路径 ----------
# 请确保这两个路径在你的电脑上是正确的
AKSHARE_FILE_FOLD_SRC = r'A:\projects\money2\venv\Lib\site-packages\akshare\file_fold'
MINI_RACER_DLL_SRC = r'A:\projects\money2\venv\Lib\site-packages\py_mini_racer\mini_racer.dll'

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[
        (MINI_RACER_DLL_SRC, '.'),
    ],
    datas=[
        (AKSHARE_FILE_FOLD_SRC, 'akshare/file_fold'),
        # 核心修复：必须将 static 文件夹打包进去，否则程序运行时无法加载图标
        (target_dir, 'static'), 
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
    name='FindOutFund',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为 False，运行无黑窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 此处的 icon 决定 .exe 文件在资源管理器中的图标
    icon=icon_path if icon_path else None
)