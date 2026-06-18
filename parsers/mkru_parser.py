import requests
from bs4 import BeautifulSoup
import re
from time import sleep
from typing import Dict, Iterator
from datetime import datetime, timedelta


class MKRuParser:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.mk.ru/",
        }

    def get_article_text(self, url: str) -> str:
        try:
            print(f"    Загружаем текст: {url.split('/')[-2] if '/' in url else url}")
            resp = requests.get(url, headers=self.headers, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            candidates = [
                soup.find("div", class_="article__body"),
                soup.find("div", {"itemprop": "articleBody"}),
                soup.find("article"),
                soup.find("div", class_=re.compile(r"article|content|body|text|story", re.I)),
                soup.find("main"),
                soup.find("div", id=re.compile(r"article|content|main|text", re.I)),
            ]
            article_body = next((c for c in candidates if c), None)

            if not article_body:
                h1 = soup.find(["h1", "h2"])
                if h1:
                    article_body = h1.find_parent() or soup.body

            if article_body:
                paragraphs = article_body.find_all("p")
                text_parts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 15]

                if text_parts:
                    return "\n\n".join(text_parts)

                full_text = article_body.get_text(separator="\n\n", strip=True)
                full_text = re.sub(r'\n{3,}', '\n\n', full_text)
                if len(full_text) > 150:
                    return full_text

            return ""
        
        except Exception as _ex:
            print(f"[MKRu_parser->get_article_text]. Some error with text parsing for {url}: {_ex}")
            return ""

    def get_news_links(self, url: str) -> Dict[str, dict]:
        resp = requests.get(url, headers=self.headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        news_map = {}

        article_pattern = re.compile(r'/\d{4}/\d{2}/\d{2}/[^/]+\.html')

        uls = soup.find_all("ul")
        best_ul = None
        max_count = 0

        for ul in uls:
            matching = [li for li in ul.find_all("li") if li.find("a", href=article_pattern)]
            if len(matching) > max_count:
                max_count = len(matching)
                best_ul = ul

        items = best_ul.find_all("li") if best_ul else soup.find_all("li")

        for item in items:
            a_tag = item.find("a", href=True)
            if not a_tag:
                continue

            href = a_tag.get("href", "").strip()
            if not article_pattern.search(href):
                continue

            full_url = "https://www.mk.ru" + href if href.startswith("/") else href

            time_text = a_tag.get_text(strip=True)
            pub_time = re.sub(r'[\[\]]', '', time_text).strip() if time_text else None

            li_text = item.get_text(separator=" ", strip=True)
            title = re.sub(r'^\[?\d{1,2}:\d{2}\]?\s*', '', li_text).strip()
            title = re.sub(r'\s+', ' ', title).strip()

            if full_url and title and len(title) > 10:
                news_map[full_url] = {
                    "title": title,
                    "publication_time": pub_time,
                    "source_id": 2
                }

        return news_map

    @staticmethod
    def generate_dates_backward(start_date: datetime, end_date: datetime) -> Iterator[datetime]:
        current = start_date
        while current >= end_date:
            yield current
            current -= timedelta(days=1)

    def stream_news(self, day_url: str = "https://www.mk.ru/news/2026/6/12/") -> Iterator[Dict]:  # здесь указал дату, на момент которой тестировал парсер. для диплома, может быть, бедут проведен парсинг новых новостей
        print(f"[MKRu] Получаем список новостей с {day_url}")
        links_dict = self.get_news_links(day_url)
        print(f"[MKRu_parser->stream_news]. found {len(links_dict)} news links. start parsing...")

        for idx, (url, meta) in enumerate(links_dict.items(), 1):
            print(f"  [{idx}/{len(links_dict)}] Обрабатываем MK статью...")
            text = self.get_article_text(url)

            if text and len(text) > 100:
                yield {
                    "url": url,
                    "title": meta["title"],
                    "text": text,
                    "source_id": 2
                }
            else:
                print(f"    !!  Record was skipped because of little amount of text: {meta['title'][:50]}")

            sleep(4)

        print(f"[MKRu_parser->stream_news]. got all lnks. got total: {len(links_dict)}")

    def count_news_for_day(self, day_url: str) -> int:
        links_dict = self.get_news_links(day_url)
        return len(links_dict)
    
    def stream_news_for_date(self, date_str: str, delay: float = 8.0) -> Iterator[Dict]:
        import re
        from datetime import datetime as dt

        cleaned = date_str.strip().replace('-', '/').replace('.', '/')

        if re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', cleaned):
            day_url = f"https://www.mk.ru/news/{cleaned}/"
        else:
            parsed = False
            for fmt in ('%Y/%m/%d', '%d/%m/%Y', '%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d'):
                try:
                    d = dt.strptime(cleaned, fmt)
                    day_url = f"https://www.mk.ru/news/{d.year}/{d.month}/{d.day}/"
                    parsed = True
                    break

                except ValueError:
                    continue

            if not parsed:
                day_url = f"https://www.mk.ru/news/{cleaned}/"

        print(f"[MKRu] stream_news_for_date → {day_url}")
        yield from self.stream_news(day_url=day_url)


if __name__ == "__main__":
    mk = MKRuParser()  # костыльные тысте. а чего бы нет
    test_dates = [
        datetime(2026, 6, 12),
        datetime(2026, 6, 11),
        datetime(2026, 6, 10),
        datetime(2026, 6, 9),
        datetime(2026, 6, 8),
        datetime(2026, 6, 7),
        datetime(2026, 6, 6),
    ]

    for d in test_dates:
        day_url = f"https://www.mk.ru/news/{d.year}/{d.month}/{d.day}/"
        count = mk.count_news_for_day(day_url)
        print(f"{d.strftime('%Y-%m-%d')}: {count} total links found")
