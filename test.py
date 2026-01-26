import akshare as ak

stock_code = "600519"
stock_info = ak.stock_individual_info_em(symbol=stock_code)
industry = stock_info[stock_info["item"] == "行业"]["value"].values[0]
# 打印结果，你会看到“行业”字段
print(industry)