import requests
import pandas as pd
import datetime
import re

def get_fund_holdings_direct(fund_code, year=None):
    """
    直接请求天天基金 F10 接口获取股票持仓（带伪装 Header，稳定性极高）
    """
    if year is None:
        year = datetime.datetime.now().year

    # 尝试当前年份和上一年
    for target_year in [year, year - 1]:
        url = f"http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=10&year={target_year}"
        
        # 关键：加上 User-Agent 和 Referer 伪装成浏览器
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"http://fundf10.eastmoney.com/ccmx_{fund_code}.html",
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            text = response.text

            # 从返回的 JS 字符串中提取 HTML 内容
            match = re.search(r'content:"(.*?)",arryear', text)
            if not match:
                continue

            html_content = match.group(1)
            if not html_content.strip():
                continue

            # 使用 pandas 解析 HTML 中的表格
            dfs = pd.read_html(html_content)
            if not dfs:
                continue

            # 获取最新的一个季度的持仓表格（通常是第一个）
            df = dfs[0]

            # 清理列名（去除可能存在的序号等多余列）
            df.columns = [str(col).strip() for col in df.columns]

            # 筛选我们需要的列
            # 典型列名包含：'股票代码', '股票名称', '占净值 比例', '持股数（万股）', '持仓市值（万元）'
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
            
            # 格式化股票代码（确保是 6 位字符串，如 000001）
            if '股票代码' in df_result.columns:
                df_result['股票代码'] = df_result['股票代码'].astype(str).str.extract(r'(\d{6})')[0]

            print(f"[{fund_code}] 成功获取 {target_year} 年最新持仓数据")
            return df_result, fund_code, True

        except Exception as e:
            continue

    print(f"[{fund_code}] 未能获取到持仓数据")
    return None, fund_code, False


if __name__ == "__main__":
    fund_code = "001092"
    df, code, valider = get_fund_holdings_direct(fund_code)
    if valider:
        print(df)
    else:
        print(f"获取持仓失败: {code}")