import sys
import os
import json
import random
import time
import psutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QMenu, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QPoint, QUrl
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from config import MODEL_CONFIGS, DEFAULT_MODEL_KEY, DEFAULT_SYSTEM_PROMPT, DEFAULT_PROFILE, TTS_CONFIG, SENTIMENT_PROMPT, VISION_PROMPT, IDLE_VISION_REACTION_PROMPT, get_asset_path, get_setting_path, TEMP_DIR
from managers import EconomyManager, VectorMemoryManager
from workers import AIWorker, TTSWorker, SentimentWorker, VisionWorker 
from ui import ShopDialog, InventoryDialog, SettingsDialog, MainFunctionsDialog, DeveloperConsole

class DesktopPet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_start_time = time.time()
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 300, 400)
        
        icon_path = get_asset_path("oc.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.check_resources()
        self.img_normal1 = QPixmap(get_asset_path("normal1.png"))
        self.img_normal2 = QPixmap(get_asset_path("normal2.png"))
        self.img_drag = QPixmap(get_asset_path("123.png"))
        
        dizzy_path = get_asset_path("dizzy.png")
        self.img_dizzy = QPixmap(dizzy_path) if os.path.exists(dizzy_path) else self.img_drag
        
        eat1_path = get_asset_path("eat1.png")
        self.img_eat1 = QPixmap(eat1_path) if os.path.exists(eat1_path) else self.img_normal2
        
        eat2_path = get_asset_path("eat2.png")
        self.img_eat2 = QPixmap(eat2_path) if os.path.exists(eat2_path) else self.img_normal1

        self.load_profile()
        self.reload_configs()
        
        self.memory_manager = VectorMemoryManager()
        self.economy = EconomyManager()
        
        self.player = QMediaPlayer()
        self.current_audio_path = None 
        
        # 【新增】开发者控制台
        self.dev_console = DeveloperConsole(self)
        
        self.reset_conversation()
        self.init_ui()

        self.is_dragging = False
        self.drag_position = QPoint()
        self.is_dizzy = False
        self.is_eating = False 
        self.is_mouth_open = False 
        self.is_typing = False 
        self.is_speaking = False 
        self.is_thinking = False 
        
        self.is_idle_trigger = False

        self.last_interaction_time = time.time()

        self.talk_timer = QTimer()
        self.talk_timer.timeout.connect(self.animate_mouth)
        
        self.eat_timer = QTimer() 
        self.eat_timer.timeout.connect(self.animate_eating)
        self.eat_frame = 0

        self.typewriter_timer = QTimer()
        self.typewriter_timer.timeout.connect(self.update_typewriter)
        self.full_text = ""
        self.current_text_index = 0
        
        self.bubble_timer = QTimer()
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self.fade_out_bubble)

        self.idle_check_timer = QTimer()
        self.idle_check_timer.timeout.connect(self.check_idle_chat)
        self.idle_check_timer.start(60 * 1000) 

        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_system_status)
        self.monitor_timer.start(5000)

        self.player.stateChanged.connect(self.on_media_state_changed)

        self.clean_temp_folder()
        QTimer.singleShot(500, self.report_memory_status)
        
        self.show_message(f"Zn... 已启动。 (._.)")
        self.log_to_console("System initialized successfully.", "INFO")

    # 【新增】日志输出方法
    def log_to_console(self, msg, level="INFO"):
        if self.dev_console:
            self.dev_console.log(msg, level)
        print(f"[{level}] {msg}") # 同时输出到CMD以便调试

    def open_dev_console(self):
        self.dev_console.show()

    def closeEvent(self, event):
        session_time = int(time.time() - self.app_start_time)
        self.economy.add_runtime(session_time)
        self.clean_temp_folder()
        event.accept()

    def clean_temp_folder(self):
        try:
            if os.path.exists(TEMP_DIR):
                for filename in os.listdir(TEMP_DIR):
                    file_path = os.path.join(TEMP_DIR, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except: pass
        except: pass

    def reload_configs(self):
        if self.current_model_key not in MODEL_CONFIGS:
             self.current_model_key = list(MODEL_CONFIGS.keys())[0] if MODEL_CONFIGS else DEFAULT_MODEL_KEY
        if not MODEL_CONFIGS:
             MODEL_CONFIGS["DeepSeek (官方)"] = {
                "url": "https://api.deepseek.com/chat/completions",
                "key": "sk-your-key-here", 
                "model": "deepseek-chat"
            }
             self.current_model_key = "DeepSeek (官方)"
        self.current_config = MODEL_CONFIGS.get(self.current_model_key, {})

    def check_resources(self):
        path = get_asset_path("normal1.png")
        if not os.path.exists(path):
            print(f"【警告】找不到图片: {path}")

    def load_profile(self):
        self.user_profile = DEFAULT_PROFILE
        self.custom_system_prompt = DEFAULT_SYSTEM_PROMPT
        self.current_model_key = DEFAULT_MODEL_KEY 
        try:
            p_json = get_setting_path("profile.json")
            p_txt = get_setting_path("prompt.txt")
            if os.path.exists(p_json):
                with open(p_json, "r", encoding="utf-8") as f: self.user_profile = json.load(f)
            if os.path.exists(p_txt):
                with open(p_txt, "r", encoding="utf-8") as f: self.custom_system_prompt = f.read()
        except: pass
    
    def save_profile(self):
        try:
            p_json = get_setting_path("profile.json")
            p_txt = get_setting_path("prompt.txt")
            with open(p_json, "w", encoding="utf-8") as f:
                json.dump(self.user_profile, f, ensure_ascii=False, indent=2)
            with open(p_txt, "w", encoding="utf-8") as f:
                f.write(self.custom_system_prompt)
        except: pass

    def update_interaction(self):
        self.last_interaction_time = time.time()

    def report_memory_status(self):
        if self.memory_manager.init_error:
            self.log_to_console(f"Memory Init Failed: {self.memory_manager.init_error}", "ERROR")
            QMessageBox.critical(self, "记忆模块启动失败", f"原因：\n{self.memory_manager.init_error}")
        else:
            self.log_to_console("Vector Memory Database loaded.", "INFO")

    def feed_pet(self, food_name):
        self.update_interaction() 
        self.show_message(f"在吃... {food_name}", is_system=True)
        self.is_eating = True
        self.eat_timer.start(300) 
        self.economy.update_status(affection_delta=1, mood_delta=5)
        
        self.log_to_console(f"User fed {food_name}. Mood increased.", "INFO")
        
        prompt_text = f"(主人给你投喂了【{food_name}】。Zn虽然心理有创伤，但还是需要进食。请用生硬、冷淡的语气描述口感，简单说声谢谢。)"
        self.conversation_history.append({"role": "user", "content": prompt_text})
        self.worker = AIWorker(self.conversation_history, self.current_config)
        self.worker.response_received.connect(self.handle_feed_response)
        self.worker.start()

    def handle_feed_response(self, content):
        self.is_eating = False
        self.eat_timer.stop()
        self.lbl_image.setPixmap(self.img_normal1) 
        self.process_dual_language_response(content)

    def animate_eating(self):
        if self.eat_frame == 0:
            self.lbl_image.setPixmap(self.img_eat1)
            self.eat_frame = 1
        else:
            self.lbl_image.setPixmap(self.img_eat2)
            self.eat_frame = 0

    def init_ui(self):
        self.lbl_image = QLabel(self)
        self.lbl_image.setPixmap(self.img_normal1)
        self.lbl_image.setScaledContents(True)
        self.lbl_image.resize(200, 200) 
        self.lbl_image.move(50, 100)

        self.lbl_bubble = QLabel(self)
        self.lbl_bubble.setStyleSheet("background-color: rgba(20,20,30,230); color: white; border: 2px solid #555; border-radius: 5px; padding: 10px; font-family: 'Microsoft YaHei';")
        self.lbl_bubble.setWordWrap(True)
        self.lbl_bubble.setFixedWidth(200)
        self.lbl_bubble.move(50, 10) 
        self.lbl_bubble.hide() 
        
        self.lbl_bubble.raise_()
        
        self.bubble_click_mask = QLabel(self)
        self.bubble_click_mask.setGeometry(self.lbl_bubble.geometry())
        self.bubble_click_mask.setCursor(Qt.PointingHandCursor)
        self.bubble_click_mask.hide()
        self.bubble_click_mask.mousePressEvent = self.on_bubble_click

        self.input_box = QLineEdit(self)
        self.input_box.setStyleSheet("background-color: rgba(255,255,255,220); border: 2px solid #555; border-radius: 15px; padding: 5px;")
        self.input_box.setGeometry(50, 310, 200, 30)
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.hide() 

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: white; border: 1px solid #ccc; padding: 5px; } QMenu::item { padding: 5px 20px; color: black; } QMenu::item:selected { background-color: #ddd; }")
        
        menu.addAction("🧰 主要功能").triggered.connect(self.open_main_functions)
        
        menu.addAction("👀 窥屏 (视觉)").triggered.connect(self.peek_screen_manual) 
        menu.addAction("⏱️ 专注工作").triggered.connect(self.start_focus_work)
        menu.addAction("⚙️ 控制面板").triggered.connect(self.open_settings)
        # 【新增】开发者入口
        menu.addAction("👨‍💻 开发者监控").triggered.connect(self.open_dev_console)
        
        menu.addSeparator()
        model_menu = menu.addMenu("🧠 切换大脑")
        for key in MODEL_CONFIGS.keys():
            action = model_menu.addAction(key)
            if key == self.current_model_key:
                action.setCheckable(True)
                action.setChecked(True)
            action.triggered.connect(lambda checked, name=key: self.change_model(name))
        menu.addAction("❌ 退出").triggered.connect(self.close)
        menu.exec_(event.globalPos())

    def open_main_functions(self):
        dialog = MainFunctionsDialog(self)
        dialog.exec_()

    def open_shop(self):
        shop = ShopDialog(self)
        shop.exec_()

    def open_inventory(self):
        inv = InventoryDialog(self)
        inv.exec_()

    def open_settings(self):
        settings = SettingsDialog(self)
        settings.exec_()

    def change_model(self, model_key):
        if model_key == self.current_model_key: return
        self.current_model_key = model_key
        self.current_config = MODEL_CONFIGS[model_key]
        self.show_message(f"大脑切换: {model_key}")
        self.log_to_console(f"Model switched to: {model_key}", "INFO")

    def peek_screen_manual(self):
        self.is_idle_trigger = False 
        self.log_to_console("User requested manual peek.", "INFO")
        self.start_vision_process()

    def trigger_idle_chat(self):
        self.is_idle_trigger = True 
        self.log_to_console("Idle Chat Triggered! Starting vision process...", "WARN")
        self.start_vision_process()

    def start_vision_process(self):
        self.update_interaction()
        vision_key = self.economy.user_data.get("vision_model_key", "跟随主大脑")
        
        if vision_key == "跟随主大脑" or vision_key not in MODEL_CONFIGS:
            config_to_use = self.current_config
        else:
            config_to_use = MODEL_CONFIGS[vision_key]
            
        self.log_to_console(f"Capturing screen using model: {vision_key}", "DEBUG")
        
        if not self.is_idle_trigger:
            self.is_thinking = True
            self.show_message("正在观察屏幕...", is_system=True)
        
        self.vision_worker = VisionWorker(config_to_use, VISION_PROMPT)
        self.vision_worker.response_received.connect(self.handle_vision_response)
        self.vision_worker.start()

    def handle_vision_response(self, content):
        self.is_thinking = False
        self.log_to_console(f"Vision API Response: {content[:50]}...", "DEBUG")
        
        if self.is_idle_trigger:
            final_prompt = IDLE_VISION_REACTION_PROMPT.format(screen_content=content)
            temp_history = self.conversation_history + [{"role": "system", "content": final_prompt}]
            self.log_to_console("Sending idle reaction prompt to AI...", "DEBUG")
        else:
            prompt_for_zn = f"(Zn看了一眼主人的屏幕。屏幕内容是：{content}。请根据Zn的人设，对主人现在的行为进行简短的评价、吐槽或关心。)"
            temp_history = self.conversation_history + [{"role": "system", "content": prompt_for_zn}]
            self.log_to_console("Sending manual peek prompt to AI...", "DEBUG")
        
        self.worker = AIWorker(temp_history, self.current_config)
        self.worker.response_received.connect(self.handle_response) 
        self.worker.start()

    def start_focus_work(self):
        self.update_interaction() 
        self.show_message("...你要忙了吗？那我发呆了。(20分钟后结算)", is_system=True)
        self.log_to_console("Focus work started.", "INFO")
        QTimer.singleShot(5000, self.finish_focus_work)

    def finish_focus_work(self):
        new_gold = self.economy.add_gold(20)
        self.show_message(f"结束了？...金币+20。", is_system=True)
        self.log_to_console("Focus work finished. Reward granted.", "INFO")

    def reset_conversation(self):
        prompt = f"【御主档案】\n昵称:{self.user_profile['nickname']}\n备注:{self.user_profile['user_info']}\n{self.custom_system_prompt}"
        self.conversation_history = [{"role": "system", "content": prompt}]

    def send_message(self):
        text = self.input_box.text().strip()
        if not text: return
        self.input_box.clear()
        self.input_box.hide()
        
        self.update_interaction()
        self.log_to_console(f"User Input: {text}", "INFO")
        
        current_mood = self.economy.user_data.get("mood", 50)
        if current_mood < 10: 
            self.show_message("（Zn躲到了桌子底下，不想说话...）")
            self.economy.update_status(affection_delta=-1) 
            self.log_to_console("Chat blocked due to low mood.", "WARN")
            return
        
        mem = self.memory_manager.search(text)
        
        current_aff = self.economy.user_data.get("affection", 10)
        status_prompt = f"\n[当前状态] 好感度:{current_aff}/100, 心情:{current_mood}/100。"
        force_format_prompt = "\n【系统强制要求】必须严格遵守 [日文]|||[中文] 的回复格式！"
        
        sys_prompt = self.conversation_history[0]['content'] + status_prompt + force_format_prompt
        if mem: sys_prompt += f"\n【闪回记忆】{mem}"
        
        recent_history = self.conversation_history[1:]
        if len(recent_history) > 15:
            recent_history = recent_history[-15:]
            
        temp_history = [{"role": "system", "content": sys_prompt}] + recent_history + [{"role": "user", "content": text}]
        
        self.conversation_history.append({"role": "user", "content": text})
        
        self.is_thinking = True
        self.show_message("Thinking...", is_system=True)
        
        self.worker = AIWorker(temp_history, self.current_config)
        self.worker.response_received.connect(self.handle_response)
        self.worker.start()

    def handle_response(self, content):
        self.is_thinking = False
        self.log_to_console(f"AI Response: {content}", "DEBUG")
        self.process_dual_language_response(content)
        
        if len(self.conversation_history) >= 2:
            last_user_msg = self.conversation_history[-2]['content']
            last_ai_msg = content
            self.economy.record_chat_for_eval(last_user_msg, last_ai_msg)
            
            if self.economy.should_evaluate():
                self.start_sentiment_analysis()

    def start_sentiment_analysis(self):
        self.log_to_console("Starting sentiment analysis...", "INFO")
        chat_logs = self.economy.temp_chat_history
        
        sentiment_key = self.economy.user_data.get("sentiment_model_key", "跟随主大脑")
        
        if sentiment_key == "跟随主大脑" or sentiment_key not in MODEL_CONFIGS:
            config_to_use = self.current_config
        else:
            config_to_use = MODEL_CONFIGS[sentiment_key]
            
        self.sentiment_worker = SentimentWorker(chat_logs, config_to_use, SENTIMENT_PROMPT)
        self.sentiment_worker.analysis_finished.connect(self.handle_analysis_result)
        self.sentiment_worker.start()
        self.economy.reset_eval_counter()

    def handle_analysis_result(self, aff_change, mood_change, reason):
        self.log_to_console(f"Analysis: Aff {aff_change}, Mood {mood_change}. Reason: {reason}", "INFO")
        self.economy.update_status(aff_change, mood_change)
        if abs(aff_change) >= 2 or abs(mood_change) >= 5:
            self.show_message(f"（Zn的状态发生了变化...）", is_system=True)

    def process_dual_language_response(self, content):
        jp_text = ""
        cn_text = content
        target_lang = "ja"

        if "|||" in content:
            parts = content.split("|||")
            if len(parts) >= 2:
                jp_text = parts[0].strip()
                cn_text = parts[1].strip()
            else:
                jp_text = content
                target_lang = "zh"
        else:
            jp_text = content
            target_lang = "zh"
        
        self.conversation_history.append({"role": "assistant", "content": content})
        self.memory_manager.add(self.conversation_history[-2]['content'], cn_text)
        
        self.trigger_tts_with_delay(jp_text, cn_text, target_lang)

    def trigger_tts_with_delay(self, tts_text, display_text, lang="ja"):
        clean_text = tts_text.replace("~", "").replace("(", "").replace(")", "").replace("（", "").replace("）", "")
        if not clean_text: 
            self.show_message(display_text)
            return

        temp_config = TTS_CONFIG.copy()
        temp_config["text_lang"] = lang 
        
        self.tts_worker = TTSWorker(clean_text, display_text, temp_config)
        self.tts_worker.audio_finished.connect(self.on_tts_finished)
        self.tts_worker.start()

    def on_tts_finished(self, audio_path, display_text):
        self.show_message(display_text)
        if audio_path and os.path.exists(audio_path):
            self.play_audio(audio_path)

    def play_audio(self, file_path):
        if not os.path.exists(file_path): return
        
        self.is_speaking = True 
        
        self.current_audio_path = file_path 
        url = QUrl.fromLocalFile(file_path)
        content = QMediaContent(url)
        self.player.setMedia(content)
        self.player.play()

    def on_media_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.is_speaking = True
            if not self.talk_timer.isActive() and not self.is_dizzy and not self.is_eating:
                self.talk_timer.start(200)
        
        elif state == QMediaPlayer.StoppedState:
            self.is_speaking = False
            
            if not self.is_typing:
                self.talk_timer.stop()
                self.lbl_image.setPixmap(self.img_normal1)
            
            self.bubble_timer.start(8000)
            self.lbl_bubble.raise_()

            if self.current_audio_path:
                self.player.setMedia(QMediaContent()) 
                try:
                    if os.path.exists(self.current_audio_path):
                        os.remove(self.current_audio_path)
                    self.current_audio_path = None
                except Exception as e:
                    print(f"删除失败: {e}")

    def update_typewriter(self):
        if self.current_text_index < len(self.full_text):
            self.current_text_index += 1
            self.lbl_bubble.setText(self.full_text[:self.current_text_index])
            self.lbl_bubble.adjustSize()
            self.bubble_click_mask.setGeometry(self.lbl_bubble.geometry())
        else:
            self.is_typing = False
            self.typewriter_timer.stop()
            
            if not self.is_speaking and not self.is_thinking:
                self.talk_timer.stop()
                self.lbl_image.setPixmap(self.img_normal1 if not self.is_eating else self.lbl_image.pixmap())
                self.bubble_timer.start(8000)

    def show_message(self, text, is_system=False):
        self.bubble_timer.stop()
        self.typewriter_timer.stop()
        
        self.full_text = text
        self.current_text_index = 0
        self.lbl_bubble.setText("")
        self.lbl_bubble.show()
        self.lbl_bubble.raise_()
        self.bubble_click_mask.raise_()
        
        self.lbl_bubble.adjustSize()
        self.bubble_click_mask.setGeometry(self.lbl_bubble.geometry())
        self.bubble_click_mask.show()
        self.is_typing = True
        self.typewriter_timer.start(50)
        
        if not is_system and not self.is_dizzy and not self.is_eating:
            self.talk_timer.start(200)

    def on_bubble_click(self, event):
        self.update_interaction()
        if self.is_typing:
            self.is_typing = False
            self.typewriter_timer.stop()
            self.lbl_bubble.setText(self.full_text)
            self.lbl_bubble.adjustSize()
            self.bubble_click_mask.setGeometry(self.lbl_bubble.geometry())
            if not self.is_speaking:
                self.talk_timer.stop()
                self.lbl_image.setPixmap(self.img_normal1)
        else:
            if not self.is_thinking:
                self.bubble_timer.start(8000)

    def fade_out_bubble(self):
        self.lbl_bubble.hide()
        self.bubble_click_mask.hide()

    def animate_mouth(self):
        should_animate = (self.is_typing or self.is_speaking) and not self.is_dizzy and not self.is_eating
        if not should_animate:
            if self.lbl_image.pixmap() != self.img_normal1:
                self.lbl_image.setPixmap(self.img_normal1)
            return

        if self.is_mouth_open:
            self.lbl_image.setPixmap(self.img_normal1)
            self.is_mouth_open = False
        else:
            self.lbl_image.setPixmap(self.img_normal2)
            self.is_mouth_open = True

    def check_system_status(self):
        try:
            cpu = psutil.cpu_percent()
            if cpu > 85 and not self.is_dizzy:
                self.is_dizzy = True
                self.lbl_image.setPixmap(self.img_dizzy)
                self.show_message("...有点晕。好烫。", is_system=True)
            elif cpu < 60 and self.is_dizzy:
                self.is_dizzy = False
                self.lbl_image.setPixmap(self.img_normal1)
        except: pass

    def check_idle_chat(self):
        # 如果正在聊天、晕倒或吃东西，不打扰
        if self.lbl_bubble.isVisible() or self.is_dizzy or self.is_eating: return
        
        # 计算距离上次互动过了多少分钟
        elapsed = (time.time() - self.last_interaction_time) / 60.0
        
        # 【修改点 1】门槛降为 1 分钟 (原来是 5 分钟)
        if elapsed < 1.0: return 
        
        # 【修改点 2】概率提升
        # 基础概率 15%，每多等 1 分钟增加 5%，上限 80%
        prob = 0.15 + (elapsed - 1.0) * 0.05
        if prob > 0.8: prob = 0.8
        
        # 在控制台输出调试信息，让你看到它在掷骰子
        self.log_to_console(f"闲聊检定: 沉默{elapsed:.1f}分, 触发率{prob:.0%}", "DEBUG")
        
        if random.random() < prob:
            self.log_to_console("🎲 检定通过！准备发动闲聊...", "INFO")
            self.trigger_idle_chat()
            # 触发后重置时间，防止连珠炮发问
            self.last_interaction_time = time.time()

    def enterEvent(self, event):
        self.update_interaction()
        self.input_box.show()
    def leaveEvent(self, event):
        if not self.input_box.hasFocus(): self.input_box.hide()
        self.update_interaction()
    def mousePressEvent(self, event):
        self.update_interaction()
        if event.button() == Qt.LeftButton and not self.input_box.geometry().contains(event.pos()) and not self.lbl_bubble.geometry().contains(event.pos()):
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.lbl_image.setPixmap(self.img_drag)
    def mouseMoveEvent(self, event):
        if self.is_dragging: self.move(event.globalPos() - self.drag_position)
    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.lbl_image.setPixmap(self.img_normal1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())