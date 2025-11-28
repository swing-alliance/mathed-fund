# -*- mode: python ; coding: utf-8 -*-

# 引入 os 模块用于路径操作
import os

# -------------------------------------------------------------------------------------
# ⚠️ 1. 关键路径定义 (已根据您的信息确认)
AKSHARE_FILE_FOLD_SRC = 'A:\\projects\\money2\\venv\\Lib\\site-packages\\akshare\\file_fold' 
MINI_RACER_DLL_SRC = 'A:\\projects\\money2\\venv\\Lib\\site-packages\\py_mini_racer\\mini_racer.dll'
# 注意：如果您的 venv 路径是 A:\projects\money2\venv，则 DLL 路径应该是
# MINI_RACER_DLL_SRC = 'A:\\projects\\money2\\venv\\Lib\\site-packages\\py_mini_racer\\mini_racer.dll'
# -------------------------------------------------------------------------------------

a = Analysis(
    ['main.py'],
    pathex=[],
    
    # 🌟 关键修复 1: 强制包含 mini_racer.dll
    binaries=[
        # (源 DLL 路径, 目标路径)
        # 将 DLL 目标路径设置为 '.'，确保它被解压到临时目录的根部
        (MINI_RACER_DLL_SRC, '.'), 
    ],
    
    # ⚠️ 关键修复 2: 在 datas 列表中添加 akshare 资源文件映射
    datas=[
        (AKSHARE_FILE_FOLD_SRC, 'akshare/file_fold'),
    ],
    
    # 恢复 akshare 的隐藏导入（如果 hookspath 未使用或 hook 不完整）
    hiddenimports=['akshare', 'akshare.utils', 'akshare.pro'],
    
    # 如果您使用了自定义 Hook 文件 (./hooks/hook-akshare.py)，请保持 hookspath
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
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    
    # 保持 console=True 以便查看 mini_racer 的错误信息
    console=False, 
    
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)