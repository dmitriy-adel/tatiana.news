import re
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

import torch
import torch.nn.functional as F
from torch import Tensor, inference_mode
from transformers import AutoTokenizer, AutoModel

from db_connection import DBConnection
from tools import Tools

DF_COLUMNS: list[str] = ['id', 'class_id', 'source_id', 'title', 'text', 'url', 'vector', 'created_at']


# =============================================
#           Prefix Search Sup Methods
# =============================================
class TrieNode:
    def __init__(self):
        self.children: dict[str, 'TrieNode'] = {}
        self.news_ids: set[int] = set()          


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, news_id: int):
        if not word:
            return
        
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()

            node = node.children[char]

        node.news_ids.add(news_id)

    def remove(self, word: str, news_id: int):
        if not word:
            return
        
        node = self.root
        for char in word:
            if char not in node.children:
                return  
            
            node = node.children[char]

        node.news_ids.discard(news_id)   

    def search_prefix(self, prefix: str) -> set[int]:
        if not prefix:
            return set()
        node = self.root
        for char in prefix:
            if char not in node.children:
                return set()
            node = node.children[char]

        return self._collect_ids(node)

    def _collect_ids(self, node: TrieNode) -> set[int]:
        result = set(node.news_ids)
        for child in node.children.values():
            result.update(self._collect_ids(child))

        return result

# ============================================= </prefix_search>


class SearchEngine:
    def __init__(self):
        self.dbc: DBConnection = DBConnection()
        self.tls: Tools = Tools()
        self.news_base_df: pd.DataFrame = pd.DataFrame(columns=DF_COLUMNS)

        self.title_trie: Trie = Trie()
        self.text_trie: Trie = Trie()

        self.tokenizer: AutoTokenizer = None
        self.model: AutoModel = None
        self.load_model_and_tokenizer()

        self.update_news_db()
        vectors = np.stack(self.news_base_df['vector'].apply(np.asarray).values)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if np.any(np.abs(norms - 1.0) > 1e-5):   
            print("Normilizing vectors...")
            vectors = vectors / norms
        
        self.doc_matrix = vectors.astype(np.float32)

    def load_model_and_tokenizer(self):
        self.tokenizer = AutoTokenizer.from_pretrained("deepvk/USER-bge-m3")
        self.model = AutoModel.from_pretrained("deepvk/USER-bge-m3")
        self.model.eval()

    def encode(self, text: str):
        encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt')
        with torch.no_grad():
            model_output = self.model(**encoded_input) 
            sentence_embeddings = model_output[0][:, 0]

        embed = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
        return embed.squeeze(0).numpy()

    def update_news_db(self) -> pd.DataFrame:
        """Полное обновление базы + перестройка trie"""
        news_info: dict = self.dbc.get_all_news()
        data: list[dict] = []
        for news_id, attrs in news_info['news'].items():
            row: dict = {'id': news_id, **attrs}
            data.append(row)

        self.news_base_df: pd.DataFrame = pd.DataFrame(data=data, columns=DF_COLUMNS)
        self.news_base_df['vector'] = self.news_base_df['vector'].apply(lambda x: eval(x))
        self.news_base_df['title_lower'] = self.news_base_df['title'].apply(lambda x: x.lower().strip())
        self.news_base_df['text_lower'] = self.news_base_df['text'].apply(lambda x: x.lower().strip())
        self._build_tries()          

        return self.news_base_df
    
    def _build_tries(self):
        self.title_trie: Trie = Trie()
        self.text_trie: Trie = Trie()

        for _, row in self.news_base_df.iterrows():
            news_id: int = int(row['id'])
            title: str = row.get('title', '')
            text: str = row.get('text', '')

            for word in self.tls.simple_tokenize(title):
                self.title_trie.insert(word, news_id)

            for word in self.tls.simple_tokenize(text):
                self.text_trie.insert(word, news_id)

    def vector_search(self, query: str, top_n: int = 10) -> pd.DataFrame:
        if self.news_base_df.empty or len(self.doc_matrix) == 0:
            return pd.DataFrame(columns=DF_COLUMNS + ['similarity'])

        query_emb = self.encode(query)                    
        query_vec = query_emb.astype(np.float32)

        similarities = cosine_similarity(
            [query_vec],          
            self.doc_matrix       
        )[0]
        top_indices = np.argsort(similarities)[::-1][:top_n]

        results = self.news_base_df.iloc[top_indices].copy()
        results['similarity'] = similarities[top_indices]

        return results.sort_values(by='similarity', ascending=False)

    def prefix_search(self, prefix: str) -> list[dict[str, any]]:
        if not prefix or len(prefix.strip()) < 2:
            return []

        prefix = prefix.lower().strip()

        # Ищем в title и text
        title_ids = self.title_trie.search_prefix(prefix)
        text_ids = self.text_trie.search_prefix(prefix)

        ordered_ids:list[int] = list(title_ids)
        seen = set(ordered_ids)
        for nid in text_ids:
            if nid not in seen:
                ordered_ids.append(nid)
                seen.add(nid)

        if not ordered_ids:
            return []

        result_ids = ordered_ids
        result_df = self.news_base_df[self.news_base_df['id'].isin(result_ids)]

        id_rank = {nid: idx for idx, nid in enumerate(ordered_ids)}
        result_df = result_df.copy()
        result_df['__rank'] = result_df['id'].map(id_rank)
        result_df = result_df.sort_values('__rank').drop(columns=['__rank'])

        return result_df.to_dict('records')
    

    def continue_user_request(self):  # TODO :: продолжает ввод пользователя до наиболее вероятного состояния. надо брать последние запросы пользователей и выдавать наиболее подходящий. обновлять базу запросов каждый час
        pass

    def full_text_search(self, user_request: str) -> list[dict]:  # полнотекстовый поиск. принимаемый текст должен полностью входить в какую-то строку
        query: str = user_request.lower().strip()
        tokens: list = re.findall(r'\w+', query)

        if not tokens:
            return []

        df: pd.DataFrame = self.news_base_df.copy()

        df['score'] = (
            df['text_lower'].apply(lambda x: self.tls.score(x, tokens)) +
            df['title_lower'].apply(lambda x: self.tls.score(x, tokens)) * 2  # костыльное ранжирование. упоминание в титуле важнее
        )
        df = df[df['score'] > 0]
        df = df.sort_values(by='score', ascending=False)

        df = df[
            ['id', 'text', 'title', 'source_id', 'class_id', 'url', 'created_at']
        ]

        return df.to_dict(orient='records')

    def rank_the_answer(self):  # ранжирование найденных ответов по релевантности 
        pass