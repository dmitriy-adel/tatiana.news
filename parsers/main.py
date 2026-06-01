import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import os
from typing import List, Dict, Optional

from models_manager import Vectorier
from tools import Tools
from db_connection import DBConnection

class Parser():
    def __init__(self):
        self.dbc: DBConnection = DBConnection()
        self.vect: Vectorier = Vectorier()
        self.tls: Tools = Tools()

        self.sources_map: dict = self.dbc.get_sources_map()
        self.parsed_urls: list[str] = None

    def get_parsed_url_by_source(self, source_id: int) -> list[str]:
        return self.dbc.get_parsed_urls_by_source(source_id=source_id)

    def scrape_lenta_article(self, url: str, session: requests.Session, source_id: int = 1) -> Dict[str, Optional[str]]:

        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()

        except requests.RequestException as e:
            print(f" Ошибка загрузки статьи {url}: {e}")
            return {'url': url, 'title': None, 'text': None, 'status': 'error'}

        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('span', class_='topic-body__title') or \
                    soup.find('h1', class_='topic-body__title')
        title = title_tag.get_text(strip=True) if title_tag else None

        paragraphs = soup.find_all('p', class_='topic-body__content-text')
        text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        full_text = '\n\n'.join(text_parts)

        return {
            'url': url,
            'title': title,
            'text': full_text,
            'source_id': source_id,
        }

    def add_to_db(self, article_info: dict) -> None:
        try:
            vector = str(self.vect.get_vector(text=self.tls.clean_to_vect(text=article_info['text'])))
            self.dbc.add_news(source_id=article_info['source_id'], url=article_info['url'], 
                              title=article_info['title'], text=article_info['text'], vector=vector)

        except Exception as _ex:
            print(f"[parsers->main->add_to_db]. Error :: {_ex}. Data :: {article_info}")


    def scrape_lenta_day_incremental(self, base_url: str, delay: float = 10.0):
        """
        Постраничный парсинг архива + немедленное сохранение каждой статьи.
        """
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                        '(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        })

        page = 1
        current_url = base_url.rstrip('/') + '/'
        output_file = 'lenta_articles_2026-04-27.json'

        if os.path.exists(output_file):
            os.remove(output_file)


        while True:
            try:
                response = session.get(current_url, timeout=10)
                response.raise_for_status()
            except requests.RequestException as _ex:
                print(f"[main.py->scrape_lenta_day_incremental]. Cant laod url {current_url}. Error :: {_ex}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')

            current_page_links: List[str] = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].strip()
                if (href.startswith('/news/2026/04/25/') or 
                    href.startswith('https://lenta.ru/news/2026/04/25/')):
                    full_url = urljoin('https://lenta.ru', href)
                    if full_url not in current_page_links:
                        current_page_links.append(full_url)

            print(f"found {len(current_page_links)} articles on page {page}")

            for i, link in enumerate(current_page_links, 1):
                print(f"  [{i:2d}/{len(current_page_links)}] Обрабатываем: {link}")
                
                article = self.scrape_lenta_article(link, session)
                self.add_to_db(article_info=article)
                
                time.sleep(delay)

            next_page = None
            for a in soup.find_all('a', href=True):
                if f'/page/{page + 1}/' in a['href']:
                    next_page = urljoin('https://lenta.ru', a['href'])
                    break

            if not next_page:
                print("\n visited last page. breaking")
                break

            current_url = next_page
            page += 1

            print(f"changing page to {page}. waiting {delay} seconds...")
            time.sleep(delay)

        print(f"\n{'='*60}")
        print(f"Парсинг завершён! Все статьи сохранены в файл:")
        print(f"→ {output_file}")
        print(f"{'='*60}")

if __name__ == "__main__":
    day_url = "https://lenta.ru/2026/04/25/"
    pars: Parser = Parser()
    
    pars.scrape_lenta_day_incremental(base_url=day_url, delay=10.0)
