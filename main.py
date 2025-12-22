import sys
from PyQt5.QtWidgets import QApplication
from mainwindow import MainWindow
import os
from PyQt5.QtGui import QIcon
import time
import glob

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    full_path = os.path.join(base_path, relative_path)
    return full_path


target_dir = get_resource_path('static')
timenow = time.strftime('%Y-%m-%d', time.localtime(time.time()))
current_month = int(time.strftime('%m', time.localtime(time.time())))

if 3 <= current_month <= 5:
    season = 'spring'
elif 6 <= current_month <= 8:
    season = 'summer'
elif 9 <= current_month <= 11:
    season = 'autumn'
else:
    season = 'winter'
pics = glob.glob(os.path.join(target_dir, f'{season}*.png'))
picdefault = glob.glob(os.path.join(target_dir, 'infinite.png'))
if pics:
    pic = pics[0]
elif picdefault:
    pic = picdefault[0]
else:
    pic = None # 如果都没找到，QIcon(None) 不会报错，只是没图标

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    if pic:
        icon = QIcon(pic)
        main_window.setWindowIcon(icon)
    main_window.show()
    sys.exit(app.exec_())
    