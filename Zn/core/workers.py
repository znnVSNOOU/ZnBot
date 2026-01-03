import requests
import os
import time
import json
import uuid 
import re
import base64
import pyautogui
from io import BytesIO
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal
from config import get_temp_path 

class AIWorker(QThread):
    response_received = pyqtSignal(str)

    def __init__(self, history, config):
        super().__init__()
        self.history = history
        self.config = config

    def run(self):
        try:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.config['key']}"}
            temp = self.config.get('temperature', 1.0)
            
            data = {
                "model": self.config['model'], 
                "messages": self.history, 
                "stream": False, 
                "max_tokens": 200,  # 稍微增加回复长度限制
                "temperature": temp 
            }
            # 【修改点】超时改为 60 秒
            response = requests.post(self.config['url'], headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                self.response_received.emit(response.json()['choices'][0]['message']['content'])
            else:
                self.response_received.emit(f"错误 {response.status_code}")
        except Exception as e:
            self.response_received.emit(f"网络超时: {str(e)}")

class TTSWorker(QThread):
    audio_finished = pyqtSignal(str, str)

    def __init__(self, tts_text, display_text, config):
        super().__init__()
        self.tts_text = tts_text
        self.display_text = display_text 
        self.config = config

    def run(self):
        if not self.config.get("enable", False):
            self.audio_finished.emit(None, self.display_text)
            return

        try:
            payload = {
                "text": self.tts_text,
                "text_lang": self.config.get("text_lang", "ja"),
                "text_language": self.config.get("text_lang", "ja"),
                "ref_audio_path": self.config.get("ref_audio_path", ""),
                "refer_wav_path": self.config.get("ref_audio_path", ""),
                "prompt_text": self.config.get("prompt_text", ""),
                "prompt_lang": self.config.get("prompt_lang", "ja"),
                "prompt_language": self.config.get("prompt_lang", "ja"),
            }
            
            # 【修改点】超时改为 60 秒 (有些长句合成可能需要久一点)
            response = requests.post(self.config["api_url"], json=payload, timeout=60)

            if response.status_code == 200:
                file_name = f"tts_{int(time.time())}_{uuid.uuid4().hex[:4]}.wav"
                temp_path = get_temp_path(file_name)
                with open(temp_path, "wb") as f:
                    f.write(response.content)
                self.audio_finished.emit(temp_path, self.display_text)
            else:
                print(f"TTS 失败 ({response.status_code}): {response.text}")
                self.audio_finished.emit(None, self.display_text)
                
        except Exception as e:
            print(f"TTS 请求错误: {e}")
            self.audio_finished.emit(None, self.display_text)

class SentimentWorker(QThread):
    analysis_finished = pyqtSignal(int, int, str)

    def __init__(self, chat_logs, config, prompt_template):
        super().__init__()
        self.chat_logs = chat_logs
        self.config = config
        self.prompt_template = prompt_template

    def run(self):
        try:
            full_prompt = self.prompt_template + "\n".join(self.chat_logs)
            
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.config['key']}"}
            data = {
                "model": self.config['model'],
                "messages": [{"role": "user", "content": full_prompt}],
                "stream": False,
                "temperature": 0.5 
            }
            
            # 【修改点】超时改为 60 秒 (情感分析需要读很长的历史记录)
            response = requests.post(self.config['url'], headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                clean_content = re.sub(r'```json\s*|\s*```', '', content).strip()
                try:
                    result = json.loads(clean_content)
                    aff = int(result.get("affection_change", 0))
                    mood = int(result.get("mood_change", 0))
                    reason = str(result.get("reason", "无理由"))
                    self.analysis_finished.emit(aff, mood, reason)
                except:
                    print(f"情感分析 JSON 解析失败: {clean_content}")
            else:
                print(f"情感分析请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"情感分析线程错误: {e}")

class VisionWorker(QThread):
    response_received = pyqtSignal(str)

    def __init__(self, config, prompt):
        super().__init__()
        self.config = config
        self.prompt = prompt

    def run(self):
        try:
            # 1. 截图
            screenshot = pyautogui.screenshot()
            
            # 2. 压缩图片
            screenshot.thumbnail((800, 800)) 
            
            # 3. 转 Base64
            buffered = BytesIO()
            screenshot.save(buffered, format="JPEG", quality=70)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            base64_url = f"data:image/jpeg;base64,{img_str}"

            # 4. 构造请求
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.config['key']}"}
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_url}
                        }
                    ]
                }
            ]

            data = {
                "model": self.config['model'],
                "messages": messages,
                "stream": False,
                "max_tokens": 150
            }
            
            # 【修改点】超时改为 90 秒 (视觉识别通常最慢)
            response = requests.post(self.config['url'], headers=headers, json=data, timeout=90)
            
            if response.status_code == 200:
                self.response_received.emit(response.json()['choices'][0]['message']['content'])
            else:
                self.response_received.emit(f"视觉API错误 {response.status_code}: {response.text[:50]}...")
                
        except Exception as e:
            self.response_received.emit(f"视觉处理失败: {str(e)}")