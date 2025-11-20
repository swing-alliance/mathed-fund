from PyInstaller.utils.hooks import collect_all

# 这会尝试收集 akshare 所有的 Python 模块、非 Python文件和二进制依赖
# 目标：解决各种路径问题
datas, binaries, hiddenimports = collect_all('akshare')