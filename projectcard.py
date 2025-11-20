import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
     QLabel, QFrame, QMessageBox,
    QDialog,QMenu,QAction,QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont 
from qdialogue import FundInfoDialog,List_group_dialog
import akshare as ak
import json
from signal_handler import signal_emitter
import pandas as pd 
from calculate_data import year_rate_sliding
from decision import decison_maker
import csv
TO_WORKER = "to_worker"
FOUND_PATH = "found"
Track_Json_Path = "track"


mapping = {}
mapping_latestdate = {}
mapping_path = os.path.join('mapping', 'mapping.csv')
mapping_latestdate_path = os.path.join('mapping', 'mapping_latestdate.csv')
groups_path = os.path.join(os.getcwd(), 'groups')

if os.path.exists(mapping_path):
    with open(mapping_path, 'r', encoding='utf-8') as f:
        for line in f:
            code, full_name = line.strip().split(',')
            mapping[code] = full_name

if os.path.exists(mapping_latestdate_path ):
    with open(mapping_latestdate_path , 'r', encoding='utf-8') as f:
        for line in f:
            path, latestdate = line.strip().split(',')
            mapping_latestdate[path] = latestdate
            
def save_new_mapping(code, full_name):
    """将新的映射保存到文件中"""
    with open(mapping_path, 'a', encoding='utf-8') as f:
        f.write(f"{code},{full_name}\n")

def get_name_by_mapping(code):
    """通过把mapping加载成字典找到对应的基金名称"""
    code_str = str(code)
    if code_str in mapping:
        return mapping[code_str]
    else:
        try:
            full_name = get_fund_name(code_str)
            if full_name:
                mapping[code_str] = full_name
                save_new_mapping(code_str, full_name)
                return full_name
            else:
                raise ValueError(f"无法通过外部查询获得基金代码 {code_str} 对应的基金名称")
        except Exception as e:
            raise ValueError(f"基金代码 {code_str} 没有找到对应的基金名称: {e}")

def get_fund_name(filename):
    """通过网络爬取akshare获得基金名称"""
    try:
        print('尝试得到基金名称')
        info = ak.fund_individual_basic_info_xq(symbol=filename)
        fund_full_name = info[info['item'] == '基金全称']['value'].iloc[0]
        return fund_full_name
    except IndexError:
        raise ValueError(f"无法从akshare查询到基金代码 {filename} 的信息")
    
def get_fund_info(filename):
        """根据六位基金代码返回基金信息，全局"""
        info=ak.fund_individual_basic_info_xq(symbol=filename)
        return info

def isflagged(filename):
    """判断文件是否在flagged.json中被标记"""
    json_path = os.path.join(Track_Json_Path, 'flagged.json')
    if not os.path.exists(json_path):
        return False
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            flagged_list = json.load(f)
            if isinstance(flagged_list, list) and filename in flagged_list:
                return True
        except (json.JSONDecodeError, FileNotFoundError):
            return False

def to_flag(filename):
    """
    把基金代码添加到 flagged.json 中。
    
    Args:
        filename (str): 要添加的基金代码，如 "000001"。
    """
    json_path = os.path.join(Track_Json_Path, 'flagged.json')
    flagged_list = []
    if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                flagged_list = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            flagged_list = []
    if filename not in flagged_list:
        flagged_list.append(filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(flagged_list, f, indent=4)
        signal_emitter.refresh_ui_signal.emit()

def to_unflag(filename):
    """
    把基金代码从 flagged.json 中删除。
    
    Args:
        filename (str): 要移除的基金代码，如 "000001"。
    """
    json_path = os.path.join(Track_Json_Path, 'flagged.json')
    # 如果文件不存在或为空，无需操作
    if not os.path.exists(json_path) or os.path.getsize(json_path) == 0:
        return
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            flagged_list = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # 如果文件内容无效，则无需操作
        return
    if filename in flagged_list:
        flagged_list.remove(filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(flagged_list, f, indent=4)
        signal_emitter.refresh_ui_signal.emit()



def get_latest_date_by_mapping(filepath):
    if filepath in mapping_latestdate:
        return mapping_latestdate[filepath]
    else:
        try:
            df = pd.read_csv(filepath)
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            latest_date = df['净值日期'].max()
            latest_date = latest_date.strftime('%Y-%m-%d')
            try:
                mapping_df = pd.read_csv(mapping_latestdate_path)
            except FileNotFoundError:
                # 如果文件不存在，则创建一个新的 DataFrame
                mapping_df = pd.DataFrame(columns=['path', 'date'])
            new_entry = pd.DataFrame({'path': [filepath], 'latest_date': [latest_date]})
            mapping_df = pd.concat([mapping_df, new_entry], ignore_index=True)
            mapping_df.to_csv(mapping_latestdate_path, index=False)
            return latest_date
        except Exception as e:
            print(f"无法读取文件 {filepath}: {e}")



class ProjectCard(QFrame):
    """根据文件路径加载的项目卡片"""
    visualize_requested = pyqtSignal(str)  # 发送文件路径，调用信号
    def __init__(self, file_path,parent=None):
        super().__init__(parent)
        self.file_path = file_path  # 当前基金的文件路径
        self.parent_widget = parent
        self.latest_date = get_latest_date_by_mapping(self.file_path)
        self.filename = os.path.splitext(os.path.basename(self.file_path))[0]  # 文件名
        self.fund_tittle: str = get_name_by_mapping(self.filename)  # 获取基金名称
        self._right_click = False
        signal_emitter.refresh_ui_signal.connect(self.update_flag_visibility)
        self.design()
        self.update_flag_visibility()
    def design(self):
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(1)
        layout = QVBoxLayout(self)
        # 第一层
        title_row_layout = QHBoxLayout()
        title_label = QLabel(f"{self.fund_tittle}")
        title_label.setFont(QFont('微软雅黑', 11))
        title_label.setAlignment(Qt.AlignLeft)
        self.flag_label = QLabel("🏴")
        self.flag_label.setFont(QFont('微软雅黑', 12))
        self.flag_label.setAlignment(Qt.AlignRight)
        title_row_layout.addWidget(title_label, 1)
        title_row_layout.addStretch(1)
        title_row_layout.addWidget(self.flag_label)
        layout.addLayout(title_row_layout)
        # 第二层
        row_layout = QHBoxLayout()
        file_label = QLabel(f"基金代码:{self.filename}  {self.latest_date} ") 
        file_label.setFont(QFont('微软雅黑', 10))
        file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        row_layout.addWidget(file_label, 1)
        layout.addLayout(row_layout)

    def show_fund_info(self):
        """在线显示基金信息对话框"""
        self.info_dialogue = FundInfoDialog(get_fund_info(self.filename))  # 获取基金信息并显示
        result = self.info_dialogue.exec_()
        if result == QDialog.Accepted:
            print("对话框被接受。")
        else:
            print("对话框被拒绝或关闭。")

    def discard(self):
        """丢弃操作：路径下的文件并刷新卡片"""
        target_path = self.file_path
        print(f"丢弃文件：{target_path}")
        if not target_path or not os.path.exists(target_path):
            QMessageBox.warning(self, "警告", f"文件 '{self.filename}' 不存在，无法丢弃。")
            return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认操作")
        msg_box.setIcon(QMessageBox.Warning)  # 设置警告图标
        msg_box.setText(f"确定要丢弃文件 '{self.filename}' 吗？")
        msg_box.setInformativeText("后续只能手动恢复")
        ok_button = msg_box.addButton("确定", QMessageBox.AcceptRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.RejectRole)
        msg_box.setDefaultButton(cancel_button)  # 设置“取消”为默认按钮
        font = QFont("微软雅黑", 12)
        msg_box.setFont(font)
        msg_box.exec_()
        if msg_box.clickedButton() == ok_button:
            try:
                os.remove(target_path)
                print(f"文件 '{self.filename}' 已成功删除")
                self.deleteLater()  # 删除后再清理对象
            except Exception as e:
                QMessageBox.warning(self, "错误", f"删除文件失败: {e}")





    def _emit_visualize_request(self):
        """当按钮点击时，发出 visualize_requested 信号，并传递文件路径"""
        self.visualize_requested.emit(self.file_path)

    def enterEvent(self, event):
        """鼠标进入时加粗外层边框"""
        self.setStyleSheet("""
            ProjectCard {
                border: 3px solid black;
                border-radius: 5px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时恢复边框宽度，只有在没有右键点击时才恢复"""
        # 只有在没有右键点击时才恢复边框
        if not self._right_click:
            self.setStyleSheet("""
                ProjectCard {
                    border: 1px solid black;
                    border-radius: 5px;
                }
            """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """重写鼠标事件，触发右键菜单，并标记是否右键点击"""
        if event.button() == Qt.RightButton:
            # 标记右键点击，阻止 leaveEvent 恢复边框
            self._right_click = True
            
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    border: 1px solid #4a4a4a;
                    padding: 0px; 
                    border-radius: 4px;
                }
                QMenu::item {
                    padding: 5px 15px;
                }
                QMenu::item:selected {
                    background-color: #dce4f0;
                }
            """)

            info_action = QAction("转到详细信息", self)
            info_action.triggered.connect(self.show_fund_info)
            
            visualize_action = QAction("转到图", self)
            visualize_action.triggered.connect(self._emit_visualize_request)
            
            caculate_year_rate_sliding_action = QAction("计算滑动年化收益", self)
            caculate_year_rate_sliding_action.triggered.connect(self.caculate_year_rate_sliding)
            
            current_is_flagged = isflagged(self.filename)#每一次右键触发检查
            if current_is_flagged:
                unflag_action = QAction("取消标记", self)
                unflag_action.triggered.connect(lambda: to_unflag(self.filename))#匿名函数
                unflag_action.setFont(QFont('微软雅黑', 11))
                menu.addAction(unflag_action)
            else:
                flag_action = QAction("标记", self)
                flag_action.triggered.connect(lambda: to_flag(self.filename))
                flag_action.setFont(QFont('微软雅黑', 11))
                menu.addAction(flag_action)
            discard_action = QAction("丢弃", self)
            discard_action.triggered.connect(self.discard)
            add_to_group_action = QAction("加入或转到已有分组", self)
            add_to_group_action.triggered.connect(lambda: self.add_to_group())
            
            add_to_group_action.setFont(QFont('微软雅黑', 11))
            discard_action.setFont(QFont('微软雅黑', 11))
            info_action.setFont(QFont('微软雅黑', 11))
            visualize_action.setFont(QFont('微软雅黑', 11))
            caculate_year_rate_sliding_action.setFont(QFont('微软雅黑', 11))

            menu.addAction(info_action)
            menu.addAction(visualize_action)
            menu.addAction(caculate_year_rate_sliding_action)
            menu.addAction(add_to_group_action)
            menu.addAction(discard_action)
            menu.exec_(event.globalPos())
            self.setStyleSheet("""
                ProjectCard {
                    border: 1px solid black;
                    border-radius: 10px;
                }
            """)
            self._right_click = False
        else:
            super().mousePressEvent(event)

    def update_flag_visibility(self):
        """根据json文件状态动态显示或隐藏旗帜。"""
        if isflagged(self.filename):
            self.flag_label.show()
        else:
            self.flag_label.hide()

    def caculate_year_rate_sliding(self):
        """计算年化收益率的滑动窗口"""
        df=pd.read_csv(self.file_path)
        year_rate_sliding(self.filename,df,base_date='2024-10-10',window_size_days=20,step_size_days=2)
        

    def add_to_group(self,straight_group_path=None):
        """加入或转到已有分组"""
        groups_path = os.path.join(os.getcwd(), 'groups')
        if straight_group_path:
            """直接定向加入系统分组"""
            print("直接定向加入系统分组")
            group_name = os.path.basename(straight_group_path)
            groups_cache_path = os.path.join(groups_path, 'group_cache.csv')
            
            if "系统" in group_name:
                if not os.path.exists(groups_cache_path):
                    with open(groups_cache_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        # 写入表头（如果需要）
                        writer.writerow(['group_name', 'file_path'])
            
            # 读取已有记录，检查是否存在相同的记录
            existing_records = set()  # 使用 set 来避免重复
            if os.path.exists(groups_cache_path):
                with open(groups_cache_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # 跳过表头
                    for row in reader:
                        existing_records.add(tuple(row))  # 将每一行记录存储为元组
            
            # 如果没有该记录，则添加
            if (self.file_path,group_name ) not in existing_records:
                with open(groups_cache_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.file_path, group_name])  # 写入数据
                print(f"数据已添加到 {groups_cache_path}")
            else:
                print("记录已经存在，跳过添加。")
        elif not straight_group_path:
            """添加到分组的对话框"""
            self.list_group_dialog = List_group_dialog(groups_path,"添加到分组",parent=None,this_code=self.filename)
            try:
                if self.list_group_dialog.exec_() == QDialog.Accepted:
                    this_group_path = self.list_group_dialog.get_selected_group_path()
                    group_name = os.path.basename(this_group_path)
                    self.massage_box = MessageBoxYesOrNo(self, title="确认加入分组", message=f"确认加入到 {group_name} 吗？")
                    self.group_cache_path = None
                    if self.massage_box.exec_():
                        try:
                            for root,_, files in os.walk(groups_path):
                                for file in files:
                                    if file == 'group_cache.csv':
                                        self.group_cache_path = os.path.join(root, file)
                                        print(f"找到 group_cache.csv 文件: {self.group_cache_path}")
                                        break
                            if not self.group_cache_path:
                                with open(os.path.join(groups_path, 'group_cache.csv'), 'w', newline='', encoding='utf-8') as f:
                                    writer = csv.writer(f)
                                    writer.writerow(['code', 'path', 'group_name','last_updated'])
                                self.group_cache_path = os.path.join(groups_path, 'group_cache.csv')
                            df=pd.read_csv(self.group_cache_path,header=0, index_col=False)
                            new_row = {'path': self.file_path, 'group_name': group_name}
                            if self.file_path in df['path'].values:
                                df.loc[df['path'] == self.file_path, ['group_name']] = [group_name]
                                df.to_csv(self.group_cache_path, index=False)
                                print(f"更新了基金 {self.filename} 的分组信息")
                            else:
                                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                                df.to_csv(self.group_cache_path, index=False)
                                print(f"添加了基金 {self.filename} 到分组 {group_name}")
                            try:
                                self.list_group_dialog.deleteLater()
                                base_path=self.parent_widget.base_path
                                if "groups" in base_path:
                                    self.deleteLater()
                            except Exception as e:
                                QMessageBox.warning(self, "错误", f"添加到分组对话框清理失败: {e}")
                            return
                        except Exception as e:
                            print(f"查找 group_cache.csv 失败: {e}")
                            return
                else:
                    print("对话框被拒绝或关闭。")
            except Exception as e:
                print(f"打开分组对话框失败: {e}")

           
    def auto_calculate_type(self,yearly_return_since_start=0.012,max_annualized_volatility=0.4):
        """自动计算类型,不好用"""
        self.decision_maker=decison_maker(fund_code=None,path=self.file_path,df=None)
        isthis_consider_risky_reward=self.decision_maker.get_risky_reward(yearly_return_since_start=yearly_return_since_start,max_annualized_volatility=max_annualized_volatility)
        isthis_consider_long_term_return=self.decision_maker.get_long_term_return(days_since_start=1618)
        isthis_consider_low_point=self.decision_maker.get_low_point(days_since_start=1618)
        return isthis_consider_risky_reward,isthis_consider_long_term_return,isthis_consider_low_point

    def return_decision(self):
        self.decision_maker=decison_maker(fund_code=None,path=self.file_path,df=None)
        return self.decision_maker


class MessageBoxYesOrNo(QMessageBox):
    def __init__(self, parent=None, title="提示", message="确定吗？"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setText(message)

        # 设置中文按钮
        self.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.button(QMessageBox.Yes).setText("确认")
        self.button(QMessageBox.No).setText("取消")
        self.setFont(QFont("微软雅黑", 10))

    def exec_(self):
        response = super().exec_()
        if response == QMessageBox.Yes:
            return True  # 用户点击了“确认”
        elif response == QMessageBox.No:
            return False  # 用户点击了“取消”
        return None  # 如果出现其他情况