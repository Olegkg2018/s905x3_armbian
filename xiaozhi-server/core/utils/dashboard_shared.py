import time
from datetime import datetime

LOG_EVENTS = []
CHAT_HISTORY = []
CURRENT_STATE = "IDLE"  # IDLE, LISTENING, THINKING, SPEAKING
GLOBAL_CONFIG_REF = {}  # Ссылка на глобальный словарь конфигурации для обновления "на лету"

def add_event(event_text: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    LOG_EVENTS.append({"time": timestamp, "event": event_text})
    if len(LOG_EVENTS) > 100:
        LOG_EVENTS.pop(0)

def add_chat(role: str, text: str):
    if not text:
        return
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Стриминг по фразам: если последнее сообщение от того же автора и добавлено недавно, объединяем
    if CHAT_HISTORY and CHAT_HISTORY[-1]["role"] == role:
        last_msg = CHAT_HISTORY[-1]
        # Проверяем, не дублируется ли текст
        if text not in last_msg["text"]:
            last_msg["text"] += " " + text
        last_msg["time"] = timestamp
    else:
        CHAT_HISTORY.append({"role": role, "text": text, "time": timestamp})
        
    if len(CHAT_HISTORY) > 50:
        CHAT_HISTORY.pop(0)

def set_state(state: str):
    global CURRENT_STATE
    CURRENT_STATE = state.upper()
    add_event(f"Система перешла в режим: {CURRENT_STATE}")
