import pandas as pd
import os
import akshare as ak

# 定义 mapping.csv 文件的路径
mapping_file_path = os.path.join('mapping', 'mapping.csv')

def get_fund_name(code):
    """根据六位基金代码返回基金名称"""
    code = str(code).zfill(6) 
    
    try:
        info = ak.fund_individual_basic_info_xq(symbol=code)
        print(f"Columns in response for {code}: {info.columns}")
        if 'item' in info.columns and 'value' in info.columns:
            # 提取基金全称
            fund_full_name: str = info[info['item'] == '基金全称']['value'].iloc[0]
            return fund_full_name
        else:
            print(f"Error: Missing expected columns for fund {code}")
            return None
    except KeyError as e:
        print(f"KeyError for fund {code}: {e}")
    except Exception as e:
        print(f"Error fetching fund name for code {code}: {e}")
    return None

if os.path.exists(mapping_file_path):
    df = pd.read_csv(mapping_file_path, header=None, names=['基金代码', '基金全称'])
    df['基金代码'] = df['基金代码'].apply(lambda x: str(x).zfill(6))
    for index, row in df.iterrows():
        try:
            if pd.notna(row['基金全称']):
                print(f"Skipping row {index} - {row['基金代码']}: Fund name already exists")
                continue
            fund_name = get_fund_name(row['基金代码'])
            if fund_name:
                df.at[index, '基金全称'] = fund_name
                print(f"Processed row {index} - {row['基金代码']}: {fund_name}")
            df.to_csv(mapping_file_path, index=False)
        except Exception as e:
            print(f"Error processing row {index}: {e}")

    print(f"Data has been successfully written to {mapping_file_path}")  # 确认保存
else:
    print(f"File {mapping_file_path} does not exist.")
