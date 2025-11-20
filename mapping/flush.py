import pandas as pd

def deduplicate_csv(file_path):
    """
    读取CSV文件，执行去重操作，并保存结果到新的文件。

    :param file_path: 你的CSV文件的完整路径
    """
    try:
        # 1. 读取CSV文件到DataFrame
        df = pd.read_csv(file_path)
        print(f"✅ 成功读取文件：{file_path}")
        
        # 🐛 修复：在这里定义 original_count 变量
        original_count = len(df)
        print(f"--- 原始记录数: {original_count} ---")

        # 2. 执行去重操作 (默认基于所有列)
        # keep='first' 表示保留第一次出现的记录，删除后续重复的记录。
        # inplace=True 表示在原始DataFrame上直接修改。
        df.drop_duplicates(keep='first', inplace=True)

        # 3. 计算并输出去重结果
        records_removed = original_count - len(df)
        print(f"--- 去除重复记录数: {records_removed} ---")
        print(f"--- 剩余不重复记录数: {len(df)} ---")
        
        # 4. 构造输出文件名
        # 在原文件名后加上 "_deduplicated"
        output_path = file_path.replace(".csv", "_deduplicated.csv")

        # 5. 保存去重后的数据到新的CSV文件
        # index=False 表示不将DataFrame的行索引写入CSV文件
        df.to_csv(output_path, index=False, encoding='utf-8-sig') 
        print(f"\n🎉 去重完成！结果已保存到：{output_path}")

    except FileNotFoundError:
        print(f"❌ 错误：找不到文件，请检查路径是否正确：{file_path}")
    except Exception as e:
        print(f"❌ 发生了一个错误: {e}")

# ----------------------------------------------------
# 📌 用户输入环节
# 请将下面的路径替换为你自己的CSV文件路径
# ----------------------------------------------------
# 你的文件路径是：A:\projects\money2\mapping\mapping_latestdate.csv
csv_file_path = "A:\\projects\\money2\\mapping\\mapping_latestdate.csv" 

# 调用函数执行去重
deduplicate_csv(csv_file_path)