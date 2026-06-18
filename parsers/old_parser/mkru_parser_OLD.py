import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from time import sleep

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
            print(f"Загружаем статью: {url}")
            resp = requests.get(url, headers=self.headers, timeout=25)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml")

            article_body = soup.find("div", class_="article__body")
            if not article_body:
                article_body = soup.find("div", {"itemprop": "articleBody"})

            if not article_body:
                print("⚠️  Не найден блок article__body на странице")
                return ""

            paragraphs = article_body.find_all("p")

            text_parts = []
            for p in paragraphs:
                txt = p.get_text(strip=True)
                if txt:  
                    text_parts.append(txt)

            full_text = "\n\n".join(text_parts)
            return full_text

        except Exception as e:
            print(f"!! cant get text for {url}: {e}")
            return ""

    def get_news_links(self, url: str):
        resp = requests.get(url, headers=self.headers, timeout=25)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "lxml")
        news_map = {}
        
        items = soup.find_all("li", class_=re.compile("news-listing__item"))
        
        if not items:  
            items = soup.find_all("a", href=re.compile(r"/\d{4}/\d{2}/\d{2}/"))
        
        for item in items:
            a_tag = item.find("a", href=True) if hasattr(item, 'find') else item
            
            if not a_tag:
                continue
                
            href = a_tag.get("href", "")
            if not href:
                continue
                
            if href.startswith("/"):
                full_url = "https://www.mk.ru" + href
            else:
                full_url = href
                
            time_tag = item.find(class_=re.compile("time|pub|clock"))
            if not time_tag:
                time_match = re.search(r'(\d{1,2}:\d{2})', a_tag.get_text())
                pub_time = time_match.group(1) if time_match else None
            
            else:
                pub_time = time_tag.get_text(strip=True)
            
            title = a_tag.get_text(strip=True)
            title = re.sub(r'^\d{1,2}:\d{2}\s*', '', title).strip()
            
            date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', full_url)
            pub_day = date_match.group(3) if date_match else "10"  
            
            if full_url and title:
                news_map[full_url] = {
                    "publication_time": pub_time,
                    "publication_day": pub_day,
                    "title": title,
                    "text": "",
                    "source_id": 2
                }

        
        print(f"total news was found: {len(news_map)}")
        return news_map

    def get_news_info(self, url):
        news_data = self.get_news_links(url)

        for url, data in news_data.items():
            text = self.get_article_text(url)
            data["text"] = text
            sleep(2.5)

        return data


if __name__ == "__main__":
    pars = MKRuParser()
    print(pars.get_news_info(url="https://www.mk.ru/news/2026/6/12/"))
