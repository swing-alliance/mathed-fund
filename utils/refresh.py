# pull_all.py
import os
import pandas as pd
import akshare as ak

def update_found_folder(folder="found"):
    """
    扫描 found 下所有六位数字 CSV 文件，
    拉取最新净值数据并更新 CSV。
    """
    if not os.path.exists(folder):
        print(f"未找到文件夹: {folder}")
        return []

    updated_files = []
    for filename in os.listdir(folder):
        if filename.endswith(".csv") and filename[:6].isdigit():
            code = filename[:6]
            csv_file = os.path.join(folder, filename)
            try:
                # 拉取最新数据
                df_new = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
                df_new['净值日期'] = pd.to_datetime(df_new['净值日期'])
                df_new = df_new.sort_values("净值日期").reset_index(drop=True)

                # 读取旧数据
                if os.path.exists(csv_file):
                    df_old = pd.read_csv(csv_file, parse_dates=['净值日期'])
                    df_combined = pd.concat([df_old, df_new]) \
                                    .drop_duplicates(subset='净值日期') \
                                    .sort_values("净值日期")
                else:
                    df_combined = df_new

                # 保存 CSV
                df_combined.to_csv(csv_file, index=False, encoding="utf-8-sig")
                updated_files.append(csv_file)
                print(f"[成功] {code} 已更新: {csv_file}")

            except Exception as e:
                print(f"[失败] {code} 更新失败: {e}")

    return updated_files



def update_to_worker_folder(folder="worker"):
    """
    扫描 to_worker 下所有六位数字 CSV 文件，并更新 CSV。
    """
    return update_found_folder(folder="to_worker")


# ----------------- 测试用例 -----------------
if __name__ == "__main__":
    # 当前目录下的 found 文件夹
    folder_path = os.path.join(os.getcwd(), "found")
    update_found_folder(folder_path)
