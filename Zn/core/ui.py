import os
import time
import calendar
import random
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem, QPushButton, 
                             QTextEdit, QLineEdit, QFormLayout, QMessageBox, 
                             QWidget, QTabWidget, QGroupBox, QComboBox, QDoubleSpinBox,
                             QProgressBar, QStackedWidget, QSplitter, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor, QTextCursor

from config import get_asset_path, MODEL_CONFIGS, save_api_configs, load_api_configs

# ================= 【新增】开发者控制台 =================
class DeveloperConsole(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("👨‍💻 Zn 开发者监控终端")
        self.resize(600, 400)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; }
            QTextEdit { 
                background-color: #1e1e1e; 
                color: #00ff00; 
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: none;
            }
            QLabel { color: #cccccc; font-weight: bold; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        layout.addWidget(QLabel(">> SYSTEM MONITORING STARTED..."))
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        self.setLayout(layout)

    def log(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        color = "#00ff00" # Green
        if level == "WARN": color = "#ffff00" # Yellow
        if level == "ERROR": color = "#ff0000" # Red
        if level == "DEBUG": color = "#00ffff" # Cyan
        
        html = f'<span style="color:#888;">[{timestamp}]</span> <span style="color:{color};">[{level}]</span> {message}'
        self.log_area.append(html)
        
        # 自动滚动到底部
        self.log_area.moveCursor(QTextCursor.End)

# ================= 【主要功能聚合页】 =================
class MainFunctionsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.pet = parent
        self.setWindowTitle("Zn 的百宝箱")
        self.resize(350, 300)
        self.setStyleSheet("""
            QDialog { background-color: #f0f4f8; }
            QPushButton {
                background-color: white;
                border: 2px solid #dce4ec;
                border-radius: 10px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                color: #555;
            }
            QPushButton:hover {
                background-color: #e6f7ff;
                border-color: #1890ff;
                color: #1890ff;
            }
            QPushButton:pressed {
                background-color: #d6e4ff;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_gold = QLabel(f"💰 当前金币: {self.pet.economy.user_data['gold']}")
        self.lbl_gold.setAlignment(Qt.AlignCenter)
        self.lbl_gold.setStyleSheet("font-size: 18px; color: #f39c12; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.lbl_gold)

        grid = QGridLayout()
        grid.setSpacing(15)

        btn_shop = QPushButton("🏪 便利店")
        btn_shop.clicked.connect(self.open_shop)
        
        btn_inventory = QPushButton("🎒 我的背包")
        btn_inventory.clicked.connect(self.open_inventory)
        
        btn_signin = QPushButton("📅 每日签到")
        btn_signin.clicked.connect(self.do_signin)
        
        btn_lottery = QPushButton("🎲 每日抽奖")
        btn_lottery.clicked.connect(self.do_lottery)

        grid.addWidget(btn_shop, 0, 0)
        grid.addWidget(btn_inventory, 0, 1)
        grid.addWidget(btn_signin, 1, 0)
        grid.addWidget(btn_lottery, 1, 1)

        layout.addLayout(grid)
        self.setLayout(layout)

    def update_gold_label(self):
        self.lbl_gold.setText(f"💰 当前金币: {self.pet.economy.user_data['gold']}")

    def open_shop(self):
        shop = ShopDialog(self.pet)
        shop.exec_()
        self.update_gold_label() 

    def open_inventory(self):
        inv = InventoryDialog(self.pet)
        inv.exec_()

    def do_signin(self):
        cal = CalendarDialog(self.pet)
        cal.exec_()
        self.update_gold_label()

    def do_lottery(self):
        lot = LotteryDialog(self.pet)
        lot.exec_()
        self.update_gold_label()

# ================= 【日历签到窗口】 =================
class CalendarDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.pet = parent
        self.setWindowTitle("📅 每日签到")
        self.resize(400, 450)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel#Title { font-size: 20px; font-weight: bold; color: #333; margin-bottom: 10px; }
            QLabel#DayLabel { border: 1px solid #eee; border-radius: 5px; background-color: #f9f9f9; }
            QLabel#Checked { background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc; font-weight: bold; }
            QLabel#Today { border: 2px solid #ffc107; }
            QPushButton#SignBtn {
                background-color: #0d6efd; color: white; border-radius: 20px; 
                padding: 10px 30px; font-size: 16px; font-weight: bold;
            }
            QPushButton#SignBtn:disabled { background-color: #ccc; }
            QPushButton#SignBtn:hover { background-color: #0b5ed7; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        current_date = time.localtime()
        year, month = current_date.tm_year, current_date.tm_mon
        title = QLabel(f"{year}年 {month}月")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(5)
        
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        for i, day in enumerate(weekdays):
            lbl = QLabel(day)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #888; font-weight: bold;")
            grid.addWidget(lbl, 0, i)

        cal = calendar.monthcalendar(year, month)
        today_str = time.strftime("%Y-%m-%d")
        history = self.pet.economy.user_data["checkin_history"]
        
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0: continue
                
                day_str = f"{year}-{month:02d}-{day:02d}"
                lbl = QLabel(str(day))
                lbl.setObjectName("DayLabel")
                lbl.setFixedSize(45, 45)
                lbl.setAlignment(Qt.AlignCenter)
                
                is_today = (day_str == today_str)
                is_checked = (day_str in history)
                
                text = str(day)
                if is_checked:
                    lbl.setObjectName("Checked")
                    text += "\n✔"
                
                if is_today:
                    if not is_checked: lbl.setStyleSheet("border: 2px solid #0d6efd;")
                    else: lbl.setStyleSheet("border: 2px solid #0d6efd; background-color: #d1e7dd;")

                lbl.setText(text)
                grid.addWidget(lbl, row_idx + 1, col_idx)

        layout.addLayout(grid)
        layout.addStretch()

        self.lbl_info = QLabel(f"累计签到: {len(history)} 天")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_info)

        self.btn_signin = QPushButton("立即签到")
        self.btn_signin.setObjectName("SignBtn")
        self.btn_signin.clicked.connect(self.do_signin)
        
        if self.pet.economy.is_checked_in_today():
            self.btn_signin.setText("今日已签到")
            self.btn_signin.setEnabled(False)
            
        layout.addWidget(self.btn_signin)
        self.setLayout(layout)

    def do_signin(self):
        success, reward, days = self.pet.economy.perform_checkin()
        if success:
            QMessageBox.information(self, "签到成功", f"🎉 签到成功！\n金币 +{reward}")
            self.pet.show_message("签到成功！心情变好了~", is_system=True)
            self.close()
            CalendarDialog(self.pet).exec_()

# ================= 【九宫格抽奖窗口】 =================
class LotteryDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.pet = parent
        self.setWindowTitle("🎲 幸运大抽奖")
        self.resize(400, 400)
        self.setStyleSheet("""
            QDialog { background-color: #2c3e50; }
            QLabel { 
                background-color: #ecf0f1; 
                border-radius: 8px; 
                font-weight: bold; 
                font-size: 14px;
                color: #2c3e50;
                border: 3px solid #bdc3c7;
            }
            QLabel#Active {
                background-color: #f1c40f;
                border: 3px solid #e67e22;
                color: #c0392b;
                font-size: 16px;
            }
            QPushButton#StartBtn {
                background-color: #e74c3c;
                color: white;
                font-size: 20px;
                font-weight: bold;
                border-radius: 50%;
                border: 4px solid #c0392b;
            }
            QPushButton#StartBtn:pressed { background-color: #c0392b; }
            QPushButton#StartBtn:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """)
        
        self.grid_labels = [] 
        self.current_index = 0 
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.target_index = -1 
        self.speed = 50 
        self.steps_run = 0 
        self.prize_data = None 

        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        prize_names = [
            "金币x20", "金币x50", "金币x10", 
            "大奖x200", "金币x30", "神秘物品", 
            "金币x80", "谢谢参与"
        ]
        
        coords = [
            (0,0), (0,1), (0,2),
            (1,2), (2,2), (2,1),
            (2,0), (1,0)
        ]

        self.grid_labels = []
        for i in range(8):
            lbl = QLabel(prize_names[i])
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(100, 100)
            layout.addWidget(lbl, coords[i][0], coords[i][1])
            self.grid_labels.append(lbl)

        self.btn_start = QPushButton("开始\n抽奖")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.setFixedSize(100, 100)
        self.btn_start.clicked.connect(self.start_lottery)
        layout.addWidget(self.btn_start, 1, 1)

        self.setLayout(layout)
        
        if not self.pet.economy.can_draw_lottery():
            self.btn_start.setEnabled(False)
            self.btn_start.setText("明日\n再来")

    def start_lottery(self):
        if not self.pet.economy.can_draw_lottery(): return
        self.target_index, self.prize_data = self.pet.economy.get_lottery_result()
        self.btn_start.setEnabled(False)
        self.speed = 50
        self.steps_run = 0
        self.timer.start(self.speed)

    def on_timer_tick(self):
        self.grid_labels[self.current_index].setObjectName("")
        self.grid_labels[self.current_index].style().unpolish(self.grid_labels[self.current_index])
        self.grid_labels[self.current_index].style().polish(self.grid_labels[self.current_index])

        self.current_index = (self.current_index + 1) % 8
        
        self.grid_labels[self.current_index].setObjectName("Active")
        self.grid_labels[self.current_index].style().unpolish(self.grid_labels[self.current_index])
        self.grid_labels[self.current_index].style().polish(self.grid_labels[self.current_index])

        self.steps_run += 1

        if self.steps_run > 24 and self.current_index == self.target_index:
            if self.speed > 300: 
                self.timer.stop()
                self.finish_lottery()
                return
            else:
                self.speed += 50
                self.timer.setInterval(self.speed)
        
        elif self.steps_run > 15:
            self.speed += 5
            self.timer.setInterval(self.speed)

    def finish_lottery(self):
        msg = self.pet.economy.apply_lottery_reward(self.prize_data)
        QMessageBox.information(self, "结果", f"🎉 {msg}")
        self.pet.show_message(f"抽奖结果：{msg}", is_system=True)
        self.btn_start.setText("明日\n再来")
        self.btn_start.setEnabled(False)

# ================= 【便利店 & 背包 & 设置面板】 =================
class ShopDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.pet = parent
        self.setWindowTitle("便利店")
        self.resize(400, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.lbl_gold = QLabel(f"💰 持有金币: {self.pet.economy.user_data['gold']}")
        self.lbl_gold.setStyleSheet("font-size: 16px; font-weight: bold; color: #f39c12;")
        layout.addWidget(self.lbl_gold)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(64, 64))
        self.refresh_list()
        layout.addWidget(self.list_widget)

        btn_buy = QPushButton("购买选中商品")
        btn_buy.clicked.connect(self.buy_selected)
        layout.addWidget(btn_buy)
        self.setLayout(layout)

    def refresh_list(self):
        self.list_widget.clear()
        for item_id, info in self.pet.economy.items_db.items():
            item = QListWidgetItem(f"{info['name']}\n💰 {info['price']}")
            image_path = get_asset_path(info.get('image', ''))
            if os.path.exists(image_path):
                item.setIcon(QIcon(image_path))
            else:
                item.setIcon(QIcon(get_asset_path("normal1.png"))) 
            item.setData(Qt.UserRole, item_id)
            self.list_widget.addItem(item)

    def buy_selected(self):
        current_item = self.list_widget.currentItem()
        if not current_item: return
        item_id = current_item.data(Qt.UserRole)
        success, msg = self.pet.economy.buy_item(item_id)
        if success:
            QMessageBox.information(self, "购买成功", f"买到了 {self.pet.economy.items_db[item_id]['name']}!")
            self.lbl_gold.setText(f"💰 持有金币: {self.pet.economy.user_data['gold']}")
        else:
            QMessageBox.warning(self, "购买失败", msg)

class InventoryDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.pet = parent
        self.setWindowTitle("我的背包")
        self.resize(400, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(64, 64))
        self.refresh_list()
        layout.addWidget(self.list_widget)

        btn_use = QPushButton("喂食 / 使用")
        btn_use.clicked.connect(self.use_selected)
        layout.addWidget(btn_use)
        self.setLayout(layout)

    def refresh_list(self):
        self.list_widget.clear()
        inventory = self.pet.economy.user_data["inventory"]
        if not inventory:
            self.list_widget.addItem("背包空空如也...")
            return
        for item_id, count in inventory.items():
            if item_id in self.pet.economy.items_db:
                info = self.pet.economy.items_db[item_id]
                item = QListWidgetItem(f"{info['name']} x{count}")
                image_path = get_asset_path(info.get('image', ''))
                if os.path.exists(image_path):
                    item.setIcon(QIcon(image_path))
                item.setData(Qt.UserRole, item_id)
                self.list_widget.addItem(item)

    def use_selected(self):
        current_item = self.list_widget.currentItem()
        if not current_item or not current_item.data(Qt.UserRole): return
        item_id = current_item.data(Qt.UserRole)
        success, item_name = self.pet.economy.use_item(item_id)
        if success:
            self.pet.feed_pet(item_name) 
            self.refresh_list()
            self.accept() 

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_pet = parent
        self.setWindowTitle("Zn 的控制面板")
        self.resize(850, 600) 
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QListWidget#Sidebar { background-color: #ffffff; border: none; border-right: 1px solid #e0e0e0; font-size: 14px; }
            QListWidget#Sidebar::item { padding: 15px 10px; border-bottom: 1px solid #f0f0f0; color: #555; }
            QListWidget#Sidebar::item:selected { background-color: #e6f7ff; color: #1890ff; border-left: 4px solid #1890ff; font-weight: bold; }
            QStackedWidget { background-color: #f8f9fa; }
            QLineEdit, QTextEdit, QDoubleSpinBox, QComboBox { background-color: white; border: 1px solid #ccc; border-radius: 4px; padding: 6px; }
            QPushButton { background-color: #fff; border: 1px solid #d9d9d9; border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { border-color: #40a9ff; color: #40a9ff; }
            QGroupBox { border: 1px solid #e0e0e0; border-radius: 6px; margin-top: 12px; background-color: white; padding-top: 10px; }
            QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(180)
        nav_items = [("📝 御主档案", 0), ("❤️ 状态监控", 1), ("⚙️ 核心人设", 2), 
                     ("⏳ 短期上下文", 3), ("🧠 记忆数据库", 4), ("🌐 API 设置", 5)]
        for name, index in nav_items:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, index)
            self.sidebar.addItem(item)
        self.sidebar.currentRowChanged.connect(self.switch_page)

        self.pages = QStackedWidget()
        self.pages.setContentsMargins(20, 20, 20, 20)
        self.page_profile = QWidget()
        self.init_profile_ui()
        self.pages.addWidget(self.page_profile)
        self.page_status = QWidget()
        self.init_status_ui()
        self.pages.addWidget(self.page_status)
        self.page_prompt = QWidget()
        self.init_prompt_ui()
        self.pages.addWidget(self.page_prompt)
        self.page_history = QWidget()
        self.init_history_ui()
        self.pages.addWidget(self.page_history)
        self.page_memory = QWidget()
        self.init_memory_ui()
        self.pages.addWidget(self.page_memory)
        self.page_api = QWidget()
        self.init_api_ui()
        self.pages.addWidget(self.page_api)

        content_frame = QFrame()
        content_frame.setLayout(QVBoxLayout())
        content_frame.layout().addWidget(self.pages)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_frame)
        self.setLayout(main_layout)
        self.sidebar.setCurrentRow(0)

    def switch_page(self, row):
        item = self.sidebar.item(row)
        if item:
            idx = item.data(Qt.UserRole)
            self.pages.setCurrentIndex(idx)
            if idx == 4: self.refresh_memory_db_list()
            elif idx == 3: self.refresh_history_list()
            elif idx == 1: self.refresh_status_ui() 
            elif idx == 5: self.refresh_api_ui_elements() 

    def init_profile_ui(self):
        layout = QVBoxLayout()
        group = QGroupBox("关于你")
        form_layout = QFormLayout()
        
        stored_time = self.parent_pet.economy.user_data.get("total_runtime", 0)
        current_session = int(time.time() - self.parent_pet.app_start_time)
        m, s = divmod(stored_time + current_session, 60)
        h, m = divmod(m, 60)
        lbl_runtime = QLabel(f"{h}小时 {m}分钟 {s}秒")
        lbl_runtime.setStyleSheet("font-size: 18px; color: #2ecc71;")
        
        self.input_nickname = QLineEdit(self.parent_pet.user_profile.get("nickname", ""))
        self.input_relation = QLineEdit(self.parent_pet.user_profile.get("relation", ""))
        self.input_info = QLineEdit(self.parent_pet.user_profile.get("user_info", ""))
        
        form_layout.addRow("⏰ 累计陪伴:", lbl_runtime) 
        form_layout.addRow("怎么称呼你:", self.input_nickname)
        form_layout.addRow("你们的关系:", self.input_relation)
        form_layout.addRow("特征/备注:", self.input_info)
        group.setLayout(form_layout)
        
        btn_save = QPushButton("💾 保存档案")
        btn_save.clicked.connect(self.save_profile)
        layout.addWidget(group)
        layout.addStretch()
        layout.addWidget(btn_save)
        self.page_profile.setLayout(layout)

    def init_status_ui(self):
        layout = QVBoxLayout()
        group_bars = QGroupBox("实时状态")
        bar_layout = QVBoxLayout()
        
        aff_val = self.parent_pet.economy.user_data.get("affection", 0)
        self.bar_affection = QProgressBar()
        self.bar_affection.setRange(0, 100)
        self.bar_affection.setValue(aff_val)
        self.bar_affection.setFormat(f"好感度: %v/100")
        self.bar_affection.setStyleSheet("QProgressBar::chunk { background-color: #FF69B4; }")
        
        mood_val = self.parent_pet.economy.user_data.get("mood", 50)
        self.bar_mood = QProgressBar()
        self.bar_mood.setRange(0, 100)
        self.bar_mood.setValue(mood_val)
        self.bar_mood.setFormat(f"心情: %v/100")
        self.bar_mood.setStyleSheet("QProgressBar::chunk { background-color: #87CEEB; }")

        bar_layout.addWidget(QLabel("💖 亲密度"))
        bar_layout.addWidget(self.bar_affection)
        bar_layout.addSpacing(10)
        bar_layout.addWidget(QLabel("☁️ 当前心情"))
        bar_layout.addWidget(self.bar_mood)
        group_bars.setLayout(bar_layout)

        group_desc = QGroupBox("心理侧写")
        desc_layout = QVBoxLayout()
        self.lbl_status_desc = QLabel()
        self.update_status_desc(aff_val, mood_val)
        self.lbl_status_desc.setWordWrap(True)
        desc_layout.addWidget(self.lbl_status_desc)
        group_desc.setLayout(desc_layout)

        group_model = QGroupBox("后台分析大脑")
        model_layout = QFormLayout()
        self.combo_sentiment_model = QComboBox()
        self.combo_sentiment_model.addItem("跟随主大脑")
        self.refresh_model_combos()
        
        current_model = self.parent_pet.economy.user_data.get("sentiment_model_key", "跟随主大脑")
        index = self.combo_sentiment_model.findText(current_model)
        if index >= 0: self.combo_sentiment_model.setCurrentIndex(index)
        
        self.combo_sentiment_model.currentTextChanged.connect(self.save_sentiment_model)
        model_layout.addRow("评估用模型:", self.combo_sentiment_model)
        group_model.setLayout(model_layout)

        layout.addWidget(group_bars)
        layout.addWidget(group_desc)
        layout.addWidget(group_model)
        layout.addStretch()
        
        btn_refresh = QPushButton("🔄 刷新状态")
        btn_refresh.clicked.connect(self.refresh_status_ui)
        layout.addWidget(btn_refresh)
        self.page_status.setLayout(layout)

    def init_prompt_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("System Prompt:"))
        self.txt_prompt = QTextEdit()
        self.txt_prompt.setPlainText(self.parent_pet.custom_system_prompt)
        layout.addWidget(self.txt_prompt)
        btn_save = QPushButton("💾 更新设定")
        btn_save.clicked.connect(self.save_prompt)
        layout.addWidget(btn_save)
        self.page_prompt.setLayout(layout)

    def init_history_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("当前会话上下文:"))
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.on_history_double_clicked)
        layout.addWidget(self.history_list)
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.clicked.connect(self.refresh_history_list)
        layout.addWidget(btn_refresh)
        self.page_history.setLayout(layout)

    def init_memory_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("长期记忆库:"))
        self.memory_list_widget = QListWidget()
        layout.addWidget(self.memory_list_widget)
        btn_refresh = QPushButton("刷新数据库")
        btn_refresh.clicked.connect(self.refresh_memory_db_list)
        layout.addWidget(btn_refresh)
        self.page_memory.setLayout(layout)

    def init_api_ui(self):
        layout = QVBoxLayout() 
        top_layout = QVBoxLayout()
        top_layout.addWidget(QLabel("已保存配置:"))
        self.api_list_widget = QListWidget()
        self.api_list_widget.setMaximumHeight(150) 
        self.api_list_widget.currentRowChanged.connect(self.on_api_selected)
        top_layout.addWidget(self.api_list_widget)
        
        btn_layout = QHBoxLayout()
        btn_new = QPushButton("➕ 新建")
        btn_new.clicked.connect(self.new_api_config)
        btn_del = QPushButton("🗑️ 删除")
        btn_del.setStyleSheet("color: red;")
        btn_del.clicked.connect(self.delete_api_config)
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_del)
        top_layout.addLayout(btn_layout)

        group = QGroupBox("参数详情")
        form_layout = QFormLayout()
        
        self.inp_conf_name = QLineEdit()
        self.inp_conf_name.setPlaceholderText("GPT-4")
        self.inp_api_url = QLineEdit()
        self.inp_api_url.setPlaceholderText("https://...")
        self.inp_api_key = QLineEdit()
        self.inp_api_key.setEchoMode(QLineEdit.Password) 
        self.inp_model_name = QLineEdit()
        self.inp_model_name.setPlaceholderText("model-id")
        self.inp_temperature = QDoubleSpinBox()
        self.inp_temperature.setRange(0.0, 2.0)
        self.inp_temperature.setValue(1.0)

        form_layout.addRow("名称:", self.inp_conf_name)
        form_layout.addRow("URL:", self.inp_api_url)
        form_layout.addRow("Key:", self.inp_api_key)
        form_layout.addRow("Model:", self.inp_model_name)
        form_layout.addRow("温度:", self.inp_temperature)
        
        btn_save = QPushButton("💾 保存配置")
        btn_save.clicked.connect(self.save_api_config)
        form_layout.addRow(btn_save)
        group.setLayout(form_layout)

        group_vision = QGroupBox("视觉识别设置")
        vision_layout = QFormLayout()
        self.combo_vision_model = QComboBox()
        self.combo_vision_model.addItem("跟随主大脑")
        self.refresh_model_combos() 
        
        current_v_model = self.parent_pet.economy.user_data.get("vision_model_key", "跟随主大脑")
        idx = self.combo_vision_model.findText(current_v_model)
        if idx >= 0: self.combo_vision_model.setCurrentIndex(idx)
        
        self.combo_vision_model.currentTextChanged.connect(self.save_vision_model)
        vision_layout.addRow("👀 窥屏专用模型:", self.combo_vision_model)
        group_vision.setLayout(vision_layout)

        layout.addLayout(top_layout)
        layout.addWidget(group)
        layout.addWidget(group_vision) 
        self.page_api.setLayout(layout)
        self.refresh_api_list()

    def refresh_status_ui(self):
        aff = self.parent_pet.economy.user_data.get("affection", 0)
        mood = self.parent_pet.economy.user_data.get("mood", 50)
        self.bar_affection.setValue(aff)
        self.bar_mood.setValue(mood)
        self.update_status_desc(aff, mood)
        self.refresh_model_combos()

    def refresh_api_ui_elements(self):
        self.refresh_api_list()
        self.refresh_model_combos()

    def refresh_model_combos(self):
        combos_to_refresh = []
        if hasattr(self, 'combo_sentiment_model'): combos_to_refresh.append(self.combo_sentiment_model)
        if hasattr(self, 'combo_vision_model'): combos_to_refresh.append(self.combo_vision_model)

        for combo in combos_to_refresh:
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("跟随主大脑")
            for name in MODEL_CONFIGS.keys(): combo.addItem(name)
            idx = combo.findText(current)
            if idx >= 0: combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def save_sentiment_model(self, text):
        self.parent_pet.economy.set_sentiment_model(text)

    def save_vision_model(self, text):
        self.parent_pet.economy.set_vision_model(text)

    def update_status_desc(self, aff, mood):
        desc = ""
        if aff < 20: desc = "警惕，像只炸毛的猫。"
        elif aff < 80: desc = "有点习惯你了，偶尔会靠近。"
        else: desc = "完全信任，你是她的全部。"
        self.lbl_status_desc.setText(desc)

    def save_profile(self):
        self.parent_pet.user_profile["nickname"] = self.input_nickname.text()
        self.parent_pet.user_profile["relation"] = self.input_relation.text()
        self.parent_pet.user_profile["user_info"] = self.input_info.text()
        self.parent_pet.save_profile()
        self.parent_pet.reset_conversation()
        QMessageBox.information(self, "成功", "档案已更新")

    def save_prompt(self):
        self.parent_pet.custom_system_prompt = self.txt_prompt.toPlainText()
        self.parent_pet.reset_conversation()
        QMessageBox.information(self, "成功", "人设已更新")

    def refresh_history_list(self):
        self.history_list.clear()
        for index, msg in enumerate(self.parent_pet.conversation_history):
            if index == 0: continue 
            raw_text = msg['content']
            display_text = raw_text
            if "|||" in raw_text:
                try:
                    display_text = raw_text.split("|||")[1].strip()
                except: pass
            if len(display_text) > 40: display_text = display_text[:40] + "..."
            item_text = f"[{msg['role']}] {display_text}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, index)
            self.history_list.addItem(item)

    def on_history_double_clicked(self, item):
        index = item.data(Qt.UserRole)
        self.refresh_history_list() 

    def refresh_memory_db_list(self):
        self.memory_list_widget.clear()
        memories = self.parent_pet.memory_manager.get_all_memories(limit=20)
        for mem in memories:
            self.memory_list_widget.addItem(f"[{mem['meta'].get('human_time')}] {mem['text'][:30]}...")

    def delete_memory_db_item(self, memory_id):
        if self.parent_pet.memory_manager.delete_memory(memory_id):
            self.refresh_memory_db_list()

    def refresh_api_list(self):
        self.api_list_widget.clear()
        for name in MODEL_CONFIGS.keys():
            self.api_list_widget.addItem(name)

    def on_api_selected(self, row):
        if row < 0: return
        name = self.api_list_widget.item(row).text()
        conf = MODEL_CONFIGS.get(name, {})
        self.inp_conf_name.setText(name)
        self.inp_api_url.setText(conf.get("url", ""))
        self.inp_api_key.setText(conf.get("key", ""))
        self.inp_model_name.setText(conf.get("model", ""))
        self.inp_temperature.setValue(conf.get("temperature", 1.0))

    def new_api_config(self):
        self.api_list_widget.clearSelection()
        self.inp_conf_name.clear()
        self.inp_api_url.clear()
        self.inp_api_key.clear()
        self.inp_model_name.clear()
        self.inp_temperature.setValue(1.0)

    def save_api_config(self):
        name = self.inp_conf_name.text().strip()
        url = self.inp_api_url.text().strip()
        key = self.inp_api_key.text().strip()
        model = self.inp_model_name.text().strip()
        temp = self.inp_temperature.value() 
        if not name or not url or not key or not model: return
        MODEL_CONFIGS[name] = {"url": url, "key": key, "model": model, "temperature": temp}
        save_api_configs()
        self.refresh_api_ui_elements()
        QMessageBox.information(self, "成功", f"配置【{name}】已保存！")
        if self.parent_pet: self.parent_pet.reload_configs()

    def delete_api_config(self):
        row = self.api_list_widget.currentRow()
        if row < 0: return
        name = self.api_list_widget.item(row).text()
        reply = QMessageBox.question(self, "确认删除", f"确定要删除【{name}】吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if name in MODEL_CONFIGS: del MODEL_CONFIGS[name]
            save_api_configs()
            self.refresh_api_ui_elements()
            if self.parent_pet: self.parent_pet.reload_configs()