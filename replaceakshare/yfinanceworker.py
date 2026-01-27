import yfinance as yf
import pandas as pd
import os
from config.get_config import get_proxy_config

# 1. 全局配置与代理设置
try:
    proxy_port = get_proxy_config()
    PROXY_URL = f"http://127.0.0.1:{proxy_port}"
    yf.set_config(proxy=PROXY_URL)
except Exception as e:
    print(f"代理配置加载失败: {e}")

# 2. 核心行业映射库 (直接手动维护，性能最强)
# 涵盖了 Yahoo Finance 绝大多数常见行业
INDUSTRY_MAPPING = {
    # --- 科技与电子 ---
    "Semiconductors": "半导体",
    "Semiconductor Equipment & Materials": "半导体设备与材料",
    "Electronic Components": "电子元件",
    "Communication Equipment": "通信设备",
    "Consumer Electronics": "消费电子",
    "Computer Hardware": "电脑硬件",
    "Software - Infrastructure": "软件基础架构",
    "Software - Application": "软件应用",
    "Internet Content & Information": "互联网内容与信息",
    "Information Technology Services": "信息技术服务",
    "Electronic Gaming & Multimedia": "电子游戏与多媒体",
    "Security & Protection Services": "安全与防护服务",
    "Advertising Agencies": "广告代理",

    # --- 医疗与生物 ---
    "Biotechnology": "生物技术",
    "Drug Manufacturers - General": "制药",
    "Drug Manufacturers - Specialty & Generic": "专科药与仿制药",
    "Medical Devices": "医疗器械",
    "Medical Instruments & Supplies": "医疗器械与用品",
    "Medical Care Facilities": "医疗护理机构",
    "Health Information Services": "健康信息服务",
    "Diagnostics & Research": "诊断与研究",

    # --- 金融、房地产与服务 ---
    "Banks - Regional": "区域性银行",
    "Banks - Diversified": "综合性银行",
    "Asset Management": "资产管理",
    "Credit Services": "信贷服务",
    "Capital Markets": "资本市场",
    "Insurance - Diversified": "综合保险",
    "Insurance - Life": "人寿保险",
    "Real Estate - Development": "房地产开发",
    "Real Estate - Diversified": "综合房地产",
    "Real Estate Services": "房地产服务",
    "REIT - Healthcare Facilities": "医疗保健信托",
    "REIT - Industrial": "工业地产信托",
    "REIT - Specialty": "特种地产信托",
    "REIT - Retail": "零售地产信托",
    "REIT - Diversified": "综合地产信托",

    # --- 工业、制造与资源 ---
    "Auto Manufacturers": "汽车制造",
    "Auto Parts": "汽车零部件",
    "Specialty Industrial Machinery": "特种工业机械",
    "Electrical Equipment & Parts": "电气设备与零件",
    "Aerospace & Defense": "航空航天与国防",
    "Farm & Heavy Construction Machinery": "农用与重型工程机械",
    "Specialty Chemicals": "特种化工",
    "Chemicals": "基础化工",
    "Metals & Mining": "金属与采矿",
    "Other Industrial Metals & Mining": "其他工业金属采矿",
    "Copper": "铜业",
    "Aluminum": "铝业",
    "Gold": "黄金",
    "Metal Fabrication": "金属制品",
    "Tools & Accessories": "工具配件",
    "Building Materials": "建筑材料",
    "Building Products & Equipment": "建筑产品与设备",
    "Engineering & Construction": "工程建设",
    "Textile Manufacturing": "纺织制造",
    "Packaging & Containers": "包装与容器",
    "Business Equipment & Supplies": "商业办公设备",

    # --- 能源与公用事业 ---
    "Oil & Gas E&P": "石油天然气开采",
    "Oil & Gas Integrated": "综合油气",
    "Oil & Gas Equipment & Services": "油气设备与服务",
    "Utilities - Independent Power Producers": "独立发电厂",
    "Utilities - Regulated Electric": "管制电力",
    "Pollution & Treatment Controls": "污染治理与控制",

    # --- 消费、零售与交通 ---
    "Internet Retail": "互联网零售",
    "Beverages - Wineries & Distilleries": "饮料与酿酒",
    "Beverages - Brewers": "饮料与啤酒",
    "Beverages - Non-Alcoholic": "非酒精饮料",
    "Packaged Foods": "包装食品",
    "Farm Products": "农产品",
    "Luxury Goods": "奢侈品",
    "Furnishings, Fixtures & Appliances": "家具、装置与家电",
    "Recreational Vehicles": "房车与休闲车",
    "Lodging": "住宿酒店",
    "Airlines": "航空公司",
    "Telecom Services": "电信服务",
}




def clean_and_format_code(raw_code):
    """
    终极转换逻辑：
    1. 含有 2 个及以上字母 -> 视为美股/特殊，去掉前导 0。
    2. 含有原始后缀 (.SS/.SZ/.HK) -> 保持现状。
    3. 纯数字 -> 根据 A股/港股规则补全。
    """
    raw_str = str(raw_code).strip().upper()
    
    # 统计原始字符串中的字母数量 (不含点号)
    letter_count = sum(1 for char in raw_str if char.isalpha())

    # --- 逻辑 1：处理美股/特殊代码 (如 00AAPL, 00AVGO) ---
    if letter_count >= 2 and not (raw_str.endswith('.SS') or raw_str.endswith('.SZ') or raw_str.endswith('.HK')):
        # 去掉前导0并返回。例如 '00AAPL' -> 'AAPL'
        return raw_str.lstrip('0')

    # --- 逻辑 2：如果已经带有 yfinance 识别的后缀，直接返回 ---
    if raw_str.endswith(('.SS', '.SZ', '.HK')):
        return raw_str

    # --- 逻辑 3：处理不带后缀的清洗逻辑 ---
    c_str = raw_str.replace('SH', '').replace('SZ', '')
    
    if c_str.isdigit():
        if len(c_str) <= 5: 
            # 港股补齐 5 位。例如 '9988' -> '09988.HK' (阿里巴巴)
            return f"{c_str.zfill(5)}.HK"
        elif c_str.startswith(('6', '9', '5')): 
            return f"{c_str}.SS"
        else: 
            return f"{c_str}.SZ"
            
    return c_str






def fetch_single_pct(raw_code):
    """抓取单个标的的涨跌幅"""
    yf_code = clean_and_format_code(raw_code)
    try:
        ticker = yf.Ticker(yf_code)
        hist = ticker.history(period="5d", interval="1d")
        if len(hist) >= 2:
            last_close, prev_close = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            return raw_code, round(float(((last_close / prev_close) - 1) * 100), 2)
    except Exception as e:
        print(f"⚠️ 涨跌幅抓取失败 [{yf_code}]: {e}")
    return raw_code, None

def get_universal_pct_change(codes):
    """获取涨跌幅汇总"""
    return {c: p for c, p in [fetch_single_pct(code) for code in codes]}

def get_stock_industry_yfinance(stock_codes):
    """返回字典格式：{'600519': '白酒', 'AAPL': '消费电子'}"""
    results = {}
    for code in stock_codes:
        # 使用你优化后的 clean_and_format_code
        yf_code = clean_and_format_code(code)
        try:
            ticker = yf.Ticker(yf_code)
            # 获取行业
            eng = ticker.info.get('industry') or ticker.info.get('sector')
            if eng:
                # 使用本地映射表翻译
                zh = INDUSTRY_MAPPING.get(eng, eng)
                results[code] = zh
        except Exception as e:
            print(f"抓取 {code} 失败: {e}")
    return results

if __name__ == "__main__":
    print(clean_and_format_code("00AAPL"))