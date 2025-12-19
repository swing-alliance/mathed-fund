import akshare as ak
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

fund_code = "001877"
codes=["000216","000043","501025","002834","018156"]


def get_holdings(fund_code, report_year=datetime.datetime.now().year):
    "得到今年最新的股票持仓情况"
    try:
        holdings_df = ak.fund_portfolio_hold_em(symbol=fund_code, date=report_year)
        if not holdings_df.empty:
            latest_report_session = holdings_df['季度'].max()
            latest_holdings = holdings_df[holdings_df['季度'] == latest_report_session]
            latest_holdings_sorted = latest_holdings[[
                '股票代码', 
                '股票名称', 
                '占净值比例', 
                '持股数', 
                '持仓市值'
            ]].sort_values(by='占净值比例', ascending=False).head(10)
            valider=True
            return latest_holdings_sorted, fund_code,valider
        else:
            df=None
            valider=False
            return df ,fund_code,valider
    except Exception as e:
        pass



class stocker_prompt():
    "基于持仓生成提示词"
    def __init__(self,code=None,codes=None):
        self.code = code
        self.codes = codes
        self.timenow = datetime.datetime.now()
        self.prompt_text_single=f"你是一个专业的AI投资助手，帮助用户分析此基金的股票持仓情况，结合最近三个月时事(美国，中国加/降息周期，美国政治)，全球的资金流动，给出对此股票组合的建议\n"
        self.prompt_text_multiple=f"现在是{self.timenow}，你是一个专业的AI投资助手，帮助用户将对下列基金进行资产配置。联网搜索给出的基金中的实时股票持仓情况，结合最近三个月时事(美国，中国加/降息周期，美国政治)，全球的资金流动，给出最优的资产配置,根据每个基金代码给出仓位配置和风险提醒\n"
        self.stocker=[]
        if self.code and not self.codes:
            df,fund_code,valider=get_holdings(code) 
            if valider:
                for line in df.itertuples(index=False):
                    line_str = str(line)
                    line_str = line_str.replace("Pandas","")
                    self.stocker.append(line_str)
                for line in self.stocker:
                    self.prompt_text_single+=line + '\n'
            else:
                self.prompt_text_single=f"对{fund_code}的股票持仓情况，结合最近三个月时事(美国，中国加/降息周期，美国政治），全球的资金流动，给出对此股票组合的建议\n"
        if self.codes and not self.code:
            self.executor=ThreadPoolExecutor(max_workers=10)
            self.futures=[]
            self.future_to_code={}
            for fund_code in self.codes:
                future=self.executor.submit(get_holdings,fund_code)
                self.futures.append(future)
            for future in as_completed(self.futures):
                try:
                    df,fund_code,valider=future.result()
                    if valider:
                        is_first=True
                        for line in df.itertuples(index=False):
                            if is_first:
                                self.stocker.append("基金代码"+fund_code)
                                is_first=False
                            line_str = str(line)
                            line_str = line_str.replace("Pandas","")
                            self.stocker.append(line_str)
                    else:
                        self.stocker.append("非股票型基金代码"+fund_code)
                except Exception as e:
                    pass
            for line in self.stocker:
                self.prompt_text_multiple+=line + '\n'

if __name__ == '__main__':
    print(get_holdings(fund_code="001956"))
    # stocker_prompt(code=None,codes=codes)
