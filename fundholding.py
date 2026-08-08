import datetime
import os
import re
import time
import random
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

fund_code = "001877"
codes = ["000216", "000043", "501025", "002834", "018156"]


def get_holdings(fund_code, report_year=None):
    """
    通过天天基金 F10 接口直接获取基金股票持仓情况
    """
    # 清理环境变量中的代理设置
    os.environ.pop('HTTP_PROXY', None)
    os.environ.pop('HTTPS_PROXY', None)

    if report_year is None:
        report_year = datetime.datetime.now().year

    # 尝试当前年份和上一年
    for target_year in [report_year, report_year - 1]:
        url = f"http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=10&year={target_year}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"http://fundf10.eastmoney.com/ccmx_{fund_code}.html",
        }

        try:
            # 随机小延迟，降低并发请求带来的风控风险
            time.sleep(random.uniform(0.1, 0.3))
            
            response = requests.get(url, headers=headers, timeout=10)
            text = response.text

            # 提取包含 HTML 的字段内容
            match = re.search(r'content:"(.*?)",arryear', text)
            if not match:
                continue

            html_content = match.group(1)
            if not html_content.strip():
                continue

            # 使用 pandas 解析 HTML 表格
            dfs = pd.read_html(html_content)
            if not dfs:
                continue

            df = dfs[0]
            df.columns = [str(col).strip() for col in df.columns]

            # 标准化列名映射
            rename_dict = {}
            for col in df.columns:
                if '代码' in col: rename_dict[col] = '股票代码'
                elif '名称' in col: rename_dict[col] = '股票名称'
                elif '占净值' in col: rename_dict[col] = '占净值比例'
                elif '持股数' in col: rename_dict[col] = '持股数'
                elif '市值' in col: rename_dict[col] = '持仓市值'

            df = df.rename(columns=rename_dict)
            
            required_cols = ['股票代码', '股票名称', '占净值比例', '持股数', '持仓市值']
            existing_cols = [c for c in required_cols if c in df.columns]
            
            df_result = df[existing_cols].head(10)
            
            # 修正股票代码格式（提取6位纯数字）
            if '股票代码' in df_result.columns:
                df_result['股票代码'] = df_result['股票代码'].astype(str).str.extract(r'(\d{6})')[0]

            print(f"[{fund_code}] 成功获取 {target_year} 年持仓数据")
            return df_result, fund_code, True

        except Exception as e:
            continue

    print(f"[{fund_code}] 未能获取到持仓数据")
    return None, fund_code, False


class stocker_prompt():
    "基于持仓生成提示词"
    def __init__(self, code=None, codes=None):
        self.code = code
        self.codes = codes
        self.timenow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.prompt_text_single = (
            f"你是一个专业的AI投资助手，帮助用户分析此基金的股票持仓情况，"
            f"结合最近三个月时事(美国，中国加/降息周期，美国政治)，全球的资金流动，给出对此股票组合的建议\n"
        )
        self.prompt_text_multiple = (
            f"现在是 {self.timenow}，你是一个专业的AI投资助手，帮助用户对下列基金进行资产配置。"
            f"联网搜索给出的基金中的实时股票持仓情况，结合最近三个月时事(美国，中国加/降息周期，美国政治)，"
            f"全球的资金流动，给出最优的资产配置，根据每个基金代码给出仓位配置和风险提醒\n"
        )
        self.stocker = []

        # 处理单个基金
        if self.code and not self.codes:
            df, fund_code_res, valider = get_holdings(self.code)
            if valider and df is not None:
                for line in df.itertuples(index=False):
                    line_str = str(line).replace("Pandas", "")
                    self.stocker.append(line_str)
                for line in self.stocker:
                    self.prompt_text_single += line + '\n'
            else:
                self.prompt_text_single = f"对 {self.code} 的股票持仓情况，结合最近三个月时事(美国，中国加/降息周期，美国政治），全球的资金流动，给出对此股票组合的建议\n"

        # 处理多个基金（并发抓取）
        if self.codes and not self.code:
            # 限制 max_workers 为 3，防止过于频繁触发反爬
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(get_holdings, f_code): f_code for f_code in self.codes}
                
                for future in as_completed(futures):
                    try:
                        df, f_code, valider = future.result()
                        if valider and df is not None:
                            self.stocker.append(f"\n--- 基金代码: {f_code} ---")
                            for line in df.itertuples(index=False):
                                line_str = str(line).replace("Pandas", "")
                                self.stocker.append(line_str)
                        else:
                            self.stocker.append(f"\n--- 非股票型/无持仓基金代码: {f_code} ---")
                    except Exception as e:
                        print(f"处理基金持仓线程产生错误: {e}")

            for line in self.stocker:
                self.prompt_text_multiple += line + '\n'


if __name__ == '__main__':
    # 测试单个基金抓取
    df, code, valider = get_holdings(fund_code="001956")
    if valider:
        print("\n单基金抓取结果：")
        print(df)

    print("\n" + "="*50 + "\n")

    # 测试生成多基金 Prompt
    sp = stocker_prompt(codes=codes)
    print("生成的多基金提示词：")
    print(sp.prompt_text_multiple)