# 数据分割
import pandas as pd

def split_dataframe(dataframe, start_time, end_time):
    """
    根据开始和结束时间分割 DataFrame。
    支持字符串格式或 datetime 格式的输入。
    """
    try:
        # 1. 拷贝一份数据，避免 SettingWithCopyWarning
        df = dataframe.copy()
        
        # 2. 确保日期列是 datetime 类型
        # 注意：请根据你实际的列名修改 '净值日期'
        date_col = '净值日期'
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 3. 将日期设为索引并排序（切片的前提是索引有序）
        df = df.set_index(date_col).sort_index()
        
        # 4. 使用 loc 进行闭区间切片 [start_time, end_time]
        # pandas 的 loc 对日期字符串非常友好，支持 '2016-06-15' 这种格式
        result = df.loc[start_time : end_time]
        
        # 5. 如果需要还原索引，可以 reset_index
        return result.reset_index()
    except:
        return pd.DataFrame()  # 返回空 DataFrame 以避免错误

def get_dataframe_by_path(path):
    """
    从指定路径加载 DataFrame。
    这里假设数据是 CSV 格式的，你可以根据实际情况修改。
    """
    return pd.read_csv(path)


if __name__ == "__main__":
    # 示例用法
    path = 'A:\\projects\\money2\\my_types\\Qdii\\501018.csv'  # 替换为你的数据路径
    df = get_dataframe_by_path(path)
    
    start_time = '2025-06-15'
    end_time = '2026-0315'
    
    split_df = split_dataframe(df, start_time, end_time)
    print(split_df)