
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from time import sleep
from playwright.sync_api import sync_playwright

class VestiParser:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.vesti.ru/",
        }

    # ==================== НОВЫЙ МЕТОД ====================
    def get_all_news_links(self, max_articles: int = 300, max_scrolls: int = 40) -> list:
        """Собирает ссылки на все новости, прокручивая ленту"""
        links = []
        seen = set()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=self.headers["User-Agent"],
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            print("Загружаем страницу...")
            page.goto("https://www.vesti.ru/ns", wait_until="networkidle", timeout=30000)
            sleep(4)

            for scroll_num in range(max_scrolls):
                # Прокручиваем вниз
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                sleep(4)  # даём время на подгрузку новой секции

                # Собираем все видимые ссылки
                items = page.query_selector_all('a.news-feed-item[href^="/ns/"]')
                
                new_count = 0
                for item in items:
                    href = item.get_attribute("href") or ""
                    if not href.startswith("/ns/"):
                        continue
                        
                    url = "https://www.vesti.ru" + href
                    if url not in seen:
                        seen.add(url)
                        title = item.get_attribute("aria-label") or ""
                        links.append({"url": url, "list_title": title.strip()})
                        new_count += 1

                print(f"Прокрутка #{scroll_num + 1}: всего ссылок = {len(links)} (+{new_count})")

                if len(links) >= max_articles:
                    break

                # Если за последние 3 прокрутки ничего не добавилось — скорее всего конец
                if new_count == 0 and scroll_num > 5:
                    print("Новых ссылок не появляется — останавливаемся.")
                    break

            browser.close()

        return links[:max_articles]

    # ==================== ТВОИ МЕТОДЫ БЕЗ ИЗМЕНЕНИЙ ====================
    def parse_prefix(self, text: str):
        # твой код без изменений
        pattern = r'^([А-Яа-яЁё\- ]+?)\s+(\d{1,2}\s+[а-яё]+)\s+([А-Яа-яЁё\s\.\-]+)\.'
        match = re.match(pattern, text.strip())
        if match:
            city = match.group(1).strip()
            date = match.group(2).strip()
            source = match.group(3).strip().rstrip('.')
            return city, date, source
        return None, None, None

    def extract_clean_article_text(self, soup):
        article_body = soup.find("div", class_="article-body")
        if not article_body:
            return ""

        parts = []
        seen = set()

        for tag in article_body.find_all(["p", "blockquote"]):
            tag_classes = tag.get("class", []) or []

            if "citation_text" in tag_classes:
                text = tag.get_text(separator=" ", strip=True).strip("«»\"' ")
                if text:
                    text = f"«{text}»"
            else:
                text = tag.get_text(separator=" ", strip=True)
                text = " ".join(text.split())

            if text and text not in seen:
                seen.add(text)
                parts.append(text)

        absorbed = set()          
        for i, text in enumerate(parts):
            for j, other in enumerate(parts):
                if i != j and text in other and len(text) < len(other):
                    absorbed.add(text)
                    break

        final_parts = []
        for text in parts:
            if text in absorbed:
                continue  

            modified = text
            for short in absorbed:
                if short in text:
                    modified = modified.replace(short, f"«{short}»", 1)

            final_parts.append(modified)

        return "\n\n".join(final_parts)

    # # ==================== ОБНОВЛЁННЫЙ get_vesti_news ====================
    # def get_vesti_news(self, max_articles: int = 200) -> dict:
    #     print("Собираем ссылки через Playwright...")
    #     links = self.get_all_news_links(max_articles=max_articles)
    #     print(f"\nВсего найдено ссылок: {len(links)}\n")

    #     news_data = {}

    #     for ind, link in enumerate(links):
    #         sleep(2.5)  # уважение к сайту
    #         print(f"Обрабатываем статью #{ind + 1} / {len(links)}")

    #         try:
    #             resp_art = requests.get(link["url"], headers=self.headers, timeout=15)
    #             resp_art.raise_for_status()
    #             soup_art = BeautifulSoup(resp_art.text, "lxml")

    #             # === твой код извлечения заголовка, даты, текста ===
    #             h1 = soup_art.find("h1", {"itemprop": "headline"}) or soup_art.find("h1")
    #             header = h1.get_text(strip=True) if h1 else "Заголовок не найден"

    #             time_tag = soup_art.find("time", {"itemprop": "datePublished"})
    #             date_raw = time_tag.get("datetime") if time_tag else None
    #             if date_raw:
    #                 try:
    #                     dt = datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
    #                     pub_date = dt.strftime("%d.%m.%Y %H:%M")
    #                 except:
    #                     pub_date = date_raw
    #             else:
    #                 pub_date = None

    #             full_text = self.extract_clean_article_text(soup_art)
    #             city, prefix_date, source = self.parse_prefix(full_text)

    #             if city:
    #                 prefix_str = f"{city} {prefix_date} {source}."
    #                 if full_text.startswith(prefix_str):
    #                     text = full_text[len(prefix_str):].lstrip()
    #                 else:
    #                     text = full_text.replace(prefix_str + " ", "", 1).strip()
    #             else:
    #                 text = full_text
    #                 city = prefix_date = source = None

    #             news_data[link["url"]] = {
    #                 "title": header,
    #                 "city": city,
    #                 "date": prefix_date,
    #                 "source_id": 3,
    #                 "text": text,
    #             }

    #         except Exception as e:
    #             print(f"Ошибка на {link['url']}: {e}")
    #             continue

    #     return news_data

    def stream_recent_news(self, max_new_articles: int = 300, 
                       scroll_step: int = 6,
                       max_scrolls_without_new: int = 5,
                       article_delay: float = 2.5):
        """
        Динамически скроллит ленту и парсит статьи "на лету".
        Подгружает новые секции только когда нужно.
        """
        seen_in_session = set()
        parsed_count = 0
        scrolls_without_new = 0

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": self.headers["User-Agent"]})

            print("[Vesti] Загружаем https://www.vesti.ru/ns ...")
            page.goto("https://www.vesti.ru/ns", wait_until="networkidle", timeout=30000)
            sleep(4)

            while parsed_count < max_new_articles and scrolls_without_new < max_scrolls_without_new:
                # Скроллим несколько раз, чтобы подгрузить новые секции
                for _ in range(scroll_step):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    sleep(4)

                # Получаем все текущие ссылки на странице
                links = page.query_selector_all('a.news-feed-item[href^="/ns/"]')
                
                new_links_this_scroll = 0

                for link_el in links:
                    href = link_el.get_attribute("href") or ""
                    if not href.startswith("/ns/"):
                        continue

                    url = "https://www.vesti.ru" + href
                    if url in seen_in_session:
                        continue

                    seen_in_session.add(url)
                    new_links_this_scroll += 1

                    # === ПАРСИМ СТАТЬЮ СРАЗУ ===
                    try:
                        sleep(article_delay)
                        resp = requests.get(url, headers=self.headers, timeout=12)
                        soup = BeautifulSoup(resp.text, "lxml")

                        h1 = soup.find("h1", {"itemprop": "headline"}) or soup.find("h1")
                        title = h1.get_text(strip=True) if h1 else ""

                        time_tag = soup.find("time", {"itemprop": "datePublished"})
                        pub_date = None
                        if time_tag and time_tag.get("datetime"):
                            try:
                                dt = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
                                pub_date = dt.strftime("%d.%m.%Y %H:%M")
                            except:
                                pub_date = time_tag["datetime"]

                        full_text = self.extract_clean_article_text(soup)
                        city, prefix_date, source = self.parse_prefix(full_text)

                        if city:
                            prefix_str = f"{city} {prefix_date} {source}."
                            text = full_text[len(prefix_str):].lstrip() if full_text.startswith(prefix_str) else full_text
                        else:
                            text = full_text

                        if len(text) < 80:
                            continue

                        parsed_count += 1

                        yield {
                            "url": url,
                            "title": title,
                            "text": text,
                            "city": city,
                            "date": prefix_date or pub_date,
                            "source_id": 3
                        }

                        print(f"[Vesti] ✓ Спарсено {parsed_count}/{max_new_articles}")

                        if parsed_count >= max_new_articles:
                            break

                    except Exception as e:
                        print(f"[Vesti] Ошибка парсинга {url}: {e}")
                        continue

                # Логика "нужно ли скроллить дальше"
                if new_links_this_scroll == 0:
                    scrolls_without_new += 1
                    print(f"[Vesti] Нет новых ссылок... ({scrolls_without_new}/{max_scrolls_without_new})")
                else:
                    scrolls_without_new = 0  # сброс счётчика

            browser.close()

        print(f"[Vesti] Завершено. Спарсено новых статей: {parsed_count}")


if __name__ == "__main__":
    vp = VestiParser()
    data = vp.get_vesti_news(max_articles=150)   # ← здесь задаёшь сколько нужно
    print(f"\nИтогово спарсено статей: {len(data)}")