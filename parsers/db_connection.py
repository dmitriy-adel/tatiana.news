import os
import psycopg2

private_vars = os.environ

DB_HOST: str = private_vars["DB_HOST"]
DB_PORT: str = private_vars["DB_PORT"]
DB_NAME: str = private_vars["DB_NAME"]
DB_USER: str = private_vars["DB_USER"]
DB_PASSWORD: str = private_vars["DB_PASSWORD"]


class DBConnection:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        self.conn.autocommit = True

    def add_news(self, source_id: int, url: str, title: str, text: str, vector: str, class_id: int = 1,) -> None:
        try:
            query = f"""
                INSERT INTO news(class_id, source_id, url, title, text, vector)
                VALUES ('{class_id}', '{source_id}', '{url}', '{title}', '{text}', '{vector}');
            """
    
            with self.conn.cursor() as cursor:
                cursor.execute(query)
    
        except Exception as _ex:
            print(f"[parsers->db_connection->add_news]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")

    def get_parsed_urls_by_source(self, source_id: int) -> int:
        try:
            query = f"""
                SELECT n.url
                FROM news as n
                WHERE n.source_id = {source_id};
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()
                res: list[int] = [t[0] for t in query_res]
                return res
            
        except Exception as _ex:
            print(f"[parsers->db_connection->get_parsed_urls_by_source]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_sources_map(self) -> dict:
        try:
            query = f"""
                SELECT ns.id, ns.source_name, ns.source_url
                FROM news_sources as ns;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()
                res: dict = {}
                for t in query_res:
                    res[t[0]] = {
                        "name": t[1],
                        "url": t[2]
                    }
                return res
            
        except Exception as _ex:
            print(f"[parsers->db_connection->get_parsed_urls_by_source]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        