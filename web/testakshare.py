import akshare as ak
import pandas as pd


def get_fund_name(filename):
    """通过网络爬取akshare获得基金名称"""
    try:
        print('尝试得到基金名称')
        ak.fund_overview_em(symbol=filename)
        info =  ak.fund_overview_em(symbol=filename)
        fund_full_name = info[info['item'] == '基金全称']['value'].iloc[0]
        return fund_full_name
    except IndexError:
        raise ValueError(f"无法从akshare查询到基金代码 {filename} 的信息")

def fetch_fund_latest_info(filename: str) -> str:
    """
    输入6位基金代码，拉取基金基础信息并在终端打印df
    :param fund_code: 6位字符串，例 "000001"
    """
    # 输入校验：6位纯数字
    if not (len(filename) == 6 and filename.isdigit()):
        print("[ERROR] 请输入6位数字基金代码，格式示例：000001")
        return
    try:
        df: pd.DataFrame = ak.fund_overview_em(symbol=filename)
        row = df.iloc[0]
        fund_short_name = row.get("基金简称", "")
        fund_type = row.get("基金类型", "")
        # ========== 重点修改 ==========
        # 不要用row.get("基金代码")，改用入参fund_code（干净6位数字）
        f_code = filename
        raw_df_str = df.to_string()  # 完整原始df转字符串
        df_fund_info = pd.DataFrame([{
            "基金代码": f_code,
            "基金简称": fund_short_name,
            "基金类型": fund_type,
            "基金信息": raw_df_str
        }])
        return df_fund_info["基金简称"].iloc[0]
    except Exception as err:
        print(f"[ERROR] 获取基金数据失败：{str(err)}")


if __name__ == "__main__":
    # 测试函数
    test_filename = "001803"  # 替换为实际的基金代码
    try:
        df_name = fetch_fund_latest_info(test_filename)
        print(f"基金代码 {test_filename} 的信息:\n{df_name}")
        # fund_name = get_fund_name(test_filename)
        # print(f"基金代码 {test_filename} 的名称是: {fund_name}")
    except ValueError as e:
        print(e)