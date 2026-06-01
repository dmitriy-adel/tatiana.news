import re

class Tools:

    @staticmethod
    def clean_to_vect(text: str) -> str:
        text = text.lower()
        text = text.strip()
        
        text = re.sub(r'[^a-zа-яё0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
