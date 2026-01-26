import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from translate import Translator as SimpleTranslator
import pandas as pd
# 1. 全局配置
PROXY_URL = "http://127.0.0.1:10809"

# 关键改动：yfinance 新版本支持通过 set_config 启用 curl_cffi 模拟浏览器
# 这将自动处理 TLS 指纹，不再需要手动传 session
yf.set_config(proxy=PROXY_URL)


def fetch_single_pct(raw_code):
        c_str = str(raw_code).strip().upper()
        # 后缀转换逻辑
        if c_str.isdigit() and len(c_str) <= 5:
            yf_code = f"{c_str.zfill(4)}.HK" 
        elif c_str.isdigit() and len(c_str) == 6:
            yf_code = f"{c_str}.SS" if c_str.startswith(('6', '9')) else f"{c_str}.SZ"
        else:
            yf_code = c_str
        try:
            # 使用 period="5d" 提高容错，防止遇到长假
            # 注意：这里不传入 session，由 yfinance 自动处理 curl_cffi 环境
            ticker = yf.Ticker(yf_code)
            hist = ticker.history(period="5d", interval="1d")
            
            if len(hist) >= 2:
                # 取最后两个有效交易日的收盘价
                last_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                pct = ((last_close / prev_close) - 1) * 100
                return raw_code, round(float(pct), 2)
        except Exception as e:
            print(f"⚠️ 标的 {yf_code} 抓取失败: {e}")
        return raw_code, None




def get_universal_pct_change(codes):
    """
    多线程稳健版：支持全球标的
    将批量请求拆分为独立线程，提高 Crumb 校验通过率并防止数据丢失
    """
    result= {}
    try:
        for code in codes:
            single_pct=fetch_single_pct(code)
            result[single_pct[0]]=single_pct[1]
        return result
    except Exception as e:
        print(f"全局涨跌幅抓取错误: {e}")
        return result

def get_stock_industry_yfinance(stock_codes):
    """使用 curl_cffi 环境获取行业信息"""
    if not stock_codes: return None
    translator = SimpleTranslator(from_lang="en", to_lang="zh")
    def fetch_and_translate(code):
        c_str = str(code).strip().upper()
        # 代码转换逻辑...
        if c_str.isdigit():
            if len(c_str) <= 5: yf_code = f"{c_str.zfill(4)}.HK"
            elif c_str.startswith(('6', '9')): yf_code = f"{c_str}.SS"
            else: yf_code = f"{c_str}.SZ"
        else:
            yf_code = c_str
        try:
            # 核心改动：不要传入 session=shared_session
            # yfinance 发现环境下有 curl_cffi 会自动调用它来绕过 Crumb
            ticker = yf.Ticker(yf_code)
            info = ticker.info
            eng_industry = info.get('industry') or info.get('sector')
            if not eng_industry: return None
            
            return translator.translate(eng_industry)
        except Exception as e:
            # 如果还是报错，说明 Yahoo 封锁了当前代理 IP
            print(f"行业抓取失败 [{yf_code}]: {e}")
            return None

    industry_list = []
    try:
        print(f"🔍 正在获取 {len(stock_codes)} 个标的的行业信息...")
        # 线程数不要开太大，Yahoo 对 info 接口监控很严
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(fetch_and_translate, c) for c in stock_codes]
            for f in as_completed(futures):
                res = f.result()
                if res: industry_list.append(res)

        unique_industries = list(dict.fromkeys([i.strip() for i in industry_list if i]))
        return " | ".join(unique_industries) if unique_industries else "未知行业"
    except Exception as e:
        print(f"全局行业抓取错误: {e}")
        return None

# --- 测试运行 ---
if __name__ == "__main__":
    test_codes = ["600879", "700", "AAPL", "NVDA", "002475"]

    print(get_universal_pct_change(test_codes))