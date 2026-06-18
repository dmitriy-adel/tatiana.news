import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from typing import Dict, Iterator, Optional


class LentaParser:
    def __init__(self):
        self.parsed_urls: list[str] = []

    def scrape_lenta_article(self, url: str, session: requests.Session, source_id: int = 1) -> Optional[Dict]:
        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"    Ошибка загрузки статьи: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('span', class_='topic-body__title') or soup.find('h1', class_='topic-body__title')
        title = title_tag.get_text(strip=True) if title_tag else None

        paragraphs = soup.find_all('p', class_='topic-body__content-text')
        text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        full_text = '\n\n'.join(text_parts)

        if not title or len(full_text) < 100:
            return None

        return {
            "url": url,
            "title": title,
            "text": full_text,
            "source_id": source_id
        }

    def stream_news_for_date(self, date_str: str, delay: float = 8.0, max_pages: int = 10) -> Iterator[Dict]:
        """
        Стриминговый парсинг одной конкретной даты (например "2026/06/12").
        Парсит главную страницу дня + все страницы пагинации.
        Выдаёт статьи по одной.
        """
        base_url = f"https://lenta.ru/news/{date_str}/"
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                        '(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        })

        page = 1
        current_url = base_url
        seen_on_date = set()

        print(f"[Lenta] Начинаем дату {date_str} (задержка {delay}с)")

        while page <= max_pages:
            try:
                resp = session.get(current_url, timeout=12)
                resp.raise_for_status()
            except Exception as ex:
                print(f"  Ошибка загрузки страницы {current_url}: {ex}")
                break

            soup = BeautifulSoup(resp.text, 'html.parser')

            links_on_page = []
            prefix = f"/news/{date_str}/"
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if href.startswith(prefix) or href.startswith(f"https://lenta.ru{prefix}"):
                    full_url = urljoin("https://lenta.ru", href)
                    if full_url not in seen_on_date:
                        seen_on_date.add(full_url)
                        links_on_page.append(full_url)

            print(f"  Страница {page}: найдено {len(links_on_page)} статей")

            for i, link in enumerate(links_on_page, 1):
                article = self.scrape_lenta_article(link, session)
                if article:
                    yield article
                time.sleep(delay)

            # Ищем следующую страницу пагинации
            next_page = None
            for a in soup.find_all('a', href=True):
                href = str(a.get('href', ''))
                if f"/page/{page + 1}/" in href:
                    next_page = urljoin("https://lenta.ru", href)
                    break

            if not next_page:
                print(f"  Дата {date_str}: пагинация закончилась на странице {page}")
                break

            current_url = next_page
            page += 1
            time.sleep(delay)

        print(f"[Lenta] Дата {date_str} завершена. Обработано страниц: {page}")


if __name__ == "__main__":
    from datetime import datetime
    lp = LentaParser()
    # Тест одной даты
    for i, art in enumerate(lp.stream_news_for_date("2026/06/11", delay=3.0, max_pages=1), 1):
        print(f"{i}. {art['title'][:70]}")
        if i >= 2:
            break