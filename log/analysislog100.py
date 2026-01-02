import time
import os
import json
import pandas as pd
import numpy as np
log_path = os.path.join(os.getcwd(), 'log','log100.json')
def analysis_log_single(singlelog,inputlogdata):
    """用于记录单个记录在top100中的排名历史"""
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if inputlogdata:
            data = inputlogdata
        ranking_history = []
        for date in data:
            namelist = data[date]
            if singlelog in namelist:
                current_rank = namelist.index(singlelog) + 1
                ranking_history.append((date, current_rank))
            else:
                pass
        return ranking_history


def analysis_log_batch(batchlog):
    """用于记录多个记录在top100中的排名历史"""
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    ranking_result = []
    for singlelog in batchlog:
        ranking_history = analysis_log_single(singlelog,data)
        ranking_result.append((singlelog,ranking_history))
    return ranking_result
    