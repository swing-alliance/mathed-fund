"30天"：
order = 5
period = "日"
custom_period = 30
detrend = True
sampling = 1
window = 30
smoothing = 0.2
expect_days = 30
extrapolation_strategy = "直接外推

"60天";
order = 7
period = "日"
custom_period = 30
detrend = True
sampling = 1
window = 60
smoothing = 0.2
expect_days = 60
extrapolation_strategy = "直接外推"

"90天":
order = 10
period = "周"
custom_period = 13    # 一季度大约13周
detrend = True
sampling = 2
window = 90
smoothing = 0.25
expect_days = 60
extrapolation_strategy = "滚动窗口预测"

"180 天":
order = 15
period = "周"
custom_period = 26    # 半年约26周
detrend = True
sampling = 3
window = 180
smoothing = 0.3
expect_days = 180
extrapolation_strategy = "滚动窗口预测"

"1年":
order = 25
period = "月"
custom_period = 12    # 一年12个月
detrend = True
sampling = 5
window = 252
smoothing = 0.35
expect_days = 252
extrapolation_strategy = "与趋势模型融合"

"2年":
order = 50
period = "月"
custom_period = 24    # 两年24个月
detrend = True
sampling = 5
window = 504
smoothing = 0.4
expect_days = 504
extrapolation_strategy = "与趋势模型融合"

"3年":
order = 75
period = "月"
custom_period = 36    # 三年36个月
detrend = True
sampling = 7
window = 756
smoothing = 0.45
expect_days = 756
extrapolation_strategy = "与趋势模型融合"
