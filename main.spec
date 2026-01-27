# -*- mode: python ; coding: utf-8 -*-
import os
import akshare
import py_mini_racer

# 获取路径
akshare_path = os.path.dirname(akshare.__file__)
pmr_path = os.path.dirname(py_mini_racer.__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # 不要用 *.pyd，直接把整个目录放进去，PyInstaller 会自动处理里面的二进制文件
        (pmr_path, 'py_mini_racer'),
    ],
    datas=[
        # Akshare 资源
        (os.path.join(akshare_path, 'file_fold'), 'akshare/file_fold'),
        # 静态资源
        (r'C:\Users\zhou\Desktop\copym2\static', 'static'),
    ],
    hiddenimports=['py_mini_racer', 'pandas._libs.tslibs.np_datetime'],
    hookspath=[],
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
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, 
    console=False, 
    icon=[r'C:\Users\zhou\Desktop\copym2\static\infinite.png'],
)