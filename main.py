import sys
from PyQt5.QtWidgets import QApplication
from mainwindow import MainWindow
import traceback
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    # print("调用ARIMA预测")
    # traceback.print_stack()
    sys.exit(app.exec_())