import datetime
import os
import akshare as ak
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QProgressDialog, QMessageBox
from replaceakshare.yfinanceworker import clean_and_format_code
from PyQt5.QtCore import QThread, pyqtSignal, Qt
equity_path = os.path.join(os.path.join("my_types","Equity"))
mapping_fund_industry_path = os.path.join("mapping", "mapping_fundindustry.csv")

from replaceakshare.yfinanceworker import get_stock_industry_yfinance
from config.get_config import get_proxy_config
mapping_fund_industry_path = os.path.join("mapping", "mapping_fundindustry.csv")
mapping_stock_industry_path = os.path.join("mapping", "mapping_stockindustry.csv")
proxy_port=get_proxy_config()
PROXYURL=f"http://127.0.0.1:{proxy_port}"

def get_fund_stocks(fund_code, report_year=datetime.datetime.now().year):
    """得到今年最新的重仓股票代码列表"""
    try:
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        holdings_df = ak.fund_portfolio_hold_em(symbol=fund_code, date=str(report_year))
        if holdings_df.empty:
            holdings_df = ak.fund_portfolio_hold_em(symbol=fund_code, date=str(report_year-1))

        if not holdings_df.empty:
            # 这里的‘季度’字段请根据 akshare 返回值确认，有时叫‘报告期’
            session_col = '季度' if '季度' in holdings_df.columns else '报告期'
            latest_report_session = holdings_df[session_col].max()
            latest_holdings = holdings_df[holdings_df[session_col] == latest_report_session]
            
            latest_holdings_sorted = latest_holdings[[
                '股票代码', '股票名称', '占净值比例', '持股数', '持仓市值'
            ]].sort_values(by='占净值比例', ascending=False).head(10)
            code_list = latest_holdings_sorted['股票代码'].astype(str).str.zfill(6).tolist()
            return code_list
        else:
            print(f"基金 {fund_code} 无持仓数据")
            return []
    except Exception as e:
        print(f"获取持仓数据失败: {e}")
        return []
file_lock = threading.Lock()










def get_fund_industry_yfinance_and_akshare(fund_code):
    """获取基金行业信息"""
    stocks = get_fund_stocks(fund_code)
    if not stocks: return fund_code, "无持仓数据"
    found_industries = []
    missing_stocks = []
    try:
        with file_lock: 
            df_local = pd.read_csv(mapping_stock_industry_path, dtype={"stock_code": str})
            local_map = dict(zip(df_local['stock_code'], df_local['industry']))
    except:
        local_map = {}
    for stock in stocks:
        if stock in local_map:
            found_industries.append(local_map[stock])
        else:
            missing_stocks.append(stock)
    if missing_stocks:
        try:
            # 1. 联网获取行业映射字典
            remote_data_dict = get_stock_industry_yfinance(missing_stocks)
            
            if remote_data_dict:
                # 将抓取到的行业加入本次基金的统计结果中
                found_industries.extend(remote_data_dict.values())
                
                # --- 核心改进：加锁后的二次过滤，确保 CSV 绝对唯一 ---
                with file_lock:
                    # 重新读取最新的磁盘数据，防止其他线程在刚才联网期间已经写入了
                    if os.path.exists(mapping_stock_industry_path):
                        df_current = pd.read_csv(mapping_stock_industry_path, dtype={"stock_code": str})
                        existing_codes = set(df_current['stock_code'].tolist())
                    else:
                        existing_codes = set()

                    # 仅保留磁盘中尚未存在的代码
                    new_rows = [
                        {"stock_code": s_code, "industry": s_industry}
                        for s_code, s_industry in remote_data_dict.items()
                        if s_code not in existing_codes
                    ]
                    
                    if new_rows:
                        new_df = pd.DataFrame(new_rows)
                        header = not os.path.exists(mapping_stock_industry_path)
                        # 追加写入
                        new_df.to_csv(mapping_stock_industry_path, mode='a', 
                                     index=False, header=header, encoding="utf-8-sig")
        except Exception as e:
            print(f"基金 {fund_code} 补全股票行业失败: {e}")
    all_names = []
    for item in found_industries:
        if item:
            all_names.extend([i.strip() for i in str(item).split('|')])
    unique_industries = list(dict.fromkeys(filter(None, all_names)))
    result_str = " | ".join(unique_industries) if unique_industries else "未知行业"
    return fund_code, result_str





class FundIndustryWorker(QThread):
    progress_changed = pyqtSignal(int, str)
    work_finished = pyqtSignal(str)

    def __init__(self, codes, mapping_fund_industry_path):
        super().__init__()
        self.codes = codes
        self.mapping_fund_industry_path = mapping_fund_industry_path
        self._is_running = True 

    def run(self):
        df = None
        try:
            # 加载 CSV... (保持原样)
            if os.path.exists(self.mapping_fund_industry_path):
                df = pd.read_csv(self.mapping_fund_industry_path, dtype={"fund_code": str})
            else:
                df = pd.DataFrame(columns=["fund_code", "industrys"])

            # 使用 executor
            with ThreadPoolExecutor(max_workers=2) as executor:
                # 记录所有的 future
                future_to_code = {
                    executor.submit(get_fund_industry_yfinance_and_akshare, code): code 
                    for code in self.codes
                }
                
                count = 0
                for future in as_completed(future_to_code):
                    # --- 核心改进：即时检查中断 ---
                    if not self._is_running:
                        # 尝试取消所有还没开始的任务
                        for f in future_to_code:
                            f.cancel()
                        break 
                    
                    try:
                        fund_code, industrys = future.result()
                        # 更新 df 逻辑... (保持原样)
                        if fund_code in df["fund_code"].values:
                            df.loc[df["fund_code"] == fund_code, "industrys"] = industrys
                        else:
                            new_row = pd.DataFrame({"fund_code": [fund_code], "industrys": [industrys]})
                            df = pd.concat([df, new_row], ignore_index=True)
                        
                        count += 1
                        self.progress_changed.emit(count, fund_code)
                        
                        if count % 10 == 0:
                            df.to_csv(self.mapping_fund_industry_path, index=False, encoding="utf-8-sig")
                    except Exception as e:
                        print(f"处理异常: {e}")

            status_msg = "数据采集完成！" if self._is_running else "任务已被取消，已保存当前进度。"
            self.work_finished.emit(status_msg)

        finally:
            if df is not None:
                df.to_csv(self.mapping_fund_industry_path, index=False, encoding="utf-8-sig")

    def stop(self):
        self._is_running = False


def get_single_fund_industry(fund_code):
    return get_fund_industry_yfinance_and_akshare(fund_code)


class SingleFundIndustryWorker(QThread):
    finished_signal = pyqtSignal(object) 
    def __init__(self, fund_code):
        super().__init__()
        self.fund_code = fund_code  # 确保这里保存了传进来的代码
    def run(self):
        try:
            result = get_single_fund_industry(self.fund_code) 
            self.finished_signal.emit(result)
        except Exception as e:
            self.finished_signal.emit(("", f"错误: {e}"))


if __name__ == "__main__":
    codes = [code.split(".")[0] for code in os.listdir(equity_path)[:50]]
    FundIndustryWorker(codes, mapping_fund_industry_path).run()
    