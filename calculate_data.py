import os
import pandas as pd
import numpy as np

def normalize_columns(df):
    """把 CSV 的原始列名统一为 ['日期', '净值']"""
    col_map = {
        "净值日期": "日期",
        "单位净值": "净值",
        "date": "日期",
        "Date": "日期",
        "nav": "净值",
        "NAV": "净值"
    }
    df = df.rename(columns=col_map)
    return df[["日期", "净值"]]  # 只保留必要列




def fund_metrics(df, benchmark=None, rf=0.02):
    """
    输入基金净值，输出波动率、最大回撤、相对波动系数、夏普比率
    要求 df 至少有 ['日期','净值']
    """
    df = df.copy()
    df = df.sort_values("日期")
    df["收益率"] = df["净值"].pct_change()

    # --- 波动率（年化） ---
    vol = df["收益率"].std() * np.sqrt(252)

    # --- 最大回撤 ---
    cum_max = df["净值"].cummax()
    drawdown = (df["净值"] - cum_max) / cum_max
    mdd = drawdown.min()

    # --- 夏普比率 ---
    mean_return = df["收益率"].mean() * 252
    sharpe = (mean_return - rf) / vol if vol != 0 else np.nan

    # --- 相对波动系数 ---
    rel_vol = None
    if benchmark is not None:
        bm = benchmark.copy()
        bm = bm.sort_values("日期")
        bm["收益率"] = bm["净值"].pct_change()
        bm_vol = bm["收益率"].std() * np.sqrt(252)
        rel_vol = vol / bm_vol if bm_vol != 0 else np.nan

    return {
        "波动率": vol,
        "最大回撤": mdd,
        "夏普比率": sharpe,
        "相对波动系数": rel_vol
    }

if __name__ == '__main__':
    folder = "found"
    files = [f for f in os.listdir(folder) if f.endswith(".csv")]

    if not files:
        print("⚠️ 没有找到任何 CSV 文件")
    else:
        for file in files:
            print(file)
            file_path = os.path.join(folder, file)
            print(f"读取基金数据文件: {file_path}")

            df_fund = pd.read_csv(file_path)
            df_fund = normalize_columns(df_fund)   #修正列名

            df_benchmark = None
            bm_file = os.path.join(folder, "benchmark.csv")
            if os.path.exists(bm_file):
                df_benchmark = pd.read_csv(bm_file)
                df_benchmark = normalize_columns(df_benchmark)

            result = fund_metrics(df_fund, benchmark=df_benchmark, rf=0.02)

            print("波动率:", result["波动率"])
            print("最大回撤:", result["最大回撤"])
            print("夏普比率:", result["夏普比率"])
            print("相对波动系数:", result["相对波动系数"])
