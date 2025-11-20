
import os
import akshare as ak
import pandas as pd
from datetime import datetime,date
import csv
balanced_path=os.path.join(os.getcwd(),'balanced')
Equity_path=os.path.join(os.getcwd(),'Equity')
index_path=os.path.join(os.getcwd(),'index')
Qdii_path=os.path.join(os.getcwd(),'Qdii')
# ['混合型-偏股', '混合型-宏观策略', '混合型-灵活配置', '混合型-偏债', '混合型-股票对冲', 
#  '混合型-事件驱动', '混合型-股债平衡', 'QDII-混合', 'FOF-偏债混合', 'FOF-偏股混合', '混合型-其他']



def save_to_folder(df, base_path, file_name):
    try:
        file_path = os.path.join(base_path, file_name)
        print(f"成功保存 {file_name} 到 {base_path} 文件夹")
        if os.path.exists(file_path):
            pass
        else:
            df.to_csv(file_path, index=False, encoding='utf-8')
    except Exception as e:
        print(f"保存文件 {file_name} 时出错: {e}")

def where_to_go(code):
    "根据基金代码拿到数据，保存到文件夹"
    print(f'开始处理{code}')
    try:
        fund_info_df = ak.fund_individual_basic_info_xq(symbol=code)
        fund_type = fund_info_df[fund_info_df['item'] == '基金类型']['value'].iloc[0]
        df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
        file_name = f"{code}.csv"
        if '混合' in fund_type:
            save_to_folder(df, balanced_path, file_name)
            return
        elif '股票' in fund_type:
            save_to_folder(df, Equity_path, file_name)
            return
        elif '指数' in fund_type:
            save_to_folder(df, index_path, file_name)
            return
        elif 'QDII' in fund_type:
            save_to_folder(df, Qdii_path, file_name)
            return
        else:
            print(f"未找到匹配的基金类型: {fund_type}")
    except Exception as e:
        print(f"没有找到或失败 {code}: {e}")
        return



def update_files(path, cache_path, progress_callback=None):
    """
    更新所有文件, 支持断点续传。每个文件更新后调用 progress_callback 更新进度。
    """
    today = date.today()
    
    # --- 1. 路径和文件准备 ---
    try:
        all_files = os.listdir(path)
    except FileNotFoundError:
        # 如果path不存在，说明分组目录有问题，直接返回
        print(f"错误：分组路径不存在或无法访问：{path}")
        return

    csv_files = [file for file in all_files if file.endswith('.csv')]
    total_len = len(csv_files)
    count = 1

    try:
        # 尝试读取缓存文件，如果文件不存在，将由调用者处理 FileNotFoundError
        cache_df = pd.read_csv(cache_path)
    except FileNotFoundError:
        # 此处只是打印错误，但程序会继续运行，可能会在后面的代码中失败
        print(f"致命错误：未找到缓存文件 {cache_path}，无法进行断点续传。")
        return

    # --- 2. 遍历并更新文件 ---
    for single in csv_files:
        file_path = os.path.join(path, single)
        fund_code = single.split('.')[0]
        
        try:
            # 🌟 修复核心逻辑：安全地从缓存中获取日期 🌟
            # 1. 查找匹配的日期 Series
            date_series = cache_df.loc[cache_df['path'] == file_path, 'latest_date']

            # 2. 检查 Series 长度，安全提取单值
            if len(date_series) == 1:
                # 找到唯一匹配项，安全提取值
                cached_date = str(date_series.iloc[0]) 
            elif len(date_series) == 0:
                # 缓存中没有该文件的记录，视为从未更新过
                cached_date = '1970-01-01' 
            else:
                # 致命数据错误：路径重复
                print(f"致命数据错误：缓存中存在多条记录匹配路径 {file_path}，跳过更新。")
                count += 1
                if progress_callback:
                    progress_callback(count, total_len)
                continue
            
            # --- 3. 比较日期和更新逻辑 ---
            
            if cached_date == today.strftime('%Y-%m-%d'):
                # 缓存日期等于今天，跳过
                print(f'{single} 缓存中已经是最新，跳过更新 ({count}/{total_len})。')
                
            else:
                # 需要进行数据请求和更新
                print(f'{single} 正在进行网络请求...')
                
                # 网络请求
                data = ak.fund_open_fund_info_em(symbol=fund_code, indicator="累计净值走势")
                
                # 数据处理
                if data is None or data.empty:
                    print(f'{single} 警告：akshare返回空数据，跳过写入 ({count}/{total_len})。')
                    count += 1
                    if progress_callback:
                        progress_callback(count, total_len)
                    continue

                data["净值日期"] = pd.to_datetime(data['净值日期'])
                latest_date = data['净值日期'].max()
                latest_date_str = latest_date.strftime('%Y-%m-%d')
                
                # 检查最新日期是否与缓存日期一致（数据源尚未更新）
                if latest_date_str == cached_date:
                    print(f'{single} 数据源未更新，缓存已是最新，跳过写入缓存 ({count}/{total_len})。')
                else:
                    # 写入数据和更新缓存
                    output_path = os.path.join(path, single)
                    data.to_csv(output_path, index=False)
                    
                    # 更新缓存 DataFrame
                    # 使用布尔索引查找并更新 latest_date
                    cache_df.loc[cache_df['path'] == file_path, 'latest_date'] = latest_date_str
                    
                    # 写入缓存文件
                    cache_df.to_csv(cache_path, index=False)
                    
                    print(f'{single} 更新成功 ({count}/{total_len})，更新日期为 {latest_date_str}。缓存已同步写入。')
                    
            # --- 4. 进度更新 ---
            count += 1
            if progress_callback:
                progress_callback(count, total_len)
                
        except Exception as e:
            # 捕获 akshare 网络错误、文件写入错误等
            print(f"更新失败 {fund_code}: {e}")
            count += 1
            if progress_callback:
                progress_callback(count, total_len)
            continue
            
    print('所有文件更新处理完成！')

def de_dupulicate(path):
    """
    读取指定路径的 CSV 文件（缓存文件），根据 'path' 列去重。

    Args:
        path (str): CSV 文件的完整路径（即缓存文件的地址）。
    """
    if not os.path.exists(path):
        print(f"错误：未找到文件，路径为 {path}")
        return
    try:
        cache_df = pd.read_csv(path)
        if 'path' not in cache_df.columns:
            print(f"错误：文件 {path} 中未找到 'path' 列，无法去重。")
            return
        initial_rows = len(cache_df)
        df_deduplicated = cache_df.drop_duplicates(subset=['path'], keep='last')
        final_rows = len(df_deduplicated)
        df_deduplicated.to_csv(path, index=False)
        print(f"文件去重成功：{path}")
        print(f" - 原始行数: {initial_rows}")
        print(f" - 去重后行数: {final_rows}")
        print(f" - 移除了重复行数: {initial_rows - final_rows}")
    except pd.errors.EmptyDataError:
        print(f"警告：文件 {path} 为空，无需处理。")
    except Exception as e:
        print(f"处理文件 {path} 时发生未知错误: {e}")




def exam(path):
    """查看所有文件的基金类型"""
    all_files = os.listdir(path)
    csv_files = [file for file in all_files if file.endswith('.csv')]
    total_len=len(csv_files)
    count=1
    storage=[]
    for single in csv_files:
        fund_code = single.split('.')[0]
        try:
            print(f'处理{total_len}中的第{count}个')
            fund_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
            fund_type = fund_info_df[fund_info_df['item'] == '基金类型']['value'].iloc[0]
            if fund_type not in storage:
                storage.append(fund_type)
            else:
                pass
            count+=1
        except Exception as e:
            print(f"失败 {fund_code}: {e}")
    print(storage)
            
def flush(path):
    """危险方法"""
    all_files = os.listdir(path)
    csv_files = [file for file in all_files if file.endswith('.csv')]
    total_len=len(csv_files)
    count=1
    del_count=0
    for single in csv_files:
        fund_code = single.split('.')[0]
        try:
            fund_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
            fund_type = fund_info_df[fund_info_df['item'] == '基金类型']['value'].iloc[0]
            if'FOF'in fund_type:
                single_path=os.path.join(path,single)
                os.remove(single_path)
                print(f'{single}删除成功,{total_len}中的第{count}个')
                del_count+=1
            else:
                print(f'{fund_type}未删除，{total_len}中的第{count}个')
                pass
            count+=1
        except Exception as e:
            print(f"失败 {fund_code}: {e}")
    print(f'任务完成，成功删除{del_count}个文件')

def recover():
    list=['000216', '000217', '000218', '000307', '000929', '000930', '002610', '002611', '002963', '004253', '007910', '007911', '007937', '007938', '008142', '008143', '008701', '008702', '008827', '008828', '008986', '008987', '009033', '009034', '009198', '009477', '009478', '009504', '009505', '014661', '014662', '016581', '016582', '018391', '018392', '019005']
    count=0
    for single in list:
        try:
            df=ak.fund_open_fund_info_em(symbol=single, indicator="累计净值走势")
            file_name = f"{single}.csv"
            full_path=os.path.join(Qdii_path,file_name)
            print(full_path)
            df.to_csv(full_path,index=False)
            print(f'{single}写入成功')
            count+=1
        except Exception as e:
            print(f"失败 {single}: {e}")
    print(f'任务完成，成功写入{count}个文件')

def flush_those_outdated():
    """危险方法"""
    mapping_path = r"A:\projects\money2\mapping\mapping_latestdate.csv"
    df = pd.read_csv(mapping_path)
    df['latest_date'] = pd.to_datetime(df['latest_date'])
    threshold_date = datetime(2025, 9, 1)
    files_to_delete = df[df['latest_date'] < threshold_date]
    num=0
    for index, row in files_to_delete.iterrows():
        file_path = row['path']
        if os.path.exists(file_path):
            try:
                os.remove(file_path)  # 删除文件
                print(f"已删除文件: {file_path}")
                num+=1
            except Exception as e:
                print(f"删除文件失败: {file_path}，错误: {e}")
        else:
            print(f"文件不存在: {file_path}")
    df = df[df['latest_date'] >= threshold_date]
    df.to_csv(mapping_path, index=False)
    print(f"任务完成，成功删除{num}个文件")



def collect_csv_files():   
    csv_files = []
    for file in os.listdir(balanced_path):
        if file.endswith('.csv'):
            file=file.split('.')[0]
            if file not in csv_files:
                csv_files.append(file)
    for file in os.listdir(Equity_path):
        if file.endswith('.csv'):
            file=file.split('.')[0]
            if file not in csv_files:
                csv_files.append(file)
    for file in os.listdir(Qdii_path):
        if file.endswith('.csv'):
            file=file.split('.')[0]
            if file not in csv_files:
                csv_files.append(file)
    for file in os.listdir(index_path):
        if file.endswith('.csv'):
            file=file.split('.')[0]
            if file not in csv_files:
                csv_files.append(file)
    if csv_files:
        with open('collect_list.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['File Name'])  # 写入列标题
            for csv_file in csv_files:
                writer.writerow([csv_file])  # 写入每个文件名
        print(f'共找到 {len(csv_files)} 个 CSV 文件，并已保存到 collect_list.csv')
    else:
        print('未找到任何 CSV 文件')

if __name__ == "__main__":
       for code in range(28000,30000):
            zfilledcode=str(code).zfill(6)
            where_to_go(zfilledcode)
        
        
