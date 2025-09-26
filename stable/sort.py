import pandas as pd

# 读取 CSV 文件
df = pd.read_csv('stable.csv')

# 保证基金代码是六位数字，不足的补零
df['基金代码'] = df['基金代码'].astype(str).str.zfill(6)

# 按照基金代码列排序（按字符串排序，因为它已是六位数字格式）
df_sorted = df.sort_values(by='基金代码', ascending=True)

# 将排序后的结果保存到新的 CSV 文件
df_sorted.to_csv('sorted_file.csv', index=False)

print("排序完成！")
