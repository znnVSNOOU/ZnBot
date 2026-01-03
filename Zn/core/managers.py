import json
import os
import time
import random
import calendar
from config import get_data_path

class EconomyManager:
    def __init__(self):
        self.data_path = get_data_path("user_data.json")
        self.items_path = "settings/items.json" 
        
        self.user_data = {
            "gold": 100,
            "last_checkin": 0,
            "checkin_history": [], # 【新增】签到历史 ["2023-10-01", ...]
            "last_lottery": 0, 
            "inventory": {},
            "total_runtime": 0,
            "affection": 10,
            "mood": 50,     
            "chat_counter": 0,
            "sentiment_model_key": "跟随主大脑",
            "vision_model_key": "跟随主大脑"
        }
        self.items_db = {}
        self.temp_chat_history = [] 
        
        self.load_items()
        self.load_data()

    def load_items(self):
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings", "items.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    self.items_db = json.load(f)
        except: pass

    def load_data(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.user_data.update(data)
                    # 数据迁移/补全
                    if "checkin_history" not in self.user_data: 
                        self.user_data["checkin_history"] = []
                    if "last_lottery" not in self.user_data:
                        self.user_data["last_lottery"] = 0
            except: pass
    
    def save_data(self):
        try:
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=2)
        except: pass

    # ================= 签到逻辑 (升级版) =================
    def is_checked_in_today(self):
        today = time.strftime("%Y-%m-%d")
        return today in self.user_data["checkin_history"]

    def perform_checkin(self):
        """执行签到，返回(是否成功, 奖励, 总天数)"""
        if self.is_checked_in_today():
            return False, 0, len(self.user_data["checkin_history"])
        
        today = time.strftime("%Y-%m-%d")
        self.user_data["checkin_history"].append(today)
        self.user_data["last_checkin"] = time.strftime("%Y%m%d") # 兼容旧逻辑
        
        # 奖励计算 (可以加连续签到逻辑，这里先简单处理)
        reward = 50
        self.user_data["gold"] += reward
        self.update_status(affection_delta=2, mood_delta=5)
        
        self.save_data()
        return True, reward, len(self.user_data["checkin_history"])

    # ================= 抽奖逻辑 (预计算版) =================
    def can_draw_lottery(self):
        today = time.strftime("%Y%m%d")
        return str(self.user_data.get("last_lottery", 0)) != today

    def get_lottery_result(self):
        """
        返回: (target_index, prize_name, prize_type, prize_value)
        UI根据 target_index 决定停在哪里，动画结束后调用 apply_lottery_reward 发奖
        """
        # 定义8个格子的奖品 (0-7围成一圈)
        # 0: 左上, 1: 中上, 2: 右上, 3: 右中, 4: 右下, 5: 中下, 6: 左下, 7: 左中
        # 这是一个常见的视觉顺序
        prizes_config = [
            {"name": "金币 x20", "type": "gold", "val": 20, "weight": 30},  # Index 0
            {"name": "金币 x50", "type": "gold", "val": 50, "weight": 25},  # Index 1
            {"name": "金币 x10", "type": "gold", "val": 10, "weight": 20},  # Index 2
            {"name": "大奖 x200", "type": "gold", "val": 200, "weight": 5}, # Index 3
            {"name": "金币 x30", "type": "gold", "val": 30, "weight": 25},  # Index 4
            {"name": "神秘物品", "type": "item", "val": 0, "weight": 5},    # Index 5
            {"name": "金币 x80", "type": "gold", "val": 80, "weight": 15},  # Index 6
            {"name": "谢谢参与", "type": "empty", "val": 0, "weight": 10}   # Index 7
        ]
        
        # 权重计算
        total_weight = sum(p['weight'] for p in prizes_config)
        rand = random.randint(1, total_weight)
        current = 0
        target_idx = 0
        
        for i, p in enumerate(prizes_config):
            current += p['weight']
            if rand <= current:
                target_idx = i
                break
        
        result = prizes_config[target_idx]
        return target_idx, result

    def apply_lottery_reward(self, prize_data):
        """动画播放完毕后，真正发奖并记录时间"""
        self.user_data["last_lottery"] = time.strftime("%Y%m%d")
        
        ptype = prize_data["type"]
        val = prize_data["val"]
        msg = ""

        if ptype == "gold":
            self.user_data["gold"] += val
            msg = f"获得 {val} 金币！"
            self.update_status(mood_delta=5)
        elif ptype == "item":
            # 随机给一个物品，如果没有物品库则给500金币
            if self.items_db:
                item_id = random.choice(list(self.items_db.keys()))
                item_name = self.items_db[item_id]["name"]
                self.user_data["inventory"][item_id] = self.user_data["inventory"].get(item_id, 0) + 1
                msg = f"运气爆棚！获得物品【{item_name}】！"
                self.update_status(affection_delta=5, mood_delta=20)
            else:
                self.user_data["gold"] += 500
                msg = "获得替代大奖：500 金币！"
        elif ptype == "empty":
            msg = "虽然没中奖，但Zn摸了摸你的头。"
            self.update_status(affection_delta=1)

        self.save_data()
        return msg

    # ================= 其他原有逻辑 =================
    def add_gold(self, amount):
        self.user_data["gold"] += amount
        self.save_data()
        return self.user_data["gold"]

    def buy_item(self, item_id):
        if item_id not in self.items_db: return False, "商品不存在"
        price = self.items_db[item_id]['price']
        if self.user_data['gold'] >= price:
            self.user_data['gold'] -= price
            self.user_data['inventory'][item_id] = self.user_data['inventory'].get(item_id, 0) + 1
            self.save_data()
            return True, "购买成功"
        else:
            return False, "金币不足"

    def use_item(self, item_id):
        if item_id in self.user_data['inventory'] and self.user_data['inventory'][item_id] > 0:
            self.user_data['inventory'][item_id] -= 1
            if self.user_data['inventory'][item_id] <= 0:
                del self.user_data['inventory'][item_id]
            self.save_data()
            return True, self.items_db[item_id]['name']
        return False, ""

    def add_runtime(self, seconds):
        self.user_data["total_runtime"] = self.user_data.get("total_runtime", 0) + int(seconds)
        self.save_data()

    def update_status(self, affection_delta=0, mood_delta=0):
        self.user_data["affection"] = max(0, min(100, self.user_data["affection"] + affection_delta))
        self.user_data["mood"] = max(0, min(100, self.user_data["mood"] + mood_delta))
        self.save_data()
    
    def set_sentiment_model(self, key):
        self.user_data["sentiment_model_key"] = key
        self.save_data()

    def set_vision_model(self, key):
        self.user_data["vision_model_key"] = key
        self.save_data()

    def record_chat_for_eval(self, user_text, ai_text):
        self.temp_chat_history.append(f"主人: {user_text}\nZn: {ai_text}")
        self.user_data["chat_counter"] += 1
        self.save_data()

    def should_evaluate(self):
        return self.user_data["chat_counter"] >= 10

    def reset_eval_counter(self):
        self.user_data["chat_counter"] = 0
        self.temp_chat_history = []
        self.save_data()

import chromadb
import uuid

class VectorMemoryManager:
    def __init__(self):
        self.init_error = None
        self.collection = None
        try:
            db_path = get_data_path("memory_db")
            if not os.path.exists(db_path):
                os.makedirs(db_path)
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(name="zn_memory")
        except Exception as e:
            self.init_error = str(e)

    def add(self, user_text, ai_reply):
        if not self.collection: return
        try:
            text_to_store = f"主人说: {user_text}\nZn回复: {ai_reply}"
            self.collection.add(
                documents=[text_to_store],
                metadatas=[{"timestamp": time.time(), "human_time": time.strftime("%Y-%m-%d %H:%M:%S")}],
                ids=[str(uuid.uuid4())]
            )
        except: pass

    def search(self, query, n_results=1):
        if not self.collection: return None
        try:
            results = self.collection.query(query_texts=[query], n_results=n_results)
            if results['documents'] and len(results['documents'][0]) > 0:
                return results['documents'][0][0] 
        except: pass
        return None

    def get_all_memories(self, limit=20):
        if not self.collection: return []
        try:
            data = self.collection.get(limit=limit)
            memories = []
            for i in range(len(data['ids'])):
                memories.append({
                    "id": data['ids'][i],
                    "text": data['documents'][i],
                    "meta": data['metadatas'][i] if data['metadatas'] else {}
                })
            return sorted(memories, key=lambda x: x['meta'].get('timestamp', 0), reverse=True)
        except: return []

    def delete_memory(self, memory_id):
        if not self.collection: return False
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except: return False