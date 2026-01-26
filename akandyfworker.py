import datetime
import os
import akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
equity_path = os.path.join(os.path.join("my_types","Equity"))
mapping_fund_industry_path = os.path.join("mapping", "mapping_fundindustry.csv")

from replaceakshare.yfinanceworker import get_stock_industry_yfinance
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

def get_fund_industry_yfinance_and_akshare(fund_code):
    """
    输入基金代码，输出该基金重仓股的行业汇总
    返回: (fund_code, "行业A | 行业B | ...")
    """
    stocks = get_fund_stocks(fund_code)
    os.environ.pop('HTTP_PROXY', "http://127.0.0.1:10809")
    if not stocks:
        return fund_code, "未知行业"
    try:
        industrys = get_stock_industry_yfinance(stocks) 
        if not industrys:
            industrys = "无数据"
        return fund_code, industrys
    except Exception as e:
        print(f"获取行业汇总失败: {e}")
        return fund_code, "获取失败"

def write_mapping_fund_industry(codes):
    with open (mapping_fund_industry_path, "w", encoding="utf-8") as f:
        f.write("fund_code,industrys\n")
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_code = {executor.submit(get_fund_industry_yfinance_and_akshare, code): code for code in codes}
            for future in as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    fund_code, industrys = future.result()
                    f.write(f"{fund_code},{industrys}\n")
                    print(f"已写入基金 {fund_code} 的行业信息")
                except Exception as e:
                    print(f"处理基金 {code} 时出错: {e}")


if __name__ == "__main__":
    codes = [code.split(".")[0] for code in os.listdir(equity_path)[:50]]
    write_mapping_fund_industry(codes)
    