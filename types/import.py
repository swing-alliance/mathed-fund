"""一键导入脚本"""
import akshare as ak
import os
import pandas as pd
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

def update(path):
    """输入文件夹路径，更新所有文件"""
    all_files = os.listdir(path)
    csv_files = [file for file in all_files if file.endswith('.csv')]
    total_len=len(csv_files)
    count=1
    for single in csv_files:
        fund_code = single.split('.')[0]
        try:
            data=ak.fund_open_fund_info_em(symbol=fund_code, indicator="累计净值走势")
            output_path=os.path.join(path,single)
            data.to_csv(output_path,index=False)
            print(f'{single}更新成功,{total_len}中的第{count}个')
            count+=1
        except Exception as e:
            print(f"失败 {fund_code}: {e}")


def exam(path):
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



import os
import csv

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

    # 保存到 collect_list.csv 文件
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
        # i=10000
        # code = str(i).zfill(6)
        # where_to_go(code)
        # output=update(Equity_path)
        # exam(balanced_path)
        flush(balanced_path)
        #  collect_csv_files()
        
        
