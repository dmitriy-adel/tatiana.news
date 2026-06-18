import re
from datetime import datetime, timedelta
from typing import Iterator


class Tools:

    @staticmethod
    def clean_to_vect(text: str) -> str:
        text = text.lower()
        text = text.strip()
        
        text = re.sub(r'[^a-zа-яё0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    @staticmethod
    def generate_dates_backward(start_date: datetime, end_date: datetime) -> Iterator[datetime]:
        current = start_date
        while current >= end_date:
            yield current
            current -= timedelta(days=1)

    @staticmethod
    def format_lenta_date(d: datetime) -> str:
        return d.strftime("%Y/%m/%d")

    @staticmethod
    def format_mk_date(d: datetime) -> str:
        return f"{d.year}/{d.month}/{d.day}"