"""用于记录 Top 100 名单"""
import os
import time
import json
log_path = os.path.join(os.getcwd(), 'log','log100.json')
today = time.strftime('%Y-%m-%d', time.localtime(time.time()))

def save_to_log(namelist):
    data = {}
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    data[today] = namelist 
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"成功记录 {today} 的 Top {len(namelist)} 名单")
