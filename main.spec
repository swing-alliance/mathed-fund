# -*- mode: python ; coding: utf-8 -*-
#按照实际所在位置修改这两个路径！！！，不然会非常麻烦
py_mini_path = r"C:\Users\zhou\Desktop\copym2\venv\Lib\site-packages\py_mini_racer"
calendar_path = r"C:\Users\zhou\Desktop\copym2\venv\Lib\site-packages\akshare\file_fold"

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # 添加 mini_racer.dll（注意目标路径用 '.' 表示 exe 根目录）
        (os.path.join(py_mini_path, 'mini_racer.dll'), '.'),
    ],
    datas=[
        # 添加 calendar.json，目标路径必须是 akshare\file_fold
        (os.path.join(calendar_path, 'calendar.json'), 'akshare\\file_fold'),
    ],
    hiddenimports=[],
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
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,               # 保持带控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)