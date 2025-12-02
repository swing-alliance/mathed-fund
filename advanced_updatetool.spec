# -*- mode: python ; coding: utf-8 -*-

# 引入 os 模块用于路径操作
import os
# 确保在运行 PyInstaller 命令时，你处于项目的根目录，
# 这样相对路径('./hooks')才能正确找到。

# -------------------------------------------------------------------------------------
# ⚠️ 1. 关键路径定义
# 请根据你实际的虚拟环境（venv）或 Python 安装路径来更新这两个路径！
# -------------------------------------------------------------------------------------

# A. AkShare 资源文件路径 (file_fold 文件夹)
# 假设你的环境路径是 A:\projects\money2\venv
AKSHARE_FILE_FOLD_SRC = 'A:\\projects\\money2\\venv\\Lib\\site-packages\\akshare\\file_fold' 

# B. py_mini_racer DLL 路径 (mini_racer.dll)
MINI_RACER_DLL_SRC = 'A:\\projects\\money2\\venv\\Lib\\site-packages\\py_mini_racer\\mini_racer.dll'

# -------------------------------------------------------------------------------------

block_cipher = None

a = Analysis(
    # 🌟 将 'main.py' 替换为你的脚本名
    ['advanced_updatetool.py'],
    pathex=[],
    
    # 🌟 关键修复 1: 强制包含 mini_racer.dll
    # (源 DLL 路径, 目标路径) -> 目标路径 '.' 确保它在执行时的临时目录根部
    binaries=[
        (MINI_RACER_DLL_SRC, '.'), 
    ],
    
    # ⚠️ 关键修复 2: 在 datas 列表中添加 akshare 资源文件映射
    # (源文件夹路径, 目标文件夹名) -> 目标文件夹名 'akshare/file_fold'
    datas=[
        (AKSHARE_FILE_FOLD_SRC, 'akshare/file_fold'),
    ],
    
    # 恢复 akshare 的隐藏导入，增强兼容性
    hiddenimports=['akshare', 'akshare.utils', 'akshare.pro', 'pandas'], # 额外加上 pandas 避免它也被漏掉
    
    # 如果你创建了自定义 Hook 文件 (./hooks/hook-akshare.py)，请保持 hookspath
    # 如果没有自定义 Hook 文件，可以删除这行
    hookspath=['./hooks'], 
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles, # 使用 a.zipfiles 和 a.datas 是推荐做法
    a.datas,
    [],
    # 🌟 将 name 改为你的程序名
    name='advanced_updatetool',
    debug=False, # 部署时建议改为 False
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    
    # 如果你的程序是命令行工具，建议使用 console=True
    # 如果是 GUI 程序，使用 console=False (或 windows=True)
    console=False, 
    
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)