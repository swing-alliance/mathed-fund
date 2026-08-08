import concurrent.futures
import datetime
import akshare as ak

# ==================== 1. 多线程抓取核心 ====================

def fetch_single_fund_holdings(fund_code: str):
    """单只基金抓取函数（供线程池调用）"""
    current_year = str(datetime.datetime.now().year)
    try:
        # 尝试获取今年数据
        df = ak.fund_portfolio_hold_em(symbol=fund_code, date=current_year)
        if df.empty:
            # 今年没披露则获取去年数据
            last_year = str(datetime.datetime.now().year - 1)
            df = ak.fund_portfolio_hold_em(symbol=fund_code, date=last_year)
        
        if not df.empty:
            latest_quarter = df['季度'].iloc[0]
            latest_df = df[df['季度'] == latest_quarter].head(10)
            return fund_code, latest_df['股票名称'].tolist()
    except Exception:
        pass
    return fund_code, []

def batch_fetch_holdings(fund_codes: list, max_workers: int = 10):
    """使用线程池并发抓取所有基金持仓"""
    fund_holdings_dict = {}
    print(f"🚀 开始并发抓取 {len(fund_codes)} 只基金的持仓数据 (线程数: {max_workers})...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_fund = {executor.submit(fetch_single_fund_holdings, code): code for code in fund_codes}
        
        # 实时收集结果
        for future in concurrent.futures.as_completed(future_to_fund):
            code, stocks = future.result()
            if stocks:
                fund_holdings_dict[code] = stocks
                
    print(f"✅ 抓取完成，成功获取 {len(fund_holdings_dict)} 只基金的有效持仓。")
    return fund_holdings_dict

# ==================== 2. 相似度过滤核心 ====================

def calculate_jaccard(list_a, list_b):
    """计算杰卡德相似度"""
    set_a, set_b = set(list_a), set(list_b)
    union = set_a.union(set_b)
    if not union:
        return 0.0
    return len(set_a.intersection(set_b)) / len(union)

def filter_funds_by_threshold(recommended_funds: list, fund_holdings_dict: dict, threshold: float):
    """
    根据相似度阈值过滤基金
    threshold: 0~1 之间。值越小，筛选越严格（保留下来的基金彼此越不像）
    """
    selected_funds = []
    
    for fund in recommended_funds:
        # 如果这个基金没有抓到持仓数据，直接跳过
        if fund not in fund_holdings_dict:
            continue
            
        current_holdings = fund_holdings_dict[fund]
        
        # 检查当前基金是否与【已经入选的基金】存在过度撞仓
        should_keep = True
        for selected in selected_funds:
            sim = calculate_jaccard(current_holdings, fund_holdings_dict[selected])
            if sim > threshold:
                should_keep = False
                break  # 一旦超过阈值，直接判定太相似，踢出
                
        if should_keep:
            selected_funds.append(fund)
            
    return selected_funds

# ==================== 3. 主程序入口 ====================
if __name__ == "__main__":
    # 模拟你按推荐度从高到低排序的 100 只基金代码（这里拿 6 只代表性基金做演示）
    # 021533 和 021532 是高度撞仓的半导体基金，019632可能也是同类
    my_fund_list = ["021533", "021532", "019632", "000001", "161725", "519674"] 
    
    # 【输入参数控制】
    SIMILARITY_THRESHOLD = 0.3  # 相似度上限阈值。超过 0.3 (大约重合4只股票以上) 的次要推荐基金就会被剔除
    MAX_THREADS = 10            # 多线程并发数（网速好可以开到 20）

    # 1. 并发抓取
    holdings_data = batch_fetch_holdings(my_fund_list, max_workers=MAX_THREADS)
    
    # 2. 相似度去重过滤
    final_output_list = filter_funds_by_threshold(my_fund_list, holdings_data, threshold=SIMILARITY_THRESHOLD)
    
    # 3. 打印最终结果
    print("\n" + "="*50)
    print(f"🎯 在相似度阈值 <= {SIMILARITY_THRESHOLD} 筛选后")
    print(f"最终为你保留的差异化基金代码列表 ({len(final_output_list)} 只):")
    print(final_output_list)
    print("="*50)
    
    # 顺便展示留下的基由于什么持仓被留下了
    for code in final_output_list:
        print(f"基金 {code} 的持仓摘要: {holdings_data[code][:3]}...")