import os
import psycopg2
from datetime import datetime


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

    # --------------------------------------------------
    #               select queries
    # --------------------------------------------------

    def get_user_id_by_collection_id(self, collection_id: int) -> int:
        try:
            query = f"""
                SELECT unc.user_id
                FROM users_news_collections as unc
                WHERE unc.id = {collection_id};
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()
                return query_res[0][0]
            
        except Exception as _ex:
            print(f"[db_connection.py->get_user_id_by_collection_id]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_user_name_by_id(self, user_id: int) -> str:
        try:
            query = f"""
                SELECT u.name
                FROM users as u
                WHERE u.id = {user_id};
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()
                return query_res[0][0]
            
        except Exception as _ex:
            print(f"[db_connection.py->get_user_id_by_collection_id]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
        
    def get_user_by_id(self, user_id: int) -> list[dict]:
        try:
            query = f"""
                SELECT u.name, u.email
                FROM users as u
                WHERE u.id = {user_id};
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                cursor_fetch = cursor.fetchall()
                res: dict = {"name": cursor_fetch[0][0],
                            "email": cursor_fetch[0][1]}
                return res
        
        except Exception as _ex:
            print(f"[db_connection.py->get_user_by_id]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_user_password(self, user_email: str) -> dict:
        try:
            query = f"""
                SELECT u.id, u.hash_password
                FROM users as u
                WHERE u.email = '{user_email}';
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                cursor_fetch = cursor.fetchall()
                res: dict = {"id": cursor_fetch[0][0], "pswd": cursor_fetch[0][1]}
                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_user_password]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_user_email_by_id(self, user_id: int) -> dict:
        try:
            query = f"""
                SELECT u.email
                FROM users as u
                WHERE u.id = '{user_id}';
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                cursor_fetch = cursor.fetchall()
                res: dict = {"email": cursor_fetch[0][0]}
                return res
        except Exception as _ex:
            print(f"[db_connection.py->get_user_email_by_id]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def check_user_for_admin(self, email: str) -> bool:
        try:
            query = f"""
                SELECT ua.id 
                FROM user_admins as ua
                WHERE ua.email = '{email}';
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                return True if cursor.fetchall() else False
            
        except Exception as _ex:
            print(f"[db_connection.py->get_user_id_by_email]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_user_totp_secret_by_email(self, user_email: int) -> dict:
        try:
            query = f"""
                SELECT u.totp_secret
                FROM users as u
                WHERE u.email = '{user_email}';
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                cursor_fetch = cursor.fetchall()
                res: dict = {"secret": cursor_fetch[0][0]}
                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_user_id_by_email]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_user_id_by_email(self, user_email: int) -> dict:
        try:
            query = f"""
                SELECT u.id
                FROM users as u
                WHERE u.email = '{user_email}';
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                cursor_fetch = cursor.fetchall()
                res: dict = {"id": cursor_fetch[0][0]}
                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_user_id_by_email]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_user_news_collections_by_user_id(self, user_id: int) -> list[dict]:
        try:
            query = f"""
                SELECT unc.id, unc.name, unc.comment, unc.news_ids, 
                        unc.last_update_date, unc.create_date
                FROM users_news_collections as unc
                WHERE unc.user_id = {user_id};
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()
                res: list[dict] = []
                for ind in range(len(query_res)):
                    temp_collection: dict = {
                        "collection_id": query_res[ind][0],
                        "collection_name": query_res[ind][1],
                        "collection_comment": query_res[ind][2],
                        "collection_news_ids": query_res[ind][3],
                        "collection_total_news": len(query_res[ind][3]),
                        "collection_last_updated_at": query_res[ind][4].strftime("%d.%m.%y"),
                        "collection_created_at": query_res[ind][5].strftime("%d.%m.%y")
                    }
                    res.append(temp_collection)

                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_user_news_collections_by_user_id]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")

    def get_all_news(self) -> list[dict]:
        try:
            query = """
                SELECT n.id, n.class_id, n.source_id, n.url, n.title, n.text, n.vector, n.created_at
                FROM news as n;
            """  

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()
                res: dict = {"news": {}, "total_news": len(query_res)}
                for ind in range(len(query_res)):
                    news_id: int = query_res[ind][0]
                    res['news'][news_id] = {
                        "class_id": query_res[ind][1],
                        "source_id": query_res[ind][2],
                        "url": query_res[ind][3],
                        "title": query_res[ind][4],
                        "text": query_res[ind][5],
                        "vector": query_res[ind][6],
                        "created_at": query_res[ind][7]
                    }
                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_all_news]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_all_news_classes(self) -> dict[int, str]:
        try:
            query: str = """
                SELECT nc.id, nc.name
                FROM news_classes as nc;
            """  

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()
                res: dict[int, str] = {}
                for ind in range(len(query_res)):
                    cls_id: int = query_res[ind][0]
                    res[cls_id] = query_res[ind][1]

                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_all_news_classes]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_last_news_max_per_cls(self, max_news_per_cls: int = 10) -> dict:
        try:
            query = f"""
                SELECT id, class_id, source_id, title, text, created_at
                FROM (
                    SELECT n.id, n.class_id, n.source_id, n.title, n.text, n.created_at, ROW_NUMBER() 
                    OVER (
                            PARTITION BY n.class_id 
                            ORDER BY n.created_at DESC
                        ) as rn
                    FROM news as n
                ) sub
                WHERE rn <= %s;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, (max_news_per_cls,))
                query_res = cursor.fetchall()

                res: dict = {}
                for row in query_res:
                    news_id = row[0]
                    res[news_id] = {
                        "class_id": row[1],
                        "source_id": row[2],
                        "title": row[3],
                        "text": row[4],
                        "created_at": row[5]
                    }

                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_last_news_max_per_cls]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_news_info(self, news_id: int) -> dict:
        try:
            query = f"""select n.title, n.text, n.url, n.source_id, n.created_at
                from news as n
                where n.id = %s
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, (news_id,))
                query_res = cursor.fetchall()
                res: dict = {
                    "title": query_res[0][0],
                    "text": query_res[0][1],
                    "url": query_res[0][2],
                    "source_id": query_res[0][3],
                    "created_at": query_res[0][4]
                }

                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_news_info]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_source_name_and_url(self, source_id: int) -> dict:
        try:
            query = """select ns.source_name, ns.source_url
                from news_sources as ns
                where ns.id = %s
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, (source_id,))
                query_res = cursor.fetchall()
                res: dict = {
                    "name": query_res[0][0],
                    "url": query_res[0][1],
                    }

                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_source_name_and_url]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")   
        
    def get_category_name(self, class_id: int) -> dict:
        try:
            query = """select nc.name
                from news_classes as nc
                where nc.id = %s
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, (class_id,))
                query_res = cursor.fetchall()
                res: dict = {
                    "name": query_res[0][0],
                    }

                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_source_name_and_url]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")   

    def get_all_sources(self) -> dict:
        try:
            query = """select ns.id, ns.source_name, ns.source_url
                from news_sources as ns;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()
                
                res: list[dict] = {}
                for t in query_res:
                    res[t[0]] = {
                        "name": t[1],
                        "url": t[2],
                        }

                return res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_source_name_and_url]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    
        
    def get_collection_news_ids(self, collection_id: int) -> list[int]:
        try:
            query = """select unc.news_ids
                from users_news_collections as unc
                where unc.id = %s;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, (collection_id,))
                query_res = cursor.fetchall()[0][0]

                return query_res
            
        except Exception as _ex:
            print(f"[db_connection.py->get_collection_news_ids]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")   

    def get_some_news_info(self, news_ids: list[int]) -> list[dict]:
        try:
            placeholders = ','.join(['%s'] * len(news_ids))
            
            query = f"""
                SELECT n.id, n.title, n.text, n.source_id, n.created_at
                FROM news as n
                WHERE n.id IN ({placeholders})
                ORDER BY n.created_at DESC;  
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, news_ids)
                rows = cursor.fetchall()

                result: list[dict] = []
                for row in rows:
                    result.append({
                        "news_id": row[0],
                        "news_title": row[1],
                        "news_text": row[2],
                        "source_id": row[3],
                        "news_created_at": row[4]
                    })

                return result

        except Exception as _ex:
            print(f"[db_connection.py->get_some_news_info]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_last_news_by_category_id(self, category_id: int) -> dict:
        try:
            query = f"""
                SELECT n.id, n.title, n.text, n.created_at
                FROM news as n
                WHERE n.class_id = {category_id}
                ORDER BY n.created_at DESC
                limit 20;  
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

                result: list[dict] = []
                for row in rows:
                    created_at = row[3]
                
                    if isinstance(created_at, datetime):
                        formatted_date = created_at.strftime("%d.%m.%Y")
                    else:
                        formatted_date = str(created_at).split()[0].replace("-", ".")

                    result.append({
                        "news_id": row[0],
                        "news_title": row[1],
                        "news_text": row[2],
                        "news_created_at": formatted_date
                    })

                return result

        except Exception as _ex:
            print(f"[db_connection.py->get_some_news_info]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    def get_news_comments(self, news_id: int, last_comment_id: int = None, limit: int = 15) -> dict:
        try:
            query = '''
                SELECT uc.id, uc.user_name, uc.created_at, uc.comment_text, uc.likes, uc.dislikes
                FROM user_comments as uc
                WHERE uc.news_id = %s
            '''
            params = [news_id]

            if last_comment_id is not None:
                query += ' AND uc.id < %s'
                params.append(last_comment_id)

            query += '''
                ORDER BY uc.id DESC
                LIMIT %s
            '''
            params.append(limit)

            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                result = []
                for row in rows:
                    result.append({
                        "id": row[0],
                        "user_name": row[1],
                        "created_at": row[2],
                        "comment_text": row[3],
                        "likes": row[4] or 0,
                        "dislikes": row[5] or 0
                    })

                return {
                    "comments": result,
                    "has_more": len(result) == limit
                }

        except Exception as ex:
            print(f"[get_news_comments] Error :: {ex}")
            raise RuntimeError("DB request error")
        
    def get_total_news(self):
        try:
            
            query = f"""
                select round(count(*) * 1.2)
                from news;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()

                result = {
                    "total_news": query_res[0][0]
                }

                return result

        except Exception as _ex:
            print(f"[db_connection.py->get_total_news]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")

    def get_most_popular_source(self):
        try:
            
            query = f"""
                select n.source_id as "source_id", count(*) as "total_news" 
                from news as n 
                group by n.source_id 
                order by total_news desc
                limit 1;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()

                result = {
                    "source_id": query_res[0][0]
                }

                return result

        except Exception as _ex:
            print(f"[db_connection.py->get_most_popular_source]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")

    def get_total_sources(self):
        try:
            
            query = f"""
                select count(*) * 2
                from news_sources;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()

                result = {
                    "total_sources": query_res[0][0]
                }

                return result

        except Exception as _ex:
            print(f"[db_connection.py->get_total_sources]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")

    def get_most_popular_class(self):
        try:
            
            query = f"""
                select n.class_id as "class_id", count(*) as "total_news" 
                from news as n 
                group by n.class_id 
                order by total_news desc 
                limit 1;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()

                result = {
                    "class_id": query_res[0][0]
                }

                return result

        except Exception as _ex:
            print(f"[db_connection.py->get_most_popular_class]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    
    def get_news_per_source(self):
        try:
            
            query = f"""
                select n.source_id as "source_id", count(*) as "total_news" 
                from news as n 
                group by n.source_id 
                order by total_news desc;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                query_res = cursor.fetchall()
                result = {}

                for t in query_res:
                    result[t[0]] = t[1]

                return result

        except Exception as _ex:
            print(f"[db_connection.py->get_news_per_source]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
        
    # --------------------------------------------------
    #               insert queries
    # --------------------------------------------------

    def create_user(self, name: str, email: str, last_online_date, 
                    role: str, hash_password: str, is_2fa: bool = False, totp_secret: str = None) -> list[dict]:
        try:
            query = f"""
                INSERT INTO users(name, email, last_online_date, 
                                    role, hash_password, is_2fa, totp_secret)
                VALUES ('{name}', '{email}', '{last_online_date}', 
                                    '{role}', '{hash_password}', '{is_2fa}', '{totp_secret}');
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)

        except Exception as _ex:
            print(f"[db_connection.py->create_user]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    

    def create_news_collection(self, user_id: int, name: str, description: str, last_update_date) -> None:
        try:
            query = f"""
                INSERT INTO users_news_collections(user_id, name, comment, last_update_date)
                VALUES ('{user_id}', '{name}', '{description}', '{last_update_date}');
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)

        except Exception as _ex:
            print(f"[db_connection.py->create_news_collection]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    

    def create_first_collection(self, user_id: int, last_update_date) -> None:
        try:
            query = f"""
                INSERT INTO users_news_collections(user_id, name, comment, last_update_date)
                VALUES ('{user_id}', 'Избранное', 'Это ваша первая коллекция новостей', '{last_update_date}');
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)

        except Exception as _ex:
            print(f"[db_connection.py->create_first_collection]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    

    def change_collections_fill(self, user_id: int, to_add: list[int], 
                                to_remove: list[int], news_id: int) -> None:
        try:
            with self.conn.cursor() as cursor:
                if to_add:
                    query_add = """
                        UPDATE public.users_news_collections AS unc
                        SET news_ids = array_append(
                            COALESCE(unc.news_ids, ARRAY[]::bigint[]),
                            %s::bigint
                        )
                        WHERE unc.id = ANY(%s::bigint[])
                          AND unc.user_id = %s
                          AND NOT (%s = ANY(unc.news_ids));   -- чтобы не дублировать, если уже есть
                    """
                    cursor.execute(query_add, (news_id, to_add, user_id, news_id))

                if to_remove:
                    query_remove = """
                        UPDATE public.users_news_collections
                        SET news_ids = array_remove(news_ids, %s)
                        WHERE id = ANY(%s::bigint[])
                          AND user_id = %s;
                    """
                    cursor.execute(query_remove, (news_id, to_remove, user_id))

                self.conn.commit()
                return True

        except Exception as _ex:
            self.conn.rollback() 
            print(f"[db_connection.py->change_collections_fill]. Error :: {_ex}")
            raise RuntimeError("DB request error")

    def add_news(self, class_id: int, source_id: int, url: str, 
                 title: str, text: str, key_words: str, vector: str, tags: str) -> list[dict]:
        try:
            query = f"""
                INSERT INTO news(class_id, source_id, url, title, 
                                    text, key_words, vector, tags)
                VALUES ('{class_id}', '{source_id}', '{url}', '{title}', 
                        '{text}', '{key_words}', '{vector}', '{tags}');
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)

        except Exception as _ex:
            print(f"[db_connection.py->add_news]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    

    def add_support_appeal(self, to_email: str, name: str, theme: str, 
                 message_text: str, is_answered: bool = False) -> list[dict]:
        try:
            query = f"""
                INSERT INTO tech_support_appeals(user_email, user_name, 
                                                    appeal_theme, appeal_text, is_answered)
                VALUES ('{to_email}', '{name}', '{theme}', '{message_text}', '{is_answered}');
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)

        except Exception as _ex:
            print(f"[db_connection.py->add_support_appeal]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    
        
    def add_comment(self, news_id: int, user_id: int, user_name: str, 
                    comment_text: str, replied_at_id: int | None = None) -> None:
        try:
            query = f"""
                INSERT INTO user_comments 
                    (news_id, user_id, user_name, comment_text, replied_at_id)
                VALUES 
                    ({news_id}, {user_id}, '{user_name}', '{comment_text}', 
                     {replied_at_id if replied_at_id is not None else 'NULL'});
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)

        except Exception as _ex:
            print(f"[db_connection.py->add_comment]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")

    def add_like(self, comment_id: int) -> None:
        try:
            query = f"""
                UPDATE user_comments 
                SET likes = likes + 1 
                WHERE id = {comment_id};
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)

        except Exception as _ex:
            print(f"[db_connection.py->add_like]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")

    def add_dislike(self, comment_id: int) -> None:
        try:
            query = f"""
                UPDATE user_comments 
                SET dislikes = dislikes + 1 
                WHERE id = {comment_id};
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)

        except Exception as _ex:
            print(f"[db_connection.py->add_dislike]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")
        
    # def remove_like(self, comment_id: int) -> None:
    #     try:
    #         query = f"""
    #             UPDATE user_comments 
    #             SET likes = likes - 1 
    #             WHERE id = {comment_id};
    #         """

    #         with self.conn.cursor() as cursor:
    #             cursor.execute(query)

    #     except Exception as _ex:
    #         print(f"[db_connection.py->add_like]. Error :: {_ex}")
    #         raise RuntimeError(status_code=500, detail="DB request error")

    # def remove_dislike(self, comment_id: int) -> None:
    #     try:
    #         query = f"""
    #             UPDATE user_comments 
    #             SET dislikes = dislikes - 1 
    #             WHERE id = {comment_id};
    #         """

    #         with self.conn.cursor() as cursor:
    #             cursor.execute(query)

    #     except Exception as _ex:
    #         print(f"[db_connection.py->add_dislike]. Error :: {_ex}")
    #         raise RuntimeError(status_code=500, detail="DB request error")

    # --------------------------------------------------
    #               update queries
    # --------------------------------------------------

    def confirm_2fa(self, email: str):
        try:
            query = f"UPDATE users SET is_2fa = TRUE WHERE email = '{email}'"
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                self.conn.commit()

        except Exception as _ex:
            print(f"[db_connection.py->confirm_2fa]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    


    def update_news_collection(self, collection_id: int, name: str, description: str, last_update_date) -> None:
        try:
            query = f"""
                UPDATE users_news_collections as unc
                SET name = '{name}',
                    comment = '{description}',
                    last_update_date = '{last_update_date}'

                WHERE id = {collection_id};
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                self.conn.commit()

        except Exception as _ex:
            print(f"[db_connection.py->update_news_collection]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    

    def update_user(self, user_id: int, update_dict: dict[str, any]) -> None:
        try:
            field_mapping = {
                "new_name": "name",
                "new_email": "email",
                "new_password": "hash_password"
            }

            fields_to_update = []
            values = []

            for input_key, db_column in field_mapping.items():
                if input_key in update_dict and update_dict[input_key] is not None:
                    fields_to_update.append(f"{db_column} = %s")
                    values.append(update_dict[input_key])

            if not fields_to_update:
                print("Warning: update_dict is empty or contains only None values")
                return

            set_clause = ", ".join(fields_to_update)
            query = f"""
                UPDATE users
                SET {set_clause}
                WHERE id = %s;
            """

            values.append(user_id)
            with self.conn.cursor() as cursor:
                cursor.execute(query, values)
                self.conn.commit()

        except Exception as _ex:
            print(f"[db_connection.py->update_user]. Error :: {_ex}")
            print(f'Error updating user {user_id}: {_ex}')
            if self.conn:
                self.conn.rollback()

    # --------------------------------------------------
    #               remove queries
    # --------------------------------------------------

    def remove_news_collection(self, collection_id: int) -> None:
        try:
            query = f"""
                DELETE FROM users_news_collections as unc
                WHERE unc.id = {collection_id};
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                self.conn.commit()

        except Exception as _ex:
            print(f"[db_connection.py->remove_news_collection]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    

    def remove_user(self, user_id: int, admin_id: int, comment: str) -> None:
        try:
            query = """
                DELETE FROM users
                WHERE id = %s;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                self.conn.commit()

        except Exception as _ex:
            print(f"[db_connection.py->remove_user]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    

    def remove_news(self, news_id: int) -> None:
        try:
            query = """
                DELETE FROM news
                WHERE news_id = %s;
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, (news_id))
                self.conn.commit()

        except Exception as _ex:
            print(f"[db_connection.py->remove_news]. Error :: {_ex}")
            raise RuntimeError(status_code=500, detail="DB request error")    
