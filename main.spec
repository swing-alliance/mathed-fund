import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# ================== 路径配置（按你的实际路径修改） ==================
py_mini_path = r"A:\projects\money2\venv\Lib\site-packages\py_mini_racer"
calendar_path = r"A:\projects\money2\venv\Lib\site-packages\akshare\file_fold"
icon_path = r"C:\Users\zhou\Desktop\fund\static\infinite.png"

# 自动收集 py_mini_racer 的所有数据文件和动态库
py_mini_datas = collect_data_files('py_mini_racer')
py_mini_binaries = collect_dynamic_libs('py_mini_racer')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # 1. 自动收集的所有动态库（主要是 mini_racer.dll）
        *py_mini_binaries,

        # 2. 手动把关键文件同时放到两个位置（强烈推荐，双保险）
        (os.path.join(py_mini_path, 'mini_racer.dll'), 'py_mini_racer'),   # 包内
        (os.path.join(py_mini_path, 'mini_racer.dll'), '.'),               # 根目录

        (os.path.join(py_mini_path, 'icudtl.dat'), 'py_mini_racer'),       # 包内
        (os.path.join(py_mini_path, 'icudtl.dat'), '.'),                   # 根目录 ← 解决你报错的关键！

        (os.path.join(py_mini_path, 'snapshot_blob.bin'), 'py_mini_racer'),# 包内
        (os.path.join(py_mini_path, 'snapshot_blob.bin'), '.'),            # 根目录
    ],
    datas=[
        # 自动收集 py_mini_racer 的所有数据文件（保险起见）
        *py_mini_datas,

        # akshare 的 calendar.json
        (os.path.join(calendar_path, 'calendar.json'), 'akshare\\file_fold'),
    ],
    hiddenimports=[
        'py_mini_racer',
    ],
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
    console=False,                    # 如果想隐藏控制台窗口，改成 False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)