import os
import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
path=os.path.join(os.getcwd(),'found')

def readcsv(path):
    df = pd.read_csv(path)
    return df


# fund_info_df = ak.fund_individual_basic_info_xq(symbol="000309")，返回基金信息
# df_new = ak.fund_open_fund_info_em(symbol="000216", indicator="累计净值走势")，返回累计净值走势

#年化比率

#滑动窗口年化比率
def year_rate_sliding(code, window_size_days=540, step_size_days=30):
    """滑动窗口年化，反应大方向的趋势，具有延后性，不够敏感"""
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    except Exception as e:
        print(f"获取基金 {code} 数据失败: {e}")
        return None, None
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df = df.sort_values("净值日期").reset_index(drop=True)
    if len(df) < window_size_days:
        print(f"基金 {code} 的数据不足，无法计算年化收益率。")
        return None, None
    window_size_days = window_size_days  
    step_size_days = step_size_days      
    annualized_returns = []
    window_dates = []
    end_date = df['净值日期'].iloc[-1]
    while True:
        window_end_date = end_date
        window_start_date = window_end_date - pd.Timedelta(days=window_size_days)
        if window_start_date < df['净值日期'].iloc[0]:
            print(f"基金{code}的{window_start_date}到{window_end_date}数据不足，或是计算完了。")
            break
        df_window = df[(df['净值日期'] >= window_start_date) & (df['净值日期'] <= window_end_date)]#重置窗口
        if len(df_window) < 2:
            return None, None
        start_value = df_window['累计净值'].iloc[0]
        end_value = df_window['累计净值'].iloc[-1]
        if start_value <= 0 or end_value <= 0:
             return None, None
        years = (df_window['净值日期'].iloc[-1] - df_window['净值日期'].iloc[0]).days / 365.25#代表window_size_days是多少年
        if years <= 0:#不可能发生？
            end_date = end_date - pd.Timedelta(days=step_size_days)
            continue
        annualized_return = (end_value / start_value) ** (1 / years) - 1
        annualized_returns.append(annualized_return)
        window_dates.append(window_end_date)
        end_date = end_date - pd.Timedelta(days=step_size_days)
    return annualized_returns, window_dates


#夏普比率(暂时不实现)
# def sharp_ratio(annualized_returns):
#     return np.mean(annualized_returns) / np.std(annualized_returns)

#最高年化波动
def get_max_annualized_volatility(code: str, window_size: int) -> tuple[float, pd.Timestamp]:
    """
    计算并返回基金在指定滑动天数内的最高年化波动率。
    参数:
    - code (str): 基金代码，例如 '001211'。
    - window_size (int): 滑动窗口天数，例如 60。
    返回:
    - tuple[float, pd.Timestamp]: 一个元组，包含最高年化波动率和其发生的日期。
                                  如果数据获取失败，则返回 (None, None)。
    """
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df.set_index('净值日期', inplace=True)

        df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
        df.dropna(subset=['累计净值'], inplace=True)

    except Exception as e:
        print(f"获取基金 {code} 数据失败：{e}")
        return None, None

    # 计算每日百分比收益率
    daily_returns = df['累计净值'].pct_change().dropna()
    
    # 使用滑动窗口计算每日收益率的标准差
    daily_volatility = daily_returns.rolling(window=window_size).std()
    
    # 将标准差年化 (乘以 sqrt(252))
    annualized_volatility = daily_volatility * np.sqrt(252)
    
    # 找到最高年化波动率及其对应的日期
    if not annualized_volatility.empty:
        max_volatility = annualized_volatility.max()
        max_date = annualized_volatility.idxmax()
        return max_volatility, max_date
    else:
        print("无法计算波动率，数据不足或窗口大小过大。")
        return None, None


#最大回撤率

#最大回撤天数


def fourier_warm(
    code: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    sampling_frequency: str,
    order: int,
    window_size: int = None,
    prediction_steps: int = 1
):
    """使用傅里叶分析对基金净值进行滚动预测。"""
    try:
        df: pd.DataFrame = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    except Exception as e:
        print(f"获取基金 {code} 数据失败: {e}")
        return None, None
    df['净值日期']= pd.to_datetime(df['净值日期'])
    # 将日期设为索引
    df.set_index('净值日期', inplace=True)
    df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
    df.dropna(subset=['累计净值'], inplace=True)
    df = df.loc[~df.index.duplicated(keep='last')]
    # 按指定频率重采样并填充缺失值
    df = df.resample(sampling_frequency).mean()
    df['累计净值'] = df['累计净值'].interpolate(method='linear')
    df.dropna(subset=['累计净值'], inplace=True)
    print(df)
    
    df = df.loc[start_date:end_date]
    
    if len(df) < 2 * order + 1:
        raise ValueError("数据点不足，请选择更早的 start_date 或更小的 order。")

    if window_size is None:
        initial_window_size = len(df)
    else:
        initial_window_size = window_size
        
    if initial_window_size < 2 * order + 1:
        raise ValueError("窗口大小过小，无法进行傅里叶分析。")
    
    predictions = []
    
    for i in range(initial_window_size, len(df) - prediction_steps):
        train_data = df['累计净值'].iloc[i - initial_window_size : i]
        
        y = train_data.values
        n = len(y)
        fourier_transform = np.fft.fft(y)
        
        fourier_coeffs = np.zeros(n, dtype=complex)
        fourier_coeffs[:order+1] = fourier_transform[:order+1]
        fourier_coeffs[n - order:] = np.conj(fourier_transform[1:order+1][::-1])
        
        predicted_values = []
        for step in range(1, prediction_steps + 1):
            prediction = np.mean(y)
            for k in range(1, order + 1):
                A_k = fourier_transform[k]
                prediction += (A_k / n) * np.exp(2j * np.pi * k * (n + step) / n)
            
            predicted_values.append(prediction.real)

        predictions.append({
            'date': df.index[i],
            'actual_value': df['累计净值'].iloc[i],
            'predicted_values': predicted_values
        })
    
    return pd.DataFrame(predictions)



if __name__ == "__main__":
    # result =year_rate_sliding('000309')
    # print(result)
    # risk=get_max_annualized_volatility('000216',60)
    # print(risk)
    prediction = fourier_warm('000309', '2024-08-01', '2025-08-30', sampling_frequency='D', order=12, window_size=25, prediction_steps=10)
    print(prediction)
