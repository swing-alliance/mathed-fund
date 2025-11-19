import pandas as pd
import numpy as np

# 假设 akshare 库已安装 (pip install akshare)

def simulator_regular_invest(total_regulation_days, regular_invest_amount, code=None, path=None):
    """
    模拟定期定额投资的收益，并计算总收益率和年化收益率。

    Args:
        total_regulation_days (int): 模拟投资的总期数（交易日）。
        regular_invest_amount (float): 每期定期投入的金额。
        code (str, optional): 基金代码，用于通过 akshare 获取数据。
        path (str, optional): CSV 文件路径，用于读取本地数据。

    Returns:
        tuple: (annualized_return_percentage, total_return_percentage, total_invested_amount)
    """
    df = pd.DataFrame()
    if code and not path:
        try:
            import akshare as ak
            df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
            df.columns = ['净值日期', '累计净值']
        except ImportError:
            print("Error: 'akshare' not installed. Cannot fetch data by code.")
            return None, None, None
        except Exception as e:
            print(f"Error fetching data with akshare for code {code}: {e}")
            return None, None, None
            
    elif path and not code:
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"Error reading CSV file at {path}: {e}")
            return None, None, None
    else:
        print("Error: Please provide either 'code' (for online fetch) OR 'path' (for local CSV).")
        return None, None, None
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df = df.sort_values(by='净值日期', ascending=True).reset_index(drop=True)
    df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
    df.dropna(subset=['累计净值'], inplace=True)
    investment_df = df.tail(total_regulation_days).copy() 
    
    if investment_df.empty:
        print("Error: Investment data frame is empty after filtering.")
        return 0.0, 0.0, 0.0
    investment_df['购买份额'] = regular_invest_amount / investment_df['累计净值']
    total_invested_amount = len(investment_df) * regular_invest_amount
    total_shares = investment_df['购买份额'].sum()
    latest_cumulative_net_value = investment_df['累计净值'].iloc[-1]
    final_market_value = total_shares * latest_cumulative_net_value
    if total_invested_amount == 0:
        total_return_percentage = 0.0
    else:
        total_return_percentage = (final_market_value - total_invested_amount) / total_invested_amount * 100
    T_years = len(investment_df) / 250.0 
    if T_years > 0 and total_invested_amount > 0:
        annualized_return_decimal = (final_market_value / total_invested_amount) ** (1 / T_years) - 1
        annualized_return_percentage = annualized_return_decimal * 100
    else:
        annualized_return_percentage = 0.0
    return annualized_return_percentage, total_return_percentage, total_invested_amount

if __name__ == '__main__':
    # 设定参数
    total_regulation_days = 1200 # 过去 100 个交易日
    regular_invest_amount = 500.0 # 每次投入 500 元

    # 方式一: 使用基金代码 (需要 akshare 库)
    try_code = "017519" 
    
    annualized_return, total_return, total_invested_value = simulator_regular_invest(
        total_regulation_days, regular_invest_amount, code=try_code
    )
    
    if annualized_return is not None:
        print(f"\n--- 基金定投模拟结果 (代码: {try_code}) ---")
        print(f"总投入期数: {total_regulation_days} 期")
        print(f"总投入金额: {total_invested_value:,.2f} 元")
        print(f"总收益率: {total_return:.2f}%")
        print(f"年化收益率: {annualized_return:.2f}%")
        
    # 方式二: 使用本地 CSV 文件 (如果不用 akshare)
    # try_path = 'your_fund_data.csv' # 替换为你的本地文件路径
    # try:
    #     annualized_return, total_return, total_invested_value = simulator_regular_invest(
    #         total_regulation_days, regular_invest_amount, path=try_path
    #     )
    #     if annualized_return is not None:
    #         print(f"\n--- 基金定投模拟结果 (文件: {try_path}) ---")
    #         print(f"总投入期数: {total_regulation_days} 期")
    #         print(f"总投入金额: {total_invested_value:,.2f} 元")
    #         print(f"总收益率: {total_return:.2f}%")
    #         print(f"年化收益率: {annualized_return:.2f}%")
    # except Exception as e:
    #     print(f"模拟失败: {e}")