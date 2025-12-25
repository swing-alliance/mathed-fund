import akshare as ak
import yfinance as yf
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import pandas as pd
def get_china_stock_data(symbol, period="5", adjust="qfq"):
    """
    获取中国股票数据的函数
    :param symbol: 股票代码
    :param period: 数据周期
    :param adjust: 复权方式
    :return: 股票历史数据 DataFrame
    """
    try:
        return ak.stock_zh_a_hist_min_em(symbol=symbol, period=period, adjust=adjust)
    except Exception as e:
        print(f"Error fetching China stock data: {e}")
        return None


def get_stock_data(ticker, period="5d", interval="5m"):
    """
    获取国外股票数据的函数
    :param ticker: 股票代码
    :param period: 数据周期
    :param interval: 数据间隔
    :return: 股票历史数据 DataFrame
    """
    stock_refer=clean_stock_reference(ticker)
    if stock_refer == "cn":
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        try:
            return ak.stock_zh_a_hist_min_em(symbol=ticker, period=5, adjust="qfq")
        except Exception as e:
            print(f"Akshare 获取失败: {e}")
            return None
    else:
        os.environ['HTTP_PROXY'] = "http://127.0.0.1:10809"
        os.environ['HTTPS_PROXY'] = "http://127.0.0.1:10809"
        try:
            stock = yf.Ticker(stock_refer)
            df = stock.history(period=period, interval=interval)
            return df
        except Exception as e:
            print(f"yfinance 获取失败: {e}")
            return None
        

def clean_stock_reference(stockcode):
    """
    智能补全股票代码格式
    - 6位数字: 自动识别 sh/sz (A股)
    - 5位数字: 补全 .HK (港股)
    - 4位/6位纯数字 + .T: 日本股票 (如 7203.T 丰田)
    - 字母: 保持原样 (美股)
    """
    code = str(stockcode).strip().upper()
    if code.isdigit() and len(code) == 6:
        return "cn"
    elif code.isdigit() and len(code) == 5:
        code = int(code)
        code=str(code)
        code=code.zfill(4)
        return f"{code}.HK"
    elif code.isdigit() and len(code) == 4:
        return f"{code}.T"
    elif code.isalpha():
        return code 
    return code 


def get_stock_data_for_codes(stock_codes, period="5d", interval="5m"):
    """
    并行获取多个股票数据
    :param stock_codes: 股票代码列表
    :param period: 数据周期
    :param interval: 数据间隔
    :return: 包含所有股票数据的字典
    """
    if stock_codes:
        results = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_code = {executor.submit(get_stock_data, code, period, interval): code for code in stock_codes}
            for future in as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    data = future.result()
                    results[code] = data
                except Exception as e:
                    print(f"Error fetching data for {code}: {e}")
                    results[code] = None
    os.environ.pop('HTTP_PROXY', None)
    os.environ.pop('HTTPS_PROXY', None)
    return results



def from_stock_data_for_codes_get_real_time_fluctuation(stock_codes):
    """
    获取多个股票的实时涨跌幅
    :param stock_codes: 股票代码列表
    :return: 包含股票实时涨跌幅的字典
    """
    if stock_codes is None or len(stock_codes) == 0:
        return {}
    stock_data = get_stock_data_for_codes(stock_codes, period="5d", interval="5m")
    fluctuations = {}
    if stock_data is None:
        return fluctuations
    try:
        for code, dataframe in stock_data.items():
            if dataframe is None:
                print(f"代码: {code} 的数据为空，跳过计算。")
                continue
            if not dataframe.empty and len(dataframe) > 0:
                df = dataframe.reset_index().copy()
            else:
                print(f"代码: {code} 的数据为空，跳过计算。")
                continue
            time_col_name = get_date_column(df)
            temp_dates = pd.to_datetime(df[time_col_name], utc=True).dt.tz_localize(None).dt.date
            df[time_col_name] = temp_dates
            print(f"处理代码: {code} 的数据，时间列: {time_col_name}")
            close_col_name = get_close_column(df)
            col = df[time_col_name]
            last_date = col.iloc[-1]
            previous_date = None
            for i in range(len(df) - 1, -1, -1):
                if col.iloc[i] != last_date:
                    previous_date = col.iloc[i]
                    break
            if previous_date is not None:
                last_val = df[df[time_col_name] == last_date][close_col_name].iloc[-1]
                prev_val = df[df[time_col_name] == previous_date][close_col_name].iloc[-1]
                fluctuation = (last_val - prev_val) / prev_val * 100
                print(f"代码: {code}, 日期: {last_date}, 涨跌: {fluctuation:.2f}%, 前值: {prev_val}, 当前值: {last_val}, last_date: {last_date}, previous_date: {previous_date}")
                fluctuations[code] = fluctuation
    except Exception as e:
        print(f"计算涨跌幅时出错: {e}")
    return fluctuations

def get_close_column(dataframe):
    possible_close_cols = ['Close', 'close', '收盘价', '收盘']
    for col in possible_close_cols:
        if col in dataframe.columns:
            return col
def get_date_column(dataframe):
    possible_date_cols = ['Date', 'date', '时间', '日期', 'datetime', 'Datetime']
    for col in dataframe.columns:
        clean_col = str(col).strip() # 去除列名两端的空格
        if clean_col in possible_date_cols:
            return col
    return None

if __name__ == "__main__":
    print(get_stock_data("01347"))