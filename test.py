import akshare as ak
import pandas as pd

# 定义你想要查询的六位基金代码
fund_code = "000001"

# # 模拟数据 (你也可以通过接口获取这个信息)
# data = {
#     'item': ['基金代码', '基金名称', '基金全称', '成立时间', '最新规模', '基金公司', '基金经理', 
#              '托管银行', '基金类型', '评级机构', '基金评级', '投资策略', '投资目标', '业绩比较基准'],
#     'value': ['000001', '华夏成长混合', '华夏成长证券投资基金', '2001-12-18', '26.00亿', '华夏基金管理有限公司', 
#               '刘睿聪 郑晓辉', '中国建设银行股份有限公司', '混合型-偏股', '<NA>', '暂无评级', '在股票投资方面，本基金...', '本基金属成长型基金...', '本基金暂不设业绩比较基准']
# }
# df = pd.DataFrame(data)

# # 从模拟数据中提取基金全称
# fund_full_name = df[df['item'] == '基金全称']['value'].iloc[0]

# 调用接口获取基金基本信息
fund_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
this_df = pd.DataFrame(fund_info_df)
fund_full_name = fund_info_df[fund_info_df['item'] == '基金全称']['value'].iloc[0]
# 打印接口返回的数据
print("这是列表信息:")
print(fund_info_df.columns)
print('这是全部信息:')
print(fund_info_df)
print('这是基金全称:')
print(fund_info_df['value'][fund_info_df['item'] == '基金全称'])
# 打印提取的基金全称
print("基金全称:", fund_full_name)
print('测试:',fund_info_df[fund_info_df['item'] == '基金全称']['value'])