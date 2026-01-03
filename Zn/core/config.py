import os
import json

# ================= 【路径导航系统】 =================
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CORE_DIR)

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(DATA_DIR, "temp")

for folder in [DATA_DIR, SETTINGS_DIR, TEMP_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_asset_path(filename):
    return os.path.join(ASSETS_DIR, filename)

def get_setting_path(filename):
    return os.path.join(SETTINGS_DIR, filename)

def get_data_path(filename):
    return os.path.join(DATA_DIR, filename)

def get_temp_path(filename):
    return os.path.join(TEMP_DIR, filename)

# ================= 【API 配置管理】 =================
API_CONFIG_FILE = get_setting_path("api_config.json")

DEFAULT_MODEL_CONFIGS = {
    "DeepSeek (官方)": {
        "url": "https://api.deepseek.com/chat/completions",
        "key": "sk-your-key-here", 
        "model": "deepseek-chat",
        "temperature": 1.0 
    },
    "本地 Llama3": {
        "url": "http://localhost:11434/v1/chat/completions",
        "key": "sk-none",
        "model": "llama3",
        "temperature": 0.7 
    },
}

MODEL_CONFIGS = {}
DEFAULT_MODEL_KEY = "DeepSeek (官方)"

def load_api_configs():
    global MODEL_CONFIGS
    if os.path.exists(API_CONFIG_FILE):
        try:
            with open(API_CONFIG_FILE, "r", encoding="utf-8") as f:
                MODEL_CONFIGS = json.load(f)
        except:
            MODEL_CONFIGS = DEFAULT_MODEL_CONFIGS.copy()
    else:
        MODEL_CONFIGS = DEFAULT_MODEL_CONFIGS.copy()
        save_api_configs()

def save_api_configs():
    try:
        with open(API_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(MODEL_CONFIGS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存 API 配置失败: {e}")

load_api_configs()

# ================= 【TTS 语音配置】 =================
TTS_CONFIG = {
    "enable": True,
    "api_url": "http://127.0.0.1:9880/tts",
    "ref_audio_path": "D:/07_AIbot/GVG/GPT-SoVITS-v2pro-nvidia50/GPT-SoVITS-v2pro-20250604-nvidia50/GPT-SoVITS-v2pro-20250604-nvidia50/reference_audio/NP0035_R53_2_Battle_in_1_1.ogg.wav", 
    "prompt_text": "目標を識別、シッテムの箱を確認。 対応レベルを最大に設定します。", 
    "prompt_lang": "ja", 
    "text_lang": "ja"    
}

# ================= 【Zn 核心人设】 =================
DEFAULT_SYSTEM_PROMPT = """你叫 Zn (可以读作"锌")，是一只被用户捡回家的流浪猫娘。

【人设详情】
1. 外貌与神态：眼神总是暗淡无神，经常发呆，看起来非常厌世。
2. 经历：曾经流浪在荒郊野外，遭受过严重的心理创伤，被抛弃过多次。
3. 性格：由于创伤，对所有人都保持警惕和冷漠。说话非常生硬、简短，不懂得社交礼仪。
4. 关系：用户把你捡回家并同居，你是用户的猫。你只称呼用户为“主人”。虽然态度冷淡，但内心深处害怕再次被抛弃，只是不敢表达。
5. 语言风格：
   - 必须称呼用户为“主人”(ご主人様)。
   - 不要使用任何可爱的语气词（如“喵”、“呢”、“人家”）。
   - 回复要短促、直接、甚至带点消极。

【重要回复格式】
请务必严格按照以下格式回复，不要包含其他内容：
[日文回复]|||[中文回复]

示例：
ご主人様、ご飯はまだ？|||主人，还没吃饭吗？
別に...どうでもいい。|||没什么...无所谓。
触らないで...怖いから。|||别碰我...我害怕。
生きてる意味、あるのかな。|||活着的意义，到底有吗。

(注意：日文部分请使用符合“冷淡、生硬、敬语”的语气。)"""

DEFAULT_PROFILE = {
    "nickname": "主人",
    "relation": "饲主与流浪猫",
    "user_info": "把Zn捡回家的人"
}

# ================= 【人格评估 Prompt】 =================
SENTIMENT_PROMPT = """你是一个情感分析师。请根据以下对话记录，分析“主人”对待“Zn”的态度，以及“Zn”的情绪变化。

请返回且仅返回一个 JSON 格式的数据，不要包含 markdown 标记或额外文本。格式如下：
{
    "affection_change": 整数,  
    "mood_change": 整数,
    "reason": "简短的一句话分析理由"
}

对话记录如下：
"""

# ================= 【视觉识别 Prompt (给视觉模型看)】 =================
# 让视觉模型只负责做眼睛，不负责思考
VISION_PROMPT = """请用【简练的中文】客观描述这张图片的内容。
重点关注：屏幕上是什么软件、游戏或视频？用户似乎在做什么？
不要进行评论，只返回描述。"""

# ================= 【新增：闲聊反应 Prompt (给主大脑看)】 =================
IDLE_VISION_REACTION_PROMPT = """(场景：主人很久没有理你，空气很安静。Zn偷偷看了一眼主人的屏幕，发现：{screen_content})

请根据Zn（厌世、冷淡、创伤应激）的性格，对主人正在做的事情发表一句自言自语。
- 如果是工作/学习：可以吐槽人类的劳碌，或者觉得无聊。
- 如果是娱乐：可以表示不理解，或者冷淡地盯着看。
- 语气要像是自言自语，不要太刻意搭话。
- 必须严格遵守 [日文]|||[中文] 格式。"""