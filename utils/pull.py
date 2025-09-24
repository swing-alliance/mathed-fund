# pull.py
import os
import pandas as pd
import akshare as ak
from datetime import datetime

def fetch_and_save_fund_csv(codes, folder="found"):
    """
    根据基金代码列表拉取最新净值数据，并保存为 CSV 文件
    每个基金一个 CSV 文件，存储在 folder 中
    """
    os.makedirs(folder, exist_ok=True)
    saved_files = []  # 保存成功的文件路径
    for code in codes:
        try:
            # 拉取单位净值走势
            df_new = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            df_new['净值日期'] = pd.to_datetime(df_new['净值日期'])
            df_new = df_new.sort_values("净值日期").reset_index(drop=True)
            # CSV 文件路径
            csv_file = os.path.join(folder, f"{code}.csv")
            # 如果已有文件，读取旧数据并合并
            if os.path.exists(csv_file):
                df_old = pd.read_csv(csv_file, parse_dates=['净值日期'])
                df_combined = pd.concat([df_old, df_new]) \
                                .drop_duplicates(subset='净值日期') \
                                .sort_values("净值日期")
            else:
                df_combined = df_new
            # 保存 CSV
            df_combined.to_csv(csv_file, index=False, encoding="utf-8-sig")
            saved_files.append(csv_file)
            print(f"[成功] {code} 已保存: {csv_file}")
        except Exception as e:
            print(f"[失败] {code} 拉取失败: {e}")
    return saved_files

# ----------------- 测试用例 -----------------
if __name__ == "__main__":
    # 例如从 QDialog 获取的 codes
    codes = ["161725", "001234"]
    fetch_and_save_fund_csv(codes)
