import os
import re
import time
import random
import difflib
import traceback
import subprocess
import sys
import asyncio
from pathlib import Path
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.providers.tts.dto.dto import TTSMessageDTO, SentenceType, ContentType
from typing import TYPE_CHECKING
from config.logger import setup_logging

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

# Функция автоустановки yt-dlp при первом старте плагина
def install_ytdlp():
    try:
        import yt_dlp
    except ImportError:
        logger.bind(tag=TAG).info("Библиотека yt-dlp отсутствует. Установка yt-dlp...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            logger.bind(tag=TAG).info("Библиотека yt-dlp успешно установлена.")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Не удалось автоматически установить yt-dlp: {e}")

install_ytdlp()

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

MUSIC_CACHE = {}

play_music_function_desc = {
    "type": "function",
    "function": {
        "name": "play_music",
        "description": "Вызывай этот инструмент, когда пользователь просит включить или воспроизвести музыку, песню, исполнителя или жанр (например, 'включи спокойную музыку', 'включи песню Алсу Иногда', 'включи диско 80-х').",
        "parameters": {
            "type": "object",
            "properties": {
                "song_name": {
                    "type": "string",
                    "description": "Поисковый запрос музыки, название песни, исполнитель или стиль. Если пользователь просто просит включить музыку без уточнений, используй 'random'.",
                }
            },
            "required": ["song_name"],
        },
    },
}


def _find_best_match(potential_song, music_files):
    """Поиск лучшего совпадения среди локальных файлов"""
    best_match = None
    highest_ratio = 0
    potential_song = potential_song.lower().strip()

    for music_file in music_files:
        song_name = os.path.splitext(music_file)[0].lower()
        ratio = difflib.SequenceMatcher(None, potential_song, song_name).ratio()
        if ratio > highest_ratio and ratio > 0.5:
            highest_ratio = ratio
            best_match = music_file
    return best_match


def get_music_files(music_dir, music_ext):
    music_dir = Path(music_dir)
    music_files = []
    music_file_names = []
    for file in music_dir.rglob("*"):
        if file.is_file():
            ext = file.suffix.lower()
            if ext in music_ext:
                music_files.append(str(file.relative_to(music_dir)))
                music_file_names.append(
                    os.path.splitext(str(file.relative_to(music_dir)))[0]
                )
    return music_files, music_file_names


def initialize_music_handler(conn: "ConnectionHandler"):
    global MUSIC_CACHE
    if MUSIC_CACHE == {}:
        plugins_config = conn.config.get("plugins", {})
        if "play_music" in plugins_config:
            MUSIC_CACHE["music_config"] = plugins_config["play_music"]
            MUSIC_CACHE["music_dir"] = os.path.abspath(
                MUSIC_CACHE["music_config"].get("music_dir", "./music")
            )
            MUSIC_CACHE["music_ext"] = MUSIC_CACHE["music_config"].get(
                "music_ext", (".mp3", ".wav", ".p3")
            )
            MUSIC_CACHE["refresh_time"] = MUSIC_CACHE["music_config"].get(
                "refresh_time", 300
            )
        else:
            MUSIC_CACHE["music_dir"] = os.path.abspath("./music")
            MUSIC_CACHE["music_ext"] = (".mp3", ".wav", ".p3")
            MUSIC_CACHE["refresh_time"] = 300
            
        os.makedirs(MUSIC_CACHE["music_dir"], exist_ok=True)
        MUSIC_CACHE["music_files"], MUSIC_CACHE["music_file_names"] = get_music_files(
            MUSIC_CACHE["music_dir"], MUSIC_CACHE["music_ext"]
        )
        MUSIC_CACHE["scan_time"] = time.time()
    return MUSIC_CACHE


def _search_and_download_youtube(query: str, output_path: str) -> bool:
    """Синхронная функция скачивания звука из YouTube с помощью yt-dlp"""
    if yt_dlp is None:
        logger.error("yt_dlp не импортирован. Скачивание невозможно.")
        return False
        
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
            
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path.replace('.mp3', ''),  # yt-dlp сам добавит расширение
            'noplaylist': True,
            'default_search': 'ytsearch',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
        }
        logger.info(f"Запуск скачивания с YouTube для запроса: {query}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])
            
        # Проверяем, создался ли файл
        if os.path.exists(output_path):
            logger.info(f"Файл успешно скачан: {output_path}")
            return True
            
        # Если файл скачался, но имя слегка другое (например, .mp3 на конце добавился дважды)
        base_dir = os.path.dirname(output_path)
        base_name = os.path.basename(output_path).replace('.mp3', '')
        for f in os.listdir(base_dir):
            if f.startswith(base_name) and f.endswith('.mp3'):
                os.rename(os.path.join(base_dir, f), output_path)
                logger.info(f"Файл переименован и готов: {output_path}")
                return True
        return False
    except Exception as e:
        logger.error(f"Ошибка скачивания из YouTube: {e}")
        return False


async def speak_message(conn: "ConnectionHandler", text: str):
    """Отправка мгновенного голосового сообщения пользователю"""
    conn.tts.store_tts_text(conn.sentence_id, text)
    if conn.intent_type == "intent_llm":
        conn.tts.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=conn.sentence_id,
                sentence_type=SentenceType.FIRST,
                content_type=ContentType.ACTION,
            )
        )
    conn.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=conn.sentence_id,
            sentence_type=SentenceType.MIDDLE,
            content_type=ContentType.TEXT,
            content_detail=text,
        )
    )


async def handle_music_command(conn: "ConnectionHandler", song_name: str):
    initialize_music_handler(conn)
    global MUSIC_CACHE

    conn.logger.bind(tag=TAG).info(f"Обработка музыкального запроса: {song_name}")
    
    # 1. Если указано имя, ищем в локальной папке
    if song_name != "random" and len(MUSIC_CACHE["music_files"]) > 0:
        best_match = _find_best_match(song_name, MUSIC_CACHE["music_files"])
        if best_match:
            conn.logger.bind(tag=TAG).info(f"Найдена локальная музыка: {best_match}")
            await play_local_music(conn, specific_file=best_match)
            return True

    # 2. Если локально не найдено, ищем в интернете
    if song_name != "random":
        temp_song_name = "online_music_temp.mp3"
        temp_song_path = os.path.join(MUSIC_CACHE["music_dir"], temp_song_name)
        
        intro_text = f"Ищу песню «{song_name}» в интернете."
        await speak_message(conn, intro_text)
        
        # Скачиваем в фоновом потоке, чтобы не вешать вебсокет
        success = await asyncio.to_thread(
            _search_and_download_youtube, song_name, temp_song_path
        )
        
        if success and os.path.exists(temp_song_path):
            await play_local_music(conn, specific_file=temp_song_name, clean_display_name=song_name)
            return True
        else:
            await speak_message(conn, "К сожалению, мне не удалось найти или скачать этот трек.")
            return False

    # 3. Если random - играем случайную локальную
    await play_local_music(conn)
    return True


def _get_random_play_prompt(song_name):
    """Случайные фразы на русском перед запуском музыки"""
    clean_name = os.path.splitext(song_name)[0]
    prompts = [
        f"Включаю трек: {clean_name}.",
        f"Пожалуйста, слушайте: {clean_name}.",
        f"Включаю для вас: {clean_name}.",
        f"Сейчас заиграет: {clean_name}.",
        f"Приятного прослушивания: {clean_name}."
    ]
    return random.choice(prompts)


async def play_local_music(conn: "ConnectionHandler", specific_file=None, clean_display_name=None):
    global MUSIC_CACHE
    try:
        if not os.path.exists(MUSIC_CACHE["music_dir"]):
            conn.logger.bind(tag=TAG).error("Директория с музыкой отсутствует")
            return

        if specific_file:
            selected_music = specific_file
            music_path = os.path.join(MUSIC_CACHE["music_dir"], specific_file)
        else:
            if not MUSIC_CACHE["music_files"]:
                conn.logger.bind(tag=TAG).error("Локальные MP3 файлы не найдены")
                await speak_message(conn, "В папке музыки нет файлов для воспроизведения.")
                return
            selected_music = random.choice(MUSIC_CACHE["music_files"])
            music_path = os.path.join(MUSIC_CACHE["music_dir"], selected_music)

        if not os.path.exists(music_path):
            conn.logger.bind(tag=TAG).error(f"Файл не найден: {music_path}")
            return
            
        display_name = clean_display_name or os.path.splitext(selected_music)[0]
        text = _get_random_play_prompt(display_name)
        conn.tts.store_tts_text(conn.sentence_id, text)

        if conn.intent_type == "intent_llm":
            conn.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=conn.sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )
        # 1. Текст диктора
        conn.tts.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=conn.sentence_id,
                sentence_type=SentenceType.MIDDLE,
                content_type=ContentType.TEXT,
                content_detail=text,
            )
        )
        # 2. Аудиофайл песни
        conn.tts.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=conn.sentence_id,
                sentence_type=SentenceType.MIDDLE,
                content_type=ContentType.FILE,
                content_file=music_path,
            )
        )
        if conn.intent_type == "intent_llm":
            conn.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=conn.sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                )
            )

    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Ошибка воспроизведения локального аудио: {str(e)}")


@register_function("play_music", play_music_function_desc, ToolType.SYSTEM_CTL)
def play_music(conn: "ConnectionHandler", song_name: str):
    try:
        # Submit async task
        task = conn.loop.create_task(
            handle_music_command(conn, song_name)
        )

        def handle_done(f):
            try:
                f.result()
                conn.logger.bind(tag=TAG).info("Музыкальная команда успешно обработана")
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"Ошибка обработки музыки: {e}")

        task.add_done_callback(handle_done)

        return ActionResponse(
            action=Action.RECORD, result="Музыка найдена или скачивается", response="Ищу трек..."
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Ошибка запуска handle_music_command: {e}")
        return ActionResponse(
            action=Action.RESPONSE, result=str(e), response="Не удалось запустить проигрыватель."
        )
