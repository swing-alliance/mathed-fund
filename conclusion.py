





def generate_market_conclusion(index_up: int, index_down: int, index_normal: int, month_happened_withdrawal_ratio: float, month_happened_upover10_ratio: float) -> str:
    """
    index_up: 近30天年化收益率超过10%的基金数量,index_down: 近30天年化收益率小于0的基金数量,index_normal: 近30天年化收益率在0%到10%之间的基金数量,
    month_happened_withdrawal_ratio:过去30天存在10%回撤比例的基金占比,month_happened_upover10_ratio:过去30天存在10%上涨比例的基金占比
    """
    if any(arg < 0 for arg in [index_up, index_down, index_normal, month_happened_withdrawal_ratio, month_happened_upover10_ratio]):
        return "参数错误：所有输入值必须为非负数。"
    
    if month_happened_withdrawal_ratio > 1 or month_happened_upover10_ratio > 1:
        return "参数错误：回撤和上涨比例必须在0-1之间。"
    
    # 计算总量和比例
    total_funds = index_up + index_down + index_normal
    if total_funds == 0:
        return "暂无有效数据，当前无法判断市场行情。"
    
    p_up = index_up / total_funds
    p_down = index_down / total_funds
    p_normal = index_normal / total_funds
    
    # 阈值定义
    STRENGTH_ADVANTAGE_THRESHOLD = 0.10
    HIGH_DIVERGENCE_THRESHOLD = 0.85
    ABSOLUTE_BULLISH_THRESHOLD = 0.60
    EXTREME_MOVEMENT_THRESHOLD = 0.40  # 新增：极端波动阈值
    
    # 判断市场分化程度
    extreme_movement_ratio = month_happened_withdrawal_ratio + month_happened_upover10_ratio
    is_highly_divergent = (p_up + p_down) > HIGH_DIVERGENCE_THRESHOLD
    has_extreme_volatility = extreme_movement_ratio > EXTREME_MOVEMENT_THRESHOLD
    
    # 构建分化程度描述
    if is_highly_divergent:
        divergence_note = "市场处于高度分化状态，中间地带资产稀少。"
    else:
        divergence_note = "市场结构较为温和，多数资产处于中间状态。"
    
    # 添加波动性描述
    volatility_note = ""
    if has_extreme_volatility:
        if month_happened_withdrawal_ratio > 0.3 and month_happened_upover10_ratio > 0.3:
            volatility_note = "市场同时存在大量暴涨暴跌基金，波动极为剧烈。"
        elif month_happened_upover10_ratio > 0.3:
            volatility_note = "市场存在显著赚钱效应或者结构性行情特征，但需注意波动,短期过热风险。"
        elif month_happened_withdrawal_ratio > 0.3:
            volatility_note = "市场回撤压力较大，投资者情绪偏向谨慎,市场可能继续探底。"
    
    # 主要判断逻辑
    if p_up > ABSOLUTE_BULLISH_THRESHOLD:
        return f"""【绝对牛市阶段】
                市场表现：超过60%的股票型基金近一个月年化收益率超10%，市场处于全面进攻期，情绪极度乐观。
                {divergence_note}{volatility_note}

                推荐关注板块：
                • 进攻型：科技（半导体、AI、互联网）、新能源车、军工
                • 周期向上：有色、煤炭、化工等景气周期板块

                规避板块：
                • 防御型：医药、消费、红利高股息（此阶段大概率落后大盘）

                操作建议：
                1. 继续满仓持有强势赛道基金，顺势而为
                2. 允许适度追高，但避免使用杠杆
                3. 警惕顶部剧烈震荡，设定止盈止损位
                4. 关注成交量和政策面变化，防范系统性风险"""

    elif p_down > ABSOLUTE_BULLISH_THRESHOLD:
        return f"""【绝对熊市阶段】

            市场表现：超过60%的股票型基金近一个月出现下跌，市场进入较深调整，恐慌情绪占主导。
            {divergence_note}{volatility_note}

            推荐关注板块：
            • 防御型：医药、必选消费（食品饮料、白酒）
            • 稳健型：红利高股息、公用事业、黄金
            • 价值型：银行、保险等低估值板块

            规避板块：
            • 高波动：科技、成长股、小盘股
            • 强周期：有色、化工、新能源等顺周期品种

            操作建议：
            1. 这是长期投资者最佳的低位布局窗口
            2. 建议开启或加大定投宽基指数（沪深300、中证500）
            3. 分批买入优质行业基金，跌得越深越值得关注
            4. 保持足够现金仓位，等待明确企稳信号"""

    elif p_up > p_down and (p_up - p_down) > STRENGTH_ADVANTAGE_THRESHOLD:
        return f"""【结构性牛市，偏强势】

                市场表现：上涨基金占比 {p_up:.0%}，领先下跌基金约 {p_up-p_down:.0%}，市场仍有上行动力。
                {divergence_note}{volatility_note}

                推荐关注板块：
                • 主线板块：科技、半导体、新能源、军工
                • 弹性品种：出口链、资源品（石油化工、有色）
                • 次优选择：消费（家电、旅游）、高端制造

                暂时规避：
                • 纯防御类：医药、红利高股息（抗跌但涨幅可能有限）

                操作建议：
                1. 继续持有并可适度加仓强势赛道基金
                2. 趋势未结束前不要轻易下车，但需控制仓位
                3. 关注板块轮动机会，避免过度追高
                4. 保留部分现金应对可能的调整"""

    elif p_down > p_up and (p_down - p_up) > STRENGTH_ADVANTAGE_THRESHOLD:
        return f"""【结构性熊市，偏弱势】

            市场表现：下跌基金占比 {p_down:.0%}，领先上涨基金约 {p_down-p_up:.0%}，市场短期承压。
            {divergence_note}{volatility_note}

            推荐关注板块：
            • 防御核心：医药（创新药、医疗器械）、必选消费
            • 稳健配置：红利高股息、银行、保险、公用事业
            • 避险资产：黄金及相关基金

            规避板块：
            • 高估值：科技（半导体、AI、计算机）
            • 强周期：新能源车、周期品、小盘成长

            操作建议：
            1. 降低总体股票仓位，控制风险暴露
            2. 优先配置防御类行业基金
            3. 耐心等待企稳信号，不急于抄底
            4. 少数抗跌的科技龙头可持有但不加仓"""

    else:
        return f"""【震荡市，多空平衡】

                市场表现：上涨与下跌基金数量接近，市场缺乏明确趋势，处于来回拉锯状态。
                {divergence_note}{volatility_note}

                短线投资者：
                • 关注热点轮动（AI→医药→消费→红利）
                • 小仓位波段操作，快进快出
                • 严格止损，控制单笔亏损

                长线投资者：
                • 保持定投节奏，不追涨杀跌
                • 优化持仓结构，汰弱留强
                • 等待下一轮趋势明确信号

                防御型投资者：
                • 超配红利高股息+黄金+债券混合基金
                • 注重资产配置的平衡性
                • 以稳健收益为主要目标

                总体建议：当前不宜重仓单一方向，分散配置与耐心持有是最优策略。关注政策面变化和资金流向，灵活调整战术。"""