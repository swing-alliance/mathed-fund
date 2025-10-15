import os
import csv
import pandas as pd

dates_mapping_path=r'A:\projects\money2\mapping\mapping_latestdate.csv'


df=pd.read_csv(dates_mapping_path)
df['path']