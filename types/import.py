"""一键导入脚本"""
import akshare as ak
import os
import pandas as pd
balanced_path=os.path.join(os.getcwd(),'balanced')
Equity_path=os.path.join(os.getcwd(),'Equity')
index_path=os.path.join(os.getcwd(),'index')
Qdii_path=os.path.join(os.getcwd(),'Qdii')
Etf_path=os.path.join(os.getcwd(),'Etf')



def add_to_list():
    pass



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
        fund_name = fund_info_df[fund_info_df['item'] == '基金全称']['value'].iloc[0]
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
        elif 'ETF' in fund_name:
            save_to_folder(df, Etf_path, file_name)
            return
        else:
            print(f"未找到匹配的基金类型: {fund_type}")
    except Exception as e:
        print(f"没有找到或失败 {code}: {e}")
        return



def exam():
    pass


if __name__ == "__main__":
        i=10000
        code = str(i).zfill(6)
        where_to_go(code)