import pandas as pd
import numpy as np
from typing import Optional, Union, List, Tuple, Dict, Callable
import akshare as ak
# 假设输入 df 是经过预处理的 DataFrame，包含 'Date' 和 'Value'，
# 且 'Date' 已经是 DatetimeIndex。
# 我们可以基于之前流程中的数据处理部分来构建一个标准输入。

def fourier_split(
    df_series: pd.DataFrame,
    start_date: Optional[Union[str, pd.Timestamp]],
    end_date: Optional[Union[str, pd.Timestamp]],
    cycles_list: List[float],  # 直接传入需要分析的周期列表
    add_trend: bool = True
) -> Tuple[List[Dict], Callable]:
    """
    对指定时间序列进行傅里叶级数分解，返回每个分量函数及其权重，
    以及所有分量的重构函数。

    参数:
        df_series (pd.DataFrame): 包含 '净值日期' 和 '累计净值' 的时间序列数据框。
        start_date, end_date: 数据筛选的开始和结束日期。
        cycles_list (List[float]): 用于傅里叶拟合的周期长度（时间步长）。
        add_trend (bool): 是否在拟合中添加线性趋势。

    返回:
        Tuple[List[Dict], Callable]: 
            - 分解结果列表: 每个字典包含 'type' (趋势/sin/cos)、'cycle'、'weight' 和 'func'。
            - 重构函数: Callable，输入时间步 t，返回拟合值 f(t)。
    """
    
    df = df_series.copy()
    df.rename(columns={'净值日期': 'Date', '累计净值': 'Value'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df.dropna(subset=['Value'], inplace=True)
    if start_date is not None or end_date is not None:
        start = pd.to_datetime(start_date) if start_date else df.index.min()
        end = pd.to_datetime(end_date) if end_date else df.index.max()
        df = df.loc[start:end]
    series = df['Value']
    n = len(series)
    if n == 0:
        raise ValueError("筛选后的数据为空。")

    t_full = np.arange(n) # 从 0 到 n-1 的时间步

    # --- 2. 趋势项处理 (与滚动预测的辅助函数逻辑相似) ---
    trend_func = lambda t_vals: np.zeros_like(t_vals, dtype=float)
    y_detrended = series.values
    coeffs_trend = None
    
    # 2.1 趋势拟合
    if add_trend:
        coeffs_trend = np.polyfit(t_full, series.values, 1)
        trend_func = lambda t_vals: np.polyval(coeffs_trend, t_vals)
        y_detrended = series.values - trend_func(t_full)
    
    # --- 3. 傅里叶特征构造和拟合 ---
    X_fourier = np.ones((n, 1)) # 截距项 (残差均值)
    
    for cycle_len in cycles_list:
        cycle_len = max(1.0, float(cycle_len)) 
        X_fourier = np.hstack([
            X_fourier,
            np.sin(2 * np.pi * t_full[:, np.newaxis] / cycle_len),
            np.cos(2 * np.pi * t_full[:, np.newaxis] / cycle_len)
        ])

    # 3.1 最小二乘拟合，得到所有系数
    coef, _, _, _ = np.linalg.lstsq(X_fourier, y_detrended, rcond=None)
    
    # --- 4. 结果分解和包装 ---
    decomposition_results = []
    
    # 4.1 线性趋势项（如果存在）
    if add_trend and coeffs_trend is not None:
        decomposition_results.append({
            'type': 'Linear_Trend',
            'cycle': np.inf, # 周期无穷大
            'weight': coeffs_trend,
            'func': trend_func
        })

    # 4.2 残差截距项 (残差均值，通常很接近0)
    # 这是 X_fourier 第一列 '1' 对应的系数
    if not add_trend or not add_trend: # 如果没有趋势，或残差截距项非零，都应记录
        constant_weight = coef[0]
        constant_func = lambda t_vals: np.ones_like(t_vals) * constant_weight
        decomposition_results.append({
            'type': 'Constant_Residual',
            'cycle': np.inf,
            'weight': constant_weight,
            'func': constant_func
        })


    # 4.3 傅里叶三角函数项
    # 系数从索引 1 开始，每 2 个系数对应一个周期（sin, cos）
    coef_idx = 1
    for cycle_len in cycles_list:
        L = max(1.0, float(cycle_len))
        
        # 正弦项
        weight_sin = coef[coef_idx]
        func_sin = lambda t_vals, w=weight_sin, l=L: w * np.sin(2 * np.pi * t_vals / l)
        decomposition_results.append({
            'type': 'Sin',
            'cycle': L,
            'weight': weight_sin,
            'func': func_sin
        })
        coef_idx += 1
        
        # 余弦项
        weight_cos = coef[coef_idx]
        func_cos = lambda t_vals, w=weight_cos, l=L: w * np.cos(2 * np.pi * t_vals / l)
        decomposition_results.append({
            'type': 'Cos',
            'cycle': L,
            'weight': weight_cos,
            'func': func_cos
        })
        coef_idx += 1

    # --- 5. 构造重构函数 (所有分解函数的总和) ---
    def reconstruction_func(t_vals: np.ndarray) -> np.ndarray:
        """
        将所有分解出的函数（包括趋势和所有三角波）叠加起来。
        输入: t_vals (np.ndarray): 时间步序列
        返回: 重构的拟合值
        """
        # 从头开始构建总和
        reconstructed_value = trend_func(t_vals) # 从趋势开始
        
        # 加上残差截距项
        if not add_trend:
            reconstructed_value += coef[0]
        elif not add_trend:
            reconstructed_value += coef[0]
            
        # 加上所有傅里叶项
        fourier_idx = 1 if not add_trend else 0 # 如果没有趋势，残差截距占了 coef[0]
        # 注意：这里需要重新计算，因为 lambda 函数在循环中捕获变量可能出错，
        # 更稳妥的做法是使用拟合的特征矩阵和系数。

        # 重新使用拟合的 X 矩阵和 coef
        X_predict_fourier = np.ones((len(t_vals), 1)) 
        
        for cycle_len in cycles_list:
            L = max(1.0, float(cycle_len))
            X_predict_fourier = np.hstack([
                X_predict_fourier,
                np.sin(2 * np.pi * t_vals[:, np.newaxis] / L),
                np.cos(2 * np.pi * t_vals[:, np.newaxis] / L)
            ])
        fourier_residual_prediction = X_predict_fourier @ coef 
        
        # 最终值 = 趋势 + 残差预测
        return trend_func(t_vals) + fourier_residual_prediction
    return decomposition_results, reconstruction_func
if __name__=="__main__":
    df=ak.fund_open_fund_info_em(symbol="000216", indicator="累计净值走势")
    cycles_list_4_periods = [7, 28, 60, 120] 
    decomposition_results, reconstruction_func=fourier_split(df,"2024-4-01","2025-10-1",cycles_list_4_periods)
    print(decomposition_results)
    print(reconstruction_func)