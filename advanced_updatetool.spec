# -*- mode: python ; coding: utf-8 -*-

import os
import glob
import sys

# ==================== 项目根目录 ====================
project_root = os.getcwd()                                     # 例如 A:\projects\money2
static_dir   = os.path.join(project_root, 'static')

# ==================== 自动找图标（static 里第一个 png） ====================
png_files = glob.glob(os.path.join(static_dir, '*.png'))
if not png_files:
    raise FileNotFoundError("static 目录下没有找到 .png 图标文件！请放一张图标进去")
for i, item in enumerate(png_files):
    if "premium" in item:
        icon_path = png_files[i]


# ==================== 需要额外打包的资源 ====================
# 1. akshare 的文件缓存目录
AKSHARE_SRC = r'A:\projects\money2\venv\Lib\site-packages\akshare\file_fold'

# 2. py_mini_racer 的 dll（必须）
MINI_RACER_DLL = r'A:\projects\money2\venv\Lib\site-packages\py_mini_racer\mini_racer.dll'

# 3. 如果你想运行时还能读取 static 里的图片、配置文件等（强烈建议加上）
STATIC_DATA = (static_dir, 'static')


block_cipher = None

a = Analysis(
    ['advanced_updatetool.py'],           # ←←←← 这里改成你的更新器入口文件名！！！
    pathex=[],
    binaries=[
        (MINI_RACER_DLL, '.'),            # 直接扔到程序根目录
    ],
    datas=[
        (AKSHARE_SRC, 'akshare/file_fold'),
        STATIC_DATA,                       # 把整个 static 文件夹带上，运行时可用
        # 如果还有其他资源，继续在这里加就行
    ],
    hiddenimports=[
        'akshare',
        'akshare.utils',
        'akshare.pro',
        'py_mini_racer._mini_racer',
    ],
    hookspath=['./hooks'],                 # 你原来的 hooks 目录保留
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
    name='advanced_updatetool',           # 最终 exe 名字
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                              # 有 UPX 就压缩，没装就自动跳过
    upx_exclude=['vcruntime140.dll', 'python311.dll'],
    runtime_tmpdir=None,
    console=True,                         # 正式版关闭黑窗（调试时改 True）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path                         # 自动使用 static 里的第一个 png，绝不加逗号！
)