import os
import pandas as pd
import akshare as ak
import pull

file_path = os.path.join(os.getcwd(), 'found')
if not os.path.exists(file_path):
    os.makedirs(file_path)

def main(codes_range=(1, 10000)):
    pull.main(codes_range=codes_range)





if __name__ == '__main__':
    main(codes_range=(1, 10000))