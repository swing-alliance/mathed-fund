from virtual_calculate import max_sharp_ratio_for_days
from virtual.virtual_df_split import get_dataframe_by_path,split_dataframe

if __name__ == "__main__":
    df=get_dataframe_by_path('A:\\projects\\money2\\my_types\\Qdii\\501018.csv')
    split_df=split_dataframe(df,'2025-06-15','2026-03-15')
    print(max_sharp_ratio_for_days(split_df,period_days=60))