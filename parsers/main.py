
# from datetime import datetime
# # from models_manager import Vectorier
# import time
# from tools import Tools
# from db_connection import DBConnection

# from lenta_parser import LentaParser
# from mkru_parser import MKRuParser
# from vesti_parser import VestiParser


# class ParserModule:
#     def __init__(self):
#         print("Инициализация ParserModule v3 (даты + стриминг + 8 сек задержка)...")
#         self.mk_pars = MKRuParser()
#         self.lenta_pars = LentaParser()
#         self.vesti_pars = VestiParser()

#         self.dbc = DBConnection()
#         self.tls = Tools()
#         # self.vect = Vectorier()

#         self.sources_map = self.dbc.get_sources_map()
#         print(f"✓ Карта источников загружена")

#     def _get_parsed_urls(self, source_id: int) -> set:
#         try:
#             urls = self.dbc.get_parsed_urls_by_source(source_id=source_id)
#             return set(urls) if urls else set()
#         except Exception:
#             return set()

#     def process_lenta_by_dates(self, start_date: datetime, end_date: datetime, 
#                                delay: float = 8.0, max_pages_per_day: int = 5,
#                                max_days: int = None):

#         already_parsed = self._get_parsed_urls(1)
#         added = skipped = day_count = 0

#         for current_date in self.tls.generate_dates_backward(start_date, end_date):
#             if max_days and day_count >= max_days:
#                 print(f"Достигнут лимит max_days={max_days}")
#                 break

#             date_str = self.tls.format_lenta_date(current_date)
#             day_count += 1
#             print(f"\n▶️  {current_date.date()}  ({date_str})")

#             try:
#                 for article in self.lenta_pars.stream_news_for_date(
#                     date_str=date_str,
#                     delay=delay,
#                     max_pages=max_pages_per_day
#                 ):
#                     url = article["url"]
#                     if url in already_parsed:
#                         skipped += 1
#                         continue

#                     title = article.get("title", "").strip()
#                     text = article.get("text", "").strip()

#                     if len(text) < 100:
#                         continue

#                     self.dbc.add_news(
#                         source_id=1,
#                         url=url,
#                         title=title,
#                         text=text,
#                         class_id=1
#                     )
#                     added += 1
#                     print(f"   ✓ Сохранено [{added}] {title[:65]}")

#             except Exception as e:
#                 print(f"   ❌ Ошибка на дате {date_str}: {e}")

#         time.sleep(4)

#         print(f"\n→ Lenta завершено. Дней обработано: {day_count} | Добавлено: {added} | Пропущено: {skipped}")

#     def process_mk_by_dates(self, start_date: datetime, end_date: datetime,
#                             delay: float = 8.0, max_days: int = None):
#         """Парсит MK.ru по датам (задом наперёд)"""
#         print("\n" + "="*70)
#         print("📥 MK.RU — парсинг по датам (задом наперёд)")
#         print("="*70)

#         already_parsed = self._get_parsed_urls(2)
#         added = skipped = day_count = 0

#         for current_date in self.tls.generate_dates_backward(start_date, end_date):
#             if max_days and day_count >= max_days:
#                 print(f"Достигнут лимит max_days={max_days}")
#                 break

#             date_str = self.tls.format_mk_date(current_date)
#             day_count += 1
#             print(f"\n▶️  {current_date.date()}  ({date_str})")

#             try:
#                 for article in self.mk_pars.stream_news_for_date(
#                     date_str=date_str,
#                     delay=delay
#                 ):
#                     url = article["url"]
#                     if url in already_parsed:
#                         skipped += 1
#                         continue

#                     title = article.get("title", "").strip()
#                     text = article.get("text", "").strip()

#                     if len(text) < 100:          # поднял до 100 для единообразия с Lenta
#                         continue

#                     self.dbc.add_news(
#                         source_id=2,
#                         url=url,
#                         title=title,
#                         text=text,
#                         class_id=1
#                     )
#                     added += 1
#                     print(f"   ✓ Сохранено [{added}] {title[:65]}")

#             except Exception as e:
#                 print(f"   ❌ Ошибка на дате {date_str}: {e}")

#         time.sleep(2)

#         print(f"\n→ MK.ru завершено. Дней обработано: {day_count} | Добавлено: {added} | Пропущено: {skipped}")

#     def process_vesti_recent(self, max_articles: int = 350, delay: float = 3.0):
#         """
#         Парсит свежие новости из ленты Vesti.ru (/ns)
#         Использует Playwright для подгрузки секций + requests для статей
#         """
#         print("\n" + "="*70)
#         print("📥 VESTI.RU — парсинг свежих новостей из ленты")
#         print("="*70)

#         already_parsed = self._get_parsed_urls(3)   # source_id = 3 для Vesti
#         added = skipped = 0

#         print(f"Собираем до {max_articles} статей из ленты...")
#         try:
#             news_dict = self.vesti_pars.get_vesti_news(max_articles=max_articles)
#         except Exception as e:
#             print(f"❌ Ошибка при сборе ссылок Vesti: {e}")
#             return

#         print(f"Получено {len(news_dict)} статей. Начинаем обработку...\n")

#         for idx, (url, article) in enumerate(news_dict.items(), 1):
#             if url in already_parsed:
#                 skipped += 1
#                 continue

#             title = article.get("title", "").strip()
#             text = article.get("text", "").strip()

#             if len(text) < 100:
#                 continue

#             try:
#                 self.dbc.add_news(
#                     source_id=3,
#                     url=url,
#                     title=title,
#                     text=text,
#                     class_id=1
#                 )
#                 added += 1
#                 print(f"   ✓ Vesti [{added}] {title[:70]}")
#             except Exception as e:
#                 print(f"   ❌ Ошибка сохранения {url}: {e}")

#             time.sleep(delay)

#         print(f"\n→ Vesti завершено. Добавлено: {added} | Пропущено (уже есть): {skipped}")

#     def main_run(self, max_days: int = None):
#         START = datetime(2026, 6, 12)
#         END = datetime(2026, 6, 2)

#         # # Lenta
#         # self.process_lenta_by_dates(
#         #     start_date=START,
#         #     end_date=END,
#         #     delay=8.0,
#         #     max_pages_per_day=20,
#         #     max_days=max_days
#         # )

#         # MK.ru
#         self.process_mk_by_dates(
#             start_date=START,
#             end_date=END,
#             delay=4.0,
#             max_days=max_days
#         )

#         # self.process_vesti()


# if __name__ == "__main__":
#     module = ParserModule()

#     module.main_run(max_days=None)



from datetime import datetime
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from tools import Tools
from db_connection import DBConnection

from lenta_parser import LentaParser
from mkru_parser import MKRuParser
from vesti_parser import VestiParser


class ParserModule:
    def __init__(self):
        self.mk_pars = MKRuParser()
        self.lenta_pars = LentaParser()
        self.vesti_pars = VestiParser()

        self.dbc = DBConnection()
        self.tls = Tools()

        self.sources_map = self.dbc.get_sources_map()

        self.db_lock = threading.Lock()

    def _get_parsed_urls(self, source_id: int) -> set:
        try:
            urls = self.dbc.get_parsed_urls_by_source(source_id=source_id)
            return set(urls) if urls else set()
        except Exception:
            return set()


    def _mk_worker(self, start_date, end_date, delay, max_days, added_counter, lock):
        """Рабочий поток для MK.ru"""
        already_parsed = self._get_parsed_urls(2)
        day_count = 0

        for current_date in self.tls.generate_dates_backward(start_date, end_date):
            if max_days and day_count >= max_days:
                break
            day_count += 1

            date_str = self.tls.format_mk_date(current_date)
            print(f"\n[MK] ▶️ {current_date.date()} ({date_str})")

            try:
                for article in self.mk_pars.stream_news_for_date(date_str=date_str, delay=delay):
                    url = article["url"]
                    if url in already_parsed:
                        continue

                    title = article.get("title", "").strip()
                    text = article.get("text", "").strip()
                    if len(text) < 100:
                        continue

                    with lock:  # защищаем запись в БД
                        self.dbc.add_news(source_id=2, url=url, title=title, text=text, class_id=1)
                        added_counter[0] += 1
                        print(f"[MK]   ✓ [{added_counter[0]}] {title[:60]}")

            except Exception as e:
                print(f"[MK] ❌ Ошибка на {date_str}: {e}")


    def _vesti_worker(self, max_articles, delay, added_counter, lock):
        """Поток Vesti с динамической подгрузкой"""
        already_parsed = self._get_parsed_urls(3)

        for article in self.vesti_pars.stream_recent_news(
            max_new_articles=max_articles,
            scroll_step=5,
            max_scrolls_without_new=6,
            article_delay=delay
        ):
            url = article["url"]
            if url in already_parsed:
                continue

            title = article.get("title", "").strip()
            text = article.get("text", "").strip()

            if len(text) < 100:
                continue

            with lock:
                try:
                    self.dbc.add_news(
                        source_id=3,
                        url=url,
                        title=title,
                        text=text,
                        class_id=1
                    )
                    added_counter[0] += 1
                    print(f"[Vesti] ✓ Сохранено [{added_counter[0]}] {title[:65]}")

                except Exception as e:
                    print(f"[Vesti] ❌ Ошибка сохранения: {e}")

    def run_mk_and_vesti_parallel(self, max_days: int = None, vesti_articles: int = 400):
        START = datetime(2026, 6, 12)
        END = datetime(2026, 6, 2)

        added_counter = [0]       
        lock = self.db_lock

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Запускаем оба парсера одновременно
            future_mk = executor.submit(
                self._mk_worker,
                START, END, 4.0, max_days, added_counter, lock
            )
            future_vesti = executor.submit(
                self._vesti_worker,
                vesti_articles, 4.0, added_counter, lock
            )

            future_mk.result()
            future_vesti.result()

        print("\n" + "="*75)
        print(f"✅ Параллельная обработка завершена. Всего добавлено: {added_counter[0]}")
        print("="*75)

    def main_run(self, max_days: int = None):
        self.run_mk_and_vesti_parallel(max_days=max_days, vesti_articles=4000)

        # self.process_lenta_by_dates(...)


if __name__ == "__main__":
    module = ParserModule()
    module.main_run(max_days=None)