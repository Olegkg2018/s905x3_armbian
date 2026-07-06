import requests
from bs4 import BeautifulSoup
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

GET_NEWS_RU_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_news_ru",
        "description": "Получить последние новости на русском языке для Украины. Вызывай этот инструмент, когда пользователь просит рассказать новости.",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Количество новостей для вывода, по умолчанию 5.",
                }
            },
            "required": [],
        },
    },
}

@register_function("get_news_ru", GET_NEWS_RU_FUNCTION_DESC, ToolType.WAIT)
def get_news_ru(conn: "ConnectionHandler", count: int = 5):
    logger.bind(tag=TAG).info(f"get_news_ru (Украина) вызван для вывода {count} новостей")
    if not count or count <= 0:
        count = 5
        
    try:
        # Украинская Правда (русскоязычная лента новостей)
        url = "https://www.pravda.com.ua/rus/rss/"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
            )
        }
        
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        # Парсим XML
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        
        if not items:
            soup = BeautifulSoup(resp.content, "html.parser")
            items = soup.find_all("item")
            
        if not items:
            return ActionResponse(
                action=Action.REQLLM,
                result="Не удалось получить ленту новостей Украины.",
                response=None
            )
            
        news_list = []
        for i, item in enumerate(items[:count]):
            title = item.find("title")
            title_text = title.text.strip() if title else "Без заголовка"
            
            description = item.find("description")
            desc_text = description.text.strip() if description else ""
            
            # Очищаем текст от HTML-тегов
            desc_text = BeautifulSoup(desc_text, "html.parser").get_text().strip()
            
            if desc_text:
                news_list.append(f"{i+1}. {title_text} — {desc_text}")
            else:
                news_list.append(f"{i+1}. {title_text}")
                
        result_text = "Последние новости Украины:\n" + "\n\n".join(news_list)
        logger.bind(tag=TAG).info("get_news_ru (Украина) успешно получил новости")
        return ActionResponse(action=Action.REQLLM, result=result_text, response=None)
        
    except Exception as e:
        logger.bind(tag=TAG).error(f"Ошибка получения украинских новостей: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result="Не удалось получить новости из-за сетевой ошибки. Пожалуйста, попробуйте позже.",
            response=None
        )
