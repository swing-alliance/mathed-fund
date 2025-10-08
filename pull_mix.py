import os
import pandas as pd
import akshare as ak
import multiprocessing
from filelock import FileLock

# 设置文件保存路径和文件路径
output_dir = './stable'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

output_file_path = os.path.join(output_dir, "stable.csv")
lock_file_path = os.path.join(output_dir, "stable.csv.lock") # 锁文件的路径

def fetch_and_write(code):
    """
    尝试拉取并写入单个基金代码，无重试。
    """
    try:
        fund_info_df = ak.fund_individual_basic_info_xq(symbol=code)
        
        if fund_info_df is not None and not fund_info_df.empty:
            fund_type = fund_info_df.loc[fund_info_df['item'] == '基金类型', 'value'].values[0]
            if "混合" in fund_type:
                # 使用文件锁确保进程安全地写入文件
                lock = FileLock(lock_file_path)
                with lock:
                    with open(output_file_path, 'a', encoding="utf-8-sig") as f:
                        f.write(f"{code}\n")
    except Exception:
        # 捕获所有异常，但不做任何处理，直接跳过
        pass

def fetch_mixed_fund_codes_process(start_code, end_code):
    """
    每个进程抓取一部分基金代码并筛选。
    """
    for code_num in range(start_code, end_code + 1):
        code = f"{code_num:06d}"
        fetch_and_write(code)

def main(codes_range=(1, 999999), num_processes=3):
    """
    多进程抓取基金数据的主控函数。
    """
    # 预先创建或清空文件并写入表头
    with open(output_file_path, 'w', encoding="utf-8-sig") as f:
        f.write("基金代码\n")

    processes = []
    step = (codes_range[1] - codes_range[0] + 1) // num_processes

    for i in range(num_processes):
        start_code = codes_range[0] + i * step
        end_code = start_code + step - 1 if i < num_processes - 1 else codes_range[1]
        process = multiprocessing.Process(target=fetch_mixed_fund_codes_process, args=(start_code, end_code))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    # 统计最终结果（可选）
    try:
        df = pd.read_csv(output_file_path, encoding="utf-8-sig")
        print(f"共保存 {len(df)} 条混合型基金代码，保存路径：{output_file_path}")
    except FileNotFoundError:
        print(f"文件未找到，可能没有抓取到任何数据。")

if __name__ == '__main__':
    main(codes_range=(1, 10000))