import asyncio
import os
import json
import yaml
from aiohttp import web
from config.logger import setup_logging
from core.api.ota_handler import OTAHandler
from core.api.vision_handler import VisionHandler

TAG = __name__

# Сверхтехнологичная, стеклянная темная панель управления (Dashboard HTML)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=initial-scale=1.0">
    <title>Алиса • Умная Колонка</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0d19;
            --panel-bg: rgba(22, 28, 45, 0.6);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f1f2f6;
            --text-secondary: #a4b0be;
            --accent-blue: #0984e3;
            --accent-purple: #6c5ce7;
            --state-idle: #2ed573;
            --state-listening: #ff793f;
            --state-thinking: #a29bfe;
            --state-speaking: #0984e3;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(90, 120, 250, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(108, 92, 231, 0.08) 0%, transparent 45%);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        header {
            background: rgba(11, 13, 25, 0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-color);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo-section {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-circle {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            box-shadow: 0 0 15px rgba(108, 92, 231, 0.5);
            animation: pulse-glow 3s infinite alternate;
        }

        h1 {
            font-size: 20px;
            font-weight: 600;
            letter-spacing: -0.5px;
            background: linear-gradient(to right, #ffffff, #a4b0be);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.04);
            padding: 6px 16px;
            border-radius: 20px;
            border: 1px solid var(--border-color);
            font-size: 13px;
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            transition: all 0.4s ease;
        }

        .state-idle .status-dot { background-color: var(--state-idle); box-shadow: 0 0 10px var(--state-idle); }
        .state-listening .status-dot { background-color: var(--state-listening); box-shadow: 0 0 10px var(--state-listening); animation: pulse-blink 1s infinite; }
        .state-thinking .status-dot { background-color: var(--state-thinking); box-shadow: 0 0 10px var(--state-thinking); animation: pulse-blink 0.6s infinite; }
        .state-speaking .status-dot { background-color: var(--state-speaking); box-shadow: 0 0 10px var(--state-speaking); animation: pulse-glow-dot 2s infinite alternate; }

        .main-container {
            max-width: 1400px;
            width: 100%;
            margin: 30px auto;
            padding: 0 20px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            flex-grow: 1;
        }

        @media (max-width: 1024px) {
            .main-container {
                grid-template-columns: 1fr;
            }
        }

        .glass-panel {
            background: var(--panel-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: border 0.3s ease;
        }

        .glass-panel:hover {
            border: 1px solid rgba(255, 255, 255, 0.12);
        }

        .panel-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .panel-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Чат истории разговоров */
        .chat-area {
            height: 380px;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            background: rgba(0, 0, 0, 0.15);
        }

        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 14px;
            font-size: 14px;
            line-height: 1.5;
            position: relative;
            animation: slide-up 0.3s ease;
        }

        .message.user {
            background: linear-gradient(135deg, rgba(9, 132, 227, 0.2), rgba(9, 132, 227, 0.15));
            border: 1px solid rgba(9, 132, 227, 0.3);
            align-self: flex-end;
            border-bottom-right-radius: 2px;
            color: #ffffff;
        }

        .message.assistant {
            background: linear-gradient(135deg, rgba(108, 92, 231, 0.15), rgba(108, 92, 231, 0.1));
            border: 1px solid rgba(108, 92, 231, 0.25);
            align-self: flex-start;
            border-bottom-left-radius: 2px;
            color: #f1f2f6;
        }

        .message-time {
            font-size: 10px;
            color: var(--text-secondary);
            margin-top: 5px;
            text-align: right;
            display: block;
        }

        /* Лог операций */
        .console-area {
            height: 250px;
            overflow-y: auto;
            padding: 15px 20px;
            background: #060813;
            font-family: 'Fira Code', monospace;
            font-size: 12px;
            line-height: 1.6;
            color: #00d2d3;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .console-line {
            display: flex;
            gap: 10px;
        }

        .console-time {
            color: #54a0ff;
            flex-shrink: 0;
        }

        .console-text {
            word-break: break-all;
            color: #a4b0be;
        }

        /* Настройки */
        .settings-content {
            padding: 25px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-height: 720px;
            overflow-y: auto;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }

        label {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
        }

        input, select, textarea {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            font-family: inherit;
            color: var(--text-primary);
            font-size: 14px;
            transition: all 0.3s ease;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--accent-blue);
            background: rgba(255, 255, 255, 0.07);
            box-shadow: 0 0 10px rgba(9, 132, 227, 0.25);
        }

        textarea {
            resize: vertical;
            min-height: 120px;
            line-height: 1.5;
        }

        .checkbox-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            background: rgba(255, 255, 255, 0.02);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
        }

        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            cursor: pointer;
        }

        .checkbox-item input {
            cursor: pointer;
            width: 16px;
            height: 16px;
            accent-color: var(--accent-blue);
        }

        .btn-submit {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            border: none;
            border-radius: 8px;
            padding: 14px;
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3);
            text-align: center;
            margin-top: 10px;
        }

        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(108, 92, 231, 0.45);
        }

        .btn-submit:active {
            transform: translateY(0);
        }

        /* Уведомления */
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: rgba(46, 213, 115, 0.95);
            color: #ffffff;
            padding: 15px 25px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }

        .toast.error {
            background: rgba(255, 76, 76, 0.95);
        }

        /* Анимации */
        @keyframes pulse-glow {
            from { box-shadow: 0 0 10px rgba(108, 92, 231, 0.4); }
            to { box-shadow: 0 0 25px rgba(108, 92, 231, 0.7); }
        }

        @keyframes pulse-glow-dot {
            from { box-shadow: 0 0 6px var(--state-speaking); }
            to { box-shadow: 0 0 15px var(--state-speaking); }
        }

        @keyframes pulse-blink {
            0% { opacity: 0.3; }
            50% { opacity: 1; }
            100% { opacity: 0.3; }
        }

        @keyframes slide-up {
            from { transform: translateY(15px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        /* Скроллбар */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body class="state-idle" id="app-body">
    <header>
        <div class="logo-section">
            <div class="logo-circle"></div>
            <h1>Алиса • Панель Управления</h1>
        </div>
        <div class="status-pill" id="status-pill">
            <div class="status-dot"></div>
            <span id="status-text">ОЖИДАНИЕ</span>
        </div>
    </header>

    <div class="main-container">
        <!-- Левая колонка: Диалог и Лог -->
        <div style="display: flex; flex-direction: column; gap: 25px;">
            <!-- История диалога -->
            <div class="glass-panel">
                <div class="panel-header">
                    <div class="panel-title">💬 История диалога</div>
                </div>
                <div class="chat-area" id="chat-area">
                    <div class="message assistant">
                        Привет! Я ваша локальная Алиса. Чем могу помочь?
                        <span class="message-time">00:00</span>
                    </div>
                </div>
            </div>

            <!-- Лог операций -->
            <div class="glass-panel">
                <div class="panel-header">
                    <div class="panel-title">💻 Консоль операций</div>
                </div>
                <div class="console-area" id="console-area">
                    <div class="console-line">
                        <span class="console-time">[00:00:00]</span>
                        <span class="console-text">Инициализация веб-интерфейса панели управления...</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Правая колонка: Настройки -->
        <div class="glass-panel">
            <div class="panel-header">
                <div class="panel-title">⚙️ Настройки колонки</div>
            </div>
            <div class="settings-content">
                <!-- Модели ASR и LLM -->
                <div class="form-row">
                    <div class="form-group">
                        <label for="asr_module">Служба ASR (Голос в текст)</label>
                        <select id="asr_module">
                            <option value="GroqASR">Groq ASR (Whisper-large Cloud)</option>
                            <option value="OpenaiASR">OpenAI Whisper Cloud</option>
                            <option value="VoskASR">Vosk ASR (Локальный оффлайн)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="llm_module">Служба LLM (Интеллект)</label>
                        <select id="llm_module">
                            <option value="DeepSeekLLM">DeepSeek LLM (DeepSeek-Chat)</option>
                            <option value="GeminiLLM">Google Gemini API</option>
                            <option value="OllamaLLM">Ollama (Локальный ИИ)</option>
                        </select>
                    </div>
                </div>

                <!-- API Ключи -->
                <div class="form-group">
                    <label for="groq_key">API Ключ Groq (для ASR)</label>
                    <input type="password" id="groq_key" placeholder="gsk_...">
                </div>

                <div class="form-group">
                    <label for="deepseek_key">API Ключ ИИ (DeepSeek / Gemini)</label>
                    <input type="password" id="deepseek_key" placeholder="Ключ авторизации модели">
                </div>

                <!-- Голос EdgeTTS -->
                <div class="form-group">
                    <label for="voice">Голос диктора (EdgeTTS)</label>
                    <select id="voice">
                        <option value="ru-RU-SvetlanaNeural">Светлана (Женский, Рекомендуется)</option>
                        <option value="ru-RU-DmitryNeural">Дмитрий (Мужской)</option>
                    </select>
                </div>

                <!-- Системный промпт характера -->
                <div class="form-group">
                    <label for="prompt">Системные инструкции (Промпт Алисы)</label>
                    <textarea id="prompt" placeholder="Инструкции для персонажа ассистента..."></textarea>
                </div>

                <!-- Активные плагины -->
                <div class="form-group">
                    <label>Включенные функции и плагины</label>
                    <div class="checkbox-group">
                        <label class="checkbox-item">
                            <input type="checkbox" id="plug_weather" value="get_weather_ru">
                            🌤️ Погода (Open-Meteo)
                        </label>
                        <label class="checkbox-item">
                            <input type="checkbox" id="plug_news" value="get_news_ru">
                            📰 Новости Украины
                        </label>
                        <label class="checkbox-item">
                            <input type="checkbox" id="plug_music" value="play_music">
                            🎵 Поиск/Загрузка музыки
                        </label>
                        <label class="checkbox-item">
                            <input type="checkbox" id="plug_search" value="web_search">
                            🔍 Google поиск
                        </label>
                    </div>
                </div>

                <button class="btn-submit" onclick="saveConfig()">Сохранить настройки</button>
            </div>
        </div>
    </div>

    <div class="toast" id="toast">
        <span id="toast-text">Настройки успешно применены!</span>
    </div>

    <script>
        const stateTranslations = {
            'IDLE': 'ОЖИДАНИЕ',
            'LISTENING': 'ЗАПИСЬ ГОЛОСА',
            'THINKING': 'АНАЛИЗ И ОТВЕТ',
            'SPEAKING': 'ГОВОРИТ'
        };

        // Загрузка настроек при старте
        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                
                document.getElementById('asr_module').value = config.asr_module || 'GroqASR';
                document.getElementById('llm_module').value = config.llm_module || 'DeepSeekLLM';
                document.getElementById('groq_key').value = config.groq_key || '';
                document.getElementById('deepseek_key').value = config.deepseek_key || '';
                document.getElementById('voice').value = config.voice || 'ru-RU-SvetlanaNeural';
                document.getElementById('prompt').value = config.prompt || '';

                // Простановка чекбоксов плагинов
                const functions = config.functions || [];
                document.getElementById('plug_weather').checked = functions.includes('get_weather_ru');
                document.getElementById('plug_news').checked = functions.includes('get_news_ru');
                document.getElementById('plug_music').checked = functions.includes('play_music');
                document.getElementById('plug_search').checked = functions.includes('web_search');
            } catch (err) {
                console.error('Ошибка загрузки настроек:', err);
                showToast('Ошибка загрузки настроек с сервера', true);
            }
        }

        // Сохранение настроек
        async function saveConfig() {
            const functions = [];
            if (document.getElementById('plug_weather').checked) functions.push('get_weather_ru');
            if (document.getElementById('plug_news').checked) functions.push('get_news_ru');
            if (document.getElementById('plug_music').checked) functions.push('play_music');
            if (document.getElementById('plug_search').checked) functions.push('web_search');

            const payload = {
                asr_module: document.getElementById('asr_module').value,
                llm_module: document.getElementById('llm_module').value,
                groq_key: document.getElementById('groq_key').value,
                deepseek_key: document.getElementById('deepseek_key').value,
                voice: document.getElementById('voice').value,
                prompt: document.getElementById('prompt').value,
                functions: functions
            };

            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const res = await response.json();
                if (res.status === 'success') {
                    showToast('Конфигурация сохранена и применена!');
                } else {
                    showToast(res.message || 'Ошибка сохранения', true);
                }
            } catch (err) {
                showToast('Сетевая ошибка при сохранении настроек', true);
            }
        }

        function showToast(text, isError = false) {
            const toast = document.getElementById('toast');
            const toastText = document.getElementById('toast-text');
            toastText.textContent = text;
            if (isError) {
                toast.classList.add('error');
            } else {
                toast.classList.remove('error');
            }
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        // Периодическое обновление логов и статуса (Long Polling)
        let lastLogCount = 0;
        let lastChatCount = 0;

        async function pollStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                // Обновление состояния и класса тела документа
                const state = data.state || 'IDLE';
                const body = document.getElementById('app-body');
                body.className = 'state-' + state.toLowerCase();
                
                document.getElementById('status-text').textContent = stateTranslations[state] || state;

                // Обновление консоли операций
                const consoleArea = document.getElementById('console-area');
                if (data.logs && data.logs.length !== lastLogCount) {
                    consoleArea.innerHTML = '';
                    data.logs.forEach(log => {
                        const line = document.createElement('div');
                        line.className = 'console-line';
                        line.innerHTML = `<span class="console-time">[${log.time}]</span><span class="console-text">${log.event}</span>`;
                        consoleArea.appendChild(line);
                    });
                    lastLogCount = data.logs.length;
                    consoleArea.scrollTop = consoleArea.scrollHeight;
                }

                // Обновление диалогового лога
                const chatArea = document.getElementById('chat-area');
                if (data.chat && data.chat.length !== lastChatCount) {
                    chatArea.innerHTML = '';
                    data.chat.forEach(msg => {
                        const bubble = document.createElement('div');
                        bubble.className = `message ${msg.role}`;
                        bubble.innerHTML = `${msg.text}<span class="message-time">${msg.time}</span>`;
                        chatArea.appendChild(bubble);
                    });
                    lastChatCount = data.chat.length;
                    chatArea.scrollTop = chatArea.scrollHeight;
                }

            } catch (err) {
                console.error('Ошибка опроса статуса:', err);
            }
        }

        // Запуск
        loadConfig();
        setInterval(pollStatus, 1000);
    </script>
</body>
</html>
"""

class SimpleHttpServer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.ota_handler = OTAHandler(config)
        self.vision_handler = VisionHandler(config)
        
        # Сохраняем ссылку на конфиг для редактирования в рантайме
        from core.utils import dashboard_shared as ds
        ds.GLOBAL_CONFIG_REF = config

    def _get_websocket_url(self, local_ip: str, port: int) -> str:
        server_config = self.config["server"]
        websocket_config = server_config.get("websocket")

        if websocket_config and "你" not in websocket_config:
            return websocket_config
        else:
            return f"ws://{local_ip}:{port}/xiaozhi/v1/"

    # --- HTTP Обработчики для Панели управления (Dashboard) ---

    async def handle_dashboard_index(self, request):
        """Возвращает веб-страницу панели управления"""
        return web.Response(text=DASHBOARD_HTML, content_type="text/html", charset="utf-8")

    async def handle_api_status(self, request):
        """Возвращает текущее состояние системы, чат и консольные логи"""
        from core.utils import dashboard_shared as ds
        return web.json_response({
            "state": ds.CURRENT_STATE,
            "logs": ds.LOG_EVENTS,
            "chat": ds.CHAT_HISTORY
        })

    async def handle_api_get_config(self, request):
        """Возвращает текущие настройки колонки для отображения в форме"""
        cfg = self.config
        return web.json_response({
            "voice": cfg.get("TTS", {}).get("EdgeTTS", {}).get("voice", "ru-RU-SvetlanaNeural"),
            "prompt": cfg.get("prompt", ""),
            "groq_key": cfg.get("ASR", {}).get("GroqASR", {}).get("api_key", ""),
            "deepseek_key": cfg.get("LLM", {}).get("DeepSeekLLM", {}).get("api_key", ""),
            "asr_module": cfg.get("selected_module", {}).get("ASR", "GroqASR"),
            "llm_module": cfg.get("selected_module", {}).get("LLM", "DeepSeekLLM"),
            "functions": cfg.get("Intent", {}).get("function_call", {}).get("functions", [])
        })

    async def handle_api_save_config(self, request):
        """Принимает новые настройки, сохраняет их в файл и обновляет в памяти"""
        try:
            data = await request.json()
            custom_config_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/.config.yaml"
            
            # Читаем существующий .config.yaml
            if os.path.exists(custom_config_path):
                with open(custom_config_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
            else:
                cfg = {}

            # Обновляем поля
            if "voice" in data:
                cfg.setdefault("TTS", {}).setdefault("EdgeTTS", {})["voice"] = data["voice"]
            if "prompt" in data:
                cfg["prompt"] = data["prompt"]
            if "groq_key" in data:
                cfg.setdefault("ASR", {}).setdefault("GroqASR", {})["api_key"] = data["groq_key"]
            if "deepseek_key" in data:
                cfg.setdefault("LLM", {}).setdefault("DeepSeekLLM", {})["api_key"] = data["deepseek_key"]
            if "asr_module" in data:
                cfg.setdefault("selected_module", {})["ASR"] = data["asr_module"]
            if "llm_module" in data:
                cfg.setdefault("selected_module", {})["LLM"] = data["llm_module"]
            if "functions" in data:
                cfg.setdefault("Intent", {}).setdefault("function_call", {})["functions"] = data["functions"]

            # Сохраняем в data/.config.yaml
            os.makedirs(os.path.dirname(custom_config_path), exist_ok=True)
            with open(custom_config_path, "w", encoding="utf-8") as f:
                yaml.dump(cfg, f, allow_unicode=True)

            # Обновляем глобальную конфигурацию в оперативной памяти сервера
            for k, v in cfg.items():
                if isinstance(v, dict) and k in self.config:
                    self.config[k].update(v)
                else:
                    self.config[k] = v

            # Обновляем кэш
            from core.utils.cache.manager import cache_manager, CacheType
            cache_manager.set(CacheType.CONFIG, "main_config", self.config)

            from core.utils import dashboard_shared as ds
            ds.add_event("Настройки успешно изменены пользователем и сохранены на диск.")

            return web.json_response({"status": "success", "message": "Настройки успешно сохранены!"})
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Ошибка сохранения настроек: {e}")
            return web.json_response({"status": "error", "message": f"Ошибка: {str(e)}"}, status=500)

    # -------------------------------------------------------------

    async def start(self):
        try:
            server_config = self.config["server"]
            read_config_from_api = self.config.get("read_config_from_api", False)
            host = server_config.get("ip", "0.0.0.0")
            port = int(server_config.get("http_port", 8003))

            if port:
                app = web.Application()

                # Маршруты панели управления (Dashboard)
                app.add_routes(
                    [
                        web.get("/", self.handle_dashboard_index),
                        web.get("/api/status", self.handle_api_status),
                        web.get("/api/config", self.handle_api_get_config),
                        web.post("/api/config", self.handle_api_save_config),
                    ]
                )

                if not read_config_from_api:
                    # OTA роуты
                    app.add_routes(
                        [
                            web.get("/xiaozhi/ota/", self.ota_handler.handle_get),
                            web.post("/xiaozhi/ota/", self.ota_handler.handle_post),
                            web.options(
                                "/xiaozhi/ota/", self.ota_handler.handle_options
                            ),
                            web.get(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_download,
                            ),
                            web.options(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_options,
                            ),
                        ]
                    )
                # Зрение роуты
                app.add_routes(
                    [
                        web.get("/mcp/vision/explain", self.vision_handler.handle_get),
                        web.post(
                            "/mcp/vision/explain", self.vision_handler.handle_post
                        ),
                        web.options(
                            "/mcp/vision/explain", self.vision_handler.handle_options
                        ),
                    ]
                )

                # 运行服务
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, host, port)
                await site.start()

                # 保持服务运行
                while True:
                    await asyncio.sleep(3600)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"HTTP服务器启动失败: {e}")
            import traceback

            self.logger.bind(tag=TAG).error(f"错误堆栈: {traceback.format_exc()}")
            raise
