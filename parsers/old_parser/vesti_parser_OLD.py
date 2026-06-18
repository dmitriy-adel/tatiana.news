# import requests
# from bs4 import BeautifulSoup
# from datetime import datetime
# import re

# from time import sleep

# class VestiParser:
#     def __init__(self):
#         self.headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
#             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
#             "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#             "Referer": "https://www.vesti.ru/",
#         }

#     def parse_prefix(self, text: str):
#         pattern = r'^([А-Яа-яЁё\- ]+?)\s+(\d{1,2}\s+[а-яё]+)\s+([А-Яа-яЁё\s\.\-]+)\.'
#         match = re.match(pattern, text.strip())
#         if match:
#             city = match.group(1).strip()
#             date = match.group(2).strip()
#             source = match.group(3).strip().rstrip('.')
#             return city, date, source
#         return None, None, None

#     def extract_clean_article_text(self, soup):
#         article_body = soup.find("div", class_="article-body")
#         if not article_body:
#             return ""

#         parts = []
#         seen = set()

#         for tag in article_body.find_all(["p", "blockquote"]):
#             tag_classes = tag.get("class", []) or []

#             if "citation_text" in tag_classes:
#                 text = tag.get_text(separator=" ", strip=True).strip("«»\"' ")
#                 if text:
#                     text = f"«{text}»"
#             else:
#                 text = tag.get_text(separator=" ", strip=True)
#                 text = " ".join(text.split())

#             if text and text not in seen:
#                 seen.add(text)
#                 parts.append(text)

#         absorbed = set()          
#         for i, text in enumerate(parts):
#             for j, other in enumerate(parts):
#                 if i != j and text in other and len(text) < len(other):
#                     absorbed.add(text)
#                     break

#         final_parts = []
#         for text in parts:
#             if text in absorbed:
#                 continue  

#             modified = text
#             for short in absorbed:
#                 if short in text:
#                     modified = modified.replace(short, f"«{short}»", 1)

#             final_parts.append(modified)

#         return "\n\n".join(final_parts)


#     def get_vesti_news(self) -> dict:
#         url_list = "https://www.vesti.ru/ns"
#         resp = requests.get(url_list, headers=self.headers, timeout=15)
#         resp.raise_for_status()
#         soup_list = BeautifulSoup(resp.text, "lxml")

#         links = []
#         for a in soup_list.find_all("a", class_="news-feed-item"):
#             href = a.get("href", "")
#             if href.startswith("/ns/"):
#                 links.append({
#                     "url": "https://www.vesti.ru" + href,
#                     "list_title": a.get("aria-label", "").strip()
#                 })

#         print(f"total links in first session: {len(links)}\n")

#         news_data = {}   

#         if links:
#             for ind, link in enumerate(links):
#                 if ind < 45:
#                     continue

#                 sleep(3)
#                 print(f"Обрабатываем статью #{ind + 1}...")

#                 resp_art = requests.get(link["url"], headers=self.headers, timeout=15)
#                 resp_art.raise_for_status()
#                 soup_art = BeautifulSoup(resp_art.text, "lxml")

#                 h1 = soup_art.find("h1", {"itemprop": "headline"}) or soup_art.find("h1")
#                 header = h1.get_text(strip=True) if h1 else "Заголовок не найден"

#                 time_tag = soup_art.find("time", {"itemprop": "datePublished"})
#                 date_raw = time_tag.get("datetime") if time_tag else None
#                 if date_raw:
#                     try:
#                         dt = datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
#                         pub_date = dt.strftime("%d.%m.%Y %H:%M")

#                     except:
#                         pub_date = date_raw
#                 else:
#                     pub_date = None

#                 full_text = self.extract_clean_article_text(soup_art)
#                 city, prefix_date, source = self.parse_prefix(full_text)

#                 if city:
#                     prefix_str = f"{city} {prefix_date} {source}."
#                     if full_text.startswith(prefix_str):
#                         text = full_text[len(prefix_str):].lstrip()
#                     else:
#                         text = full_text.replace(prefix_str + " ", "", 1).strip()
#                 else:
#                     text = full_text
#                     city = prefix_date = source = None

#                 news_data[link["url"]] = {
#                     "title": header,
#                     "city": city,
#                     "date": prefix_date,
#                     "source_id": 3,
#                     "text": text,
#                 }

#         return news_data

# if __name__ == "__main__":
#     vp = VestiParser()
#     print(vp.get_vesti_news())