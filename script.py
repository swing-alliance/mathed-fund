import os
import pandas as pd
import akshare as ak

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

def main():
    # 请根据实际路径更新 sorted_stable.csv 的路径
    stable_file_path = r'A:\projects\money2\stable\sorted_stable.csv'  # 更新为正确的路径
    
    if os.path.exists(stable_file_path):
        df_stable = pd.read_csv(stable_file_path)
        fund_codes = df_stable['基金代码'].astype(str).apply(lambda x: x.zfill(6)).tolist()
        
        # 拉取基金净值并保存
        saved_files = fetch_and_save_fund_csv(fund_codes, folder="found")
        
        if saved_files:
            print(f"成功保存 {len(saved_files)} 个基金的净值数据到 found 文件夹")
        else:
            print("没有基金数据被保存。")
    else:
        print(f"文件 {stable_file_path} 不存在。")

if __name__ == "__main__":
    main()
