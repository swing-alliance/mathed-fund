import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
def get_today_change_percent_group(codes):
    """
    输入：逗号分隔的字符串 "600879,002475,002371"
    返回：字典 { '代码': '涨跌幅' }
    """
    # 1. 解析字符串并清洗数据
    results = {}
    # 2. 登录 Baostock (主循环外登录，防止 10053 错误)
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return results
    try:
        # 3. 设定日期范围（取最近 10 天确保能覆盖周末和节假日）
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        for code in codes:
            try:
                # 自动补全 6 位并判断沪深市
                clean_code = code.zfill(6)
                if clean_code.startswith('6') or clean_code.startswith('9'):
                    bs_code = f"sh.{clean_code}"
                else:
                    bs_code = f"sz.{clean_code}"
                # 查询历史 K 线数据
                rs = bs.query_history_k_data_plus(
                    bs_code,
                    "date,code,pctChg",  # pctChg 即涨跌幅
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",
                    adjustflag="3"
                )
                # 解析结果
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                if data_list:
                    # 取最后一行数据（最新交易日）
                    latest_row = data_list[-1]
                    pct_change = latest_row[2]  # pctChg 在第三列
                    results[clean_code] = float(pct_change)
                else:
                    results[clean_code] = None
                    print(f"⚠️ {clean_code} 无数据（可能停牌）")
            except Exception as e:
                print(f"❌ 处理 {code} 时出错: {e}")
                results[code] = None
    finally:
        # 4. 退出登录（确保连接释放）
        bs.logout()
        print("--- 任务结束，已安全退出 Baostock ---")
    return results



# --- 测试运行 ---
if __name__ == "__main__":
    # 这里输入你的 Account ID 相关股票清单字符串
    input_str = ["600879", "002475", "300308", "2371"]
    final_dict = get_today_change_percent_group(input_str)
    
    print("\n最后结果字典:")
    print(final_dict)