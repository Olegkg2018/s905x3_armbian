import requests
from bs4 import BeautifulSoup
from config.logger import setup_logging
from plugins_func.register import (
    register_function,
    ToolType,
    ActionResponse,
    Action,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

_DEFAULT_DESCRIPTION = (
    "联网搜索工具。当用户需要获取最新网络信息或在Google上搜索问题时使用此工具。"
)

WEB_SEARCH_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": _DEFAULT_DESCRIPTION,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或问题",
                }
            },
            "required": ["query"],
        },
    },
}

def _search_google(query: str, max_results: int = 5) -> str:
    """через парсинг google.com в реальном времени"""
    url = f"https://www.google.com/search?q={query}&hl=ru"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
        )
    }
    
    logger.bind(tag=TAG).debug(f"Google Search request | URL: {url}")
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    
    # Ищем блоки результатов
    for g in soup.find_all("div", class_="g"):
        anchors = g.find_all("a")
        if not anchors:
            continue
        link = anchors[0].get("href")
        h3 = g.find("h3")
        title = h3.text if h3 else "Без заголовка"
        
        # Попытка найти описание (сниппет)
        snippet_div = g.find("div", class_="VwiC3b") or g.find("span", class_="aCO36e")
        snippet = snippet_div.text if snippet_div else ""
        
        if link and title:
            # Убираем гугловские редиректы
            if link.startswith("/url?q="):
                link = link.split("/url?q=")[1].split("&")[0]
            results.append((title, snippet, link))
            if len(results) >= max_results:
                break
                
    if not results:
        # Резервный парсинг всех h3 с ссылками
        for h3 in soup.find_all("h3"):
            parent_a = h3.find_parent("a")
            if parent_a:
                link = parent_a.get("href")
                if link.startswith("/url?q="):
                    link = link.split("/url?q=")[1].split("&")[0]
                results.append((h3.text, "", link))
                if len(results) >= max_results:
                    break
                    
    if not results:
        return "Не удалось найти результаты в Google."
        
    lines = ["【Результаты поиска в Google】"]
    for i, (title, snippet, link) in enumerate(results, 1):
        lines.append(f"{i}. {title}")
        if snippet:
            lines.append(f"   Описание: {snippet}")
        lines.append(f"   Ссылка: {link}")
        
    return "\n".join(lines)


def _search_metaso(api_key: str, query: str, max_results: int) -> str:
    url = "https://metaso.cn/api/v1/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "size": max_results,
        "stream": False,
        "scope": "webpage",
        "includeSummary": True,
        "includeRawContent": False,
        "conciseSnippet": False,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    webpages = data.get("webpages", [])
    if not webpages:
        return "未找到相关搜索结果。"
    lines = ["【联网搜索结果】"]
    for i, item in enumerate(webpages, 1):
        title = item.get("title", "无标题")
        snippet = item.get("summary", "")
        lines.append(f"{i}. 标题：{title}\n   摘要：{snippet}")
    return "\n".join(lines)


def _search_tavily(api_key: str, query: str, max_results: int) -> str:
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_answer": "advanced",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    answer = data.get("answer", "")
    return f"【联网搜索结果】\n总结：{answer}"


@register_function("web_search", WEB_SEARCH_FUNCTION_DESC, ToolType.SYSTEM_CTL)
def web_search(conn: "ConnectionHandler", query: str = None):
    logger.bind(tag=TAG).info(f"web_search (Google) вызван | query={query}")
    if not query:
        return ActionResponse(Action.REQLLM, "Пожалуйста, введите поисковый запрос.", None)

    web_search_config = conn.config.get("plugins", {}).get("web_search", {})
    provider = web_search_config.get("provider", "google").lower()
    max_results = int(web_search_config.get("max_results", 3))
    
    try:
        if provider == "google":
            result_text = _search_google(query, max_results)
        elif provider == "metaso":
            api_key = web_search_config.get("api_key", "")
            result_text = _search_metaso(api_key, query, max_results)
        elif provider == "tavily":
            api_key = web_search_config.get("api_key", "")
            result_text = _search_tavily(api_key, query, max_results)
        else:
            result_text = _search_google(query, max_results)
            
        logger.bind(tag=TAG).info("Google Search completed successfully.")
    except Exception as e:
        logger.bind(tag=TAG).error(f"Search exception: {e}")
        result_text = "Ошибка при выполнении поиска в интернете. Пожалуйста, попробуйте позже."

    return ActionResponse(Action.REQLLM, result_text, None)
