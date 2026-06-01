import os
import secrets
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Depends, Response, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from time import time

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from db_connection import DBConnection
from tools import Tools
from rag import SearchEngine
from schemas import (SearchNewsRequest, CreateCollectionRequest, UpdateCollectionRequest, TechSupRequest, LoginUserRequest,
                    AddUserRequest, UserProfileUpdate, RemoveNewsCollectionRequest, GetCollectionNewsRequest, AddUserCommentRequest,
                    RemoveUserRequest, AddNewsRequest, RemoveNewsRequest, UpdateNewsRequest, GetNewsCommentsRequest,
                    VerificationEmailRequest, GetNewsInfoRequest, ChangeCollectionsFillRequest, LikeDislikeRequest,
                    Complete2FARegistration)

from redis_logic import lifespan
import pyotp


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost",
        "http://127.0.0.1"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

dbc: DBConnection = DBConnection()
tls: Tools = Tools()
se: SearchEngine = SearchEngine()

private_vars = os.environ
BASE_ROLE: str = private_vars["BASE_ROLE"]

# --------------------------------------------------
#               redis logic session_ids
# --------------------------------------------------

def get_redis(request: Request):
    if not hasattr(request.app.state, "redis"):
        raise RuntimeError("Redis client wasnt initialized yet")
    
    return request.app.state.redis

async def create_session(user_id: int, redis_client) -> str:
    session_id: str = secrets.token_urlsafe(32)
    key: str = f"session:{session_id}"

    session_data = {
        "user_id": str(user_id),
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
    }

    for field, value in session_data.items():
        await redis_client.hset(key, field, value)

    await redis_client.expire(key, 60 * 24 * 7)

    # print(f"Create session: {session_id[:8]}... for user {user_id}")
    return session_id

async def get_session(session_id: str, redis_client):
    if not session_id:
        return None
    
    key = f"session:{session_id}"
    data = await redis_client.hgetall(key)
    
    if not data or "user_id" not in data:
        return None

    await redis_client.expire(key, 60 * 24 * 7)
    
    return int(data["user_id"])

async def delete_session(session_id: str, redis_client):
    SESSION_PREFIX: str = "session:"
    if session_id:
        await redis_client.delete(f"{SESSION_PREFIX}{session_id}")

async def get_current_user_id_from_redis(request: Request, redis_client = Depends(get_redis)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not autorizedd")

    user_id = await get_session(session_id, redis_client)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Session expired")

    return user_id

# --------------------------------------------------
#               redis logic verification codes
# --------------------------------------------------

async def create_email_verification_code(email: str, code: str, redis_client) -> str:
    """
    Создаёт и сохраняет код подтверждения email в Redis
    Возвращает сгенерированный код
    """ 
    
    key = f"email_verification:{email}"
    
    verification_data = {
        "code": code,
        "attempts": "0",
        "created_at": datetime.utcnow().isoformat(),
    }

    for field, value in verification_data.items():
        await redis_client.hset(key, field, value)

    await redis_client.expire(key, 60 * 10)

    print(f"Код подтверждения создан для {email}: {code}")
    return code

async def get_email_verification_code(email: str, redis_client):
    """
    Получает данные кода подтверждения по email
    Возвращает dict или None, если код не найден или истёк
    """
    key = f"email_verification:{email}"
    data = await redis_client.hgetall(key)
    
    if not data:
        return None
    
    print('data items', data.items())
    return {k: v for k, v in data.items()}

async def delete_email_verification_code(email: str, redis_client):
    """Удаляет код подтверждения после успешной верификации"""
    key = f"email_verification:{email}"
    await redis_client.delete(key)

async def increment_verification_attempts(email: str, redis_client) -> int:
    """
    Увеличивает счётчик попыток ввода кода
    Возвращает текущее количество попыток
    """
    key = f"email_verification:{email}"
    attempts = await redis_client.hincrby(key, "attempts", 1)
    return attempts

async def verify_email_code(email: str, input_code: str, redis_client):
    data = await get_email_verification_code(email, redis_client)
    
    if not data:
        raise HTTPException(status_code=400, detail="Код истёк или не найден")
    
    attempts = int(data.get("attempts", 0))
    if attempts >= 5:
        raise HTTPException(status_code=429, detail="Слишком много попыток. Попробуйте позже.")
    
    if data.get("code") != input_code:
        await increment_verification_attempts(email, redis_client)
        raise HTTPException(status_code=400, detail="Неверный код")
    
    print("код подошел")
    await delete_email_verification_code(email, redis_client)
    return True

async def can_send_new_code(email: str, redis_client) -> bool:
    key = f"email_verification:{email}"
    exists = await redis_client.exists(key)
    return not bool(exists)

# --------------------------------------------------
#               sup logic
# --------------------------------------------------

@app.get("/health")
def health() -> dict[str, int]:
    return {"status": 200}

ph = PasswordHasher()
def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(stored_hash: str, provided_password: str) -> bool:
    try:
        ph.verify(stored_hash, provided_password)
        return True
    
    except VerifyMismatchError:
        return False
    
    except Exception as _ex:  
        print(f"[app.py->verify_password]. Verification error: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

# --------------------------------------------------
#               news logic
# --------------------------------------------------

@app.post("/add_news")
def add_news(request: AddNewsRequest):
    try:
        search_per: str = request.sp
        last_news = dbc.add_news(search_period=search_per)
        return last_news
    
    except Exception as _ex:
        print(f"[app.py->add_news]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.get("/get_news_classes")
async def get_news_classes():
    try:
        news_classes: dict[str, int] = dbc.get_all_news_classes()
        return news_classes
    
    except Exception as _ex:
        print(f"[app.py->get_news_classes]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

@app.post("/remove_news")
def remove_news(request: RemoveNewsRequest):
    try:
        last_news = dbc.remove_news(news_id=request.news_id)
        # result = dbc.get_news(
        #     user_id=request.user_id,
        #     search_string=request.search_string,
        #     filters=request.filters,
        #     current_news_max_pos=request.current_news_max_pos
        # )
        return last_news
    
    except Exception as _ex:
        print(f"[app.py->remove_news]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/update_news")
def update_news(request: UpdateNewsRequest):
    try:
        last_news = dbc.update_news(news_id=request.news_id, title=request.title, text=request.text, 
                                    url=request.url, class_id=request.class_id, source_id=request.source_id, 
                                    tags=request.tags, keywords=request.keywords)
        # result = dbc.get_news(
        #     user_id=request.user_id,
        #     search_string=request.search_string,
        #     filters=request.filters,
        #     current_news_max_pos=request.current_news_max_pos
        # )
        return last_news
    
    except Exception as _ex:
        print(f"[app.py->update_news]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

@app.post("/search_news")
def search_news(request: SearchNewsRequest):
    print('get request', request)
    try:
        search_string: str = request.search_string
        # filters: dict = request.filters
        search_period: int = request.search_period
        last_news = dbc.get_news(search_period=search_period)
        print(len(last_news), last_news)

        return {"output": ""}
    
    except Exception as _ex:
        print(f"[app.py->search_news]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

@app.get("/get_last_news")
def get_last_news():
    try:
        news_classes: dict = dbc.get_all_news_classes()
        all_news: dict = dbc.get_last_news_max_per_cls(max_news_per_cls=10)

        grouped_news: dict = {}
        for news_id, news_data in all_news.items():
            class_id = news_data["class_id"]
            class_name = news_classes.get(class_id, "unknown")

            if class_name not in grouped_news:
                grouped_news[class_name] = []

            news_item = news_data.copy()
            news_item["id"] = news_id
            del news_item["class_id"]

            grouped_news[class_name].append(news_item) 

        return grouped_news

    except Exception as _ex:
        print(f"[app.py->get_last_news]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/get_news_info")
def get_news_info(request: GetNewsInfoRequest):
    try:
        news_id: int = request.news_id
        news_info: dict = dbc.get_news_info(news_id=news_id)
        source_info: dict = dbc.get_source_name_and_url(source_id=news_info['source_id'])
        news_info['source_name'] = source_info['name']
        news_info['source_main_url'] = source_info['url']

        return news_info

    except Exception as _ex:
        print(f"[app.py->get_news_info]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/get_news_comments")
def get_news_comments(request: GetNewsCommentsRequest):
    try:
        news_comments = dbc.get_news_comments(news_id=request.news_id, 
                                              last_comment_id=request.last_comment_id, limit=request.limit)
        return news_comments

    except Exception as _ex:
        print(f"[app.py->get_news_comments]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/add_user_comment")
def add_user_comment(request: AddUserCommentRequest, user_id = Depends(get_current_user_id_from_redis)) -> dict:
    try:
        user_name: str = dbc.get_user_name_by_id(user_id=user_id)
        dbc.add_comment(news_id=request.news_id, user_id=user_id, user_name=user_name, 
                        comment_text=request.comment_text)
        return {"status": True}

    except Exception as _ex:
        print(f"[app.py->add_user_comment]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/add_comment_like")
def add_comment_like(request: LikeDislikeRequest) -> dict:
    try:
        dbc.add_like(comment_id=request.comment_id)
        return {"status": True}

    except Exception as _ex:
        print(f"[app.py->add_comment_like]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/add_comment_dislike")
def add_comment_dislike(request: LikeDislikeRequest) -> dict:
    try:
        dbc.add_dislike(comment_id=request.comment_id)
        return {"status": True}

    except Exception as _ex:
        print(f"[app.py->add_comment_dislike]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
# @app.post("/remove_comment_like")
# def remove_comment_like(request: LikeDislikeRequest) -> dict:
#     try:
#         dbc.remove_like()
#         return {"status": True}

#     except Exception as _ex:
#         print(f"[app.py->]. Error :: {_ex}")
#         raise HTTPException(status_code=500, detail="Server error")
    
# @app.post("/remove_comment_dislike")
# def remove_comment_dislike(request: LikeDislikeRequest) -> dict:
#     try:
#         dbc.remove_dislike()
#         return {"status": True}

#     except Exception as _ex:
#         print(f"[app.py->]. Error :: {_ex}")
#         raise HTTPException(status_code=500, detail="Server error")

# --------------------------------------------------
#               new_collections logic
# --------------------------------------------------

@app.post("/create_news_collection")  # - корректно
def create_news_collection(request: CreateCollectionRequest, user_id: int = Depends(get_current_user_id_from_redis)):
    try:
        result = dbc.create_news_collection(
            user_id=user_id,
            name=request.news_collection_name,
            description=request.news_collection_description,
            last_update_date=datetime.now()
        )
        return result
    
    except Exception as _ex:
        print(f"[app.py->create_news_collection]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

@app.post("/update_news_collection")
def update_news_collection(request: UpdateCollectionRequest) -> dict[str, str]:
    try:
        dbc.update_news_collection(
            collection_id=request.news_collection_id,
            name=request.new_news_collection_name,
            description=request.new_news_collection_description,
            last_update_date=datetime.now()
        )
        return {"status": "ok"}
    
    except Exception as _ex:
        print(f"[app.py->update_news_collection]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

@app.post("/change_collections_fill")
def change_collections_fill(request: ChangeCollectionsFillRequest, user_id: int = Depends(get_current_user_id_from_redis)):
    try:
        dbc.change_collections_fill(
            user_id=user_id,
            to_add=request.to_add,
            to_remove=request.to_remove,
            news_id=request.news_id,
        )
        return {"status": True}
    
    except Exception as _ex:
        print(f"[app.py->change_collections_fill]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

@app.get("/get_user_news_collections") 
async def get_user_news_collections(user_id: int = Depends(get_current_user_id_from_redis)):
    try:
        user_collections: list[dict] = dbc.get_user_news_collections_by_user_id(user_id=user_id)
        return user_collections
    
    except Exception as _ex:
        print(f"[app.py->get_user_news_collections]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/remove_news_collection")  
def remove_news_collection(request: RemoveNewsCollectionRequest, user_id: int = Depends(get_current_user_id_from_redis)):
    try:
        # TODO добавить проверку, что коллекция принадлежит пользователю 
        # if dbc.get_user_id_by_collection_id(collection_id=request.collection_id):
        dbc.remove_news_collection(
            collection_id=request.collection_id,
        )
        return True
        
        # else:
        #     raise HTTPException(status_code=403, detail="Not your collection")    
    
    except Exception as _ex:
        print(f"[app.py->remove_news_collection]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/get_collection_news")
def get_collection_news(request: GetCollectionNewsRequest):
    try:
        news_ids: list[int] = dbc.get_collection_news_ids(collection_id=request.collection_id)
        news_info: list[dict] = dbc.get_some_news_info(news_ids=news_ids)

        source_info: dict = dbc.get_all_sources()
        for t in range(len(news_info)):
            news_info[t]['news_source_name'] = source_info[news_info[t]['source_id']]['name']
            del news_info[t]['source_id']

        return news_info
    
    except Exception as _ex:
        print(f"[app.py->remove_news_collection]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

# --------------------------------------------------
#               user logic
# --------------------------------------------------

# @app.post("/add_user")  
# async def add_user(request: AddUserRequest, redis_client = Depends(get_redis)):
#     try:
#         hashed_pswd: str = hash_password(request.user_pswd)
#         if await verify_email_code(email=request.user_email, input_code=request.verification_code, redis_client=redis_client):
#             dbc.create_user(
#                 name=request.user_name,
#                 email=request.user_email,
#                 last_online_date=datetime.now(), 
#                 role=BASE_ROLE,  
#                 hash_password=hashed_pswd,
#                 is_2fa=request.user_email == 'dimablago210@gmail.com'
#             )
#             user_id: int = dbc.get_user_id_by_email(user_email=request.user_email)['id']
#             dbc.create_first_collection(user_id=user_id, last_update_date=datetime.now())
#             await delete_email_verification_code(email=request.user_email, redis_client=redis_client)
#             return {"status": True}
        
#         return {"status": False}
    
#     except Exception as _ex:
#         print(f"[app.py->add_user]. Error :: {_ex}")
#         raise HTTPException(status_code=500, detail="Server error")

@app.post("/add_user")  
async def add_user(request: AddUserRequest, redis_client = Depends(get_redis)):
    try:
        email = request.user_email.strip().lower()
        if not await verify_email_code(
            email=email, 
            input_code=request.verification_code, 
            redis_client=redis_client
        ):
            return {"status": False}

        hashed_pswd: str = hash_password(request.user_pswd)
        if email == 'dimablago210@gmail.com':
            totp_secret, qr_base64 = tls.generate_2fa_qr(email)

            dbc.create_user(
                name=request.user_name,
                email=email,
                last_online_date=datetime.now(), 
                role=BASE_ROLE,  
                hash_password=hashed_pswd,
                is_2fa=True,           
                totp_secret=totp_secret   
            )
            
            user_id: int = dbc.get_user_id_by_email(email)['id']
            dbc.create_first_collection(user_id=user_id, last_update_date=datetime.now())
            
            await delete_email_verification_code(email, redis_client)

            return {
                "status": True,
                "qr_code": qr_base64          
            }

        dbc.create_user(
            name=request.user_name,
            email=email,
            last_online_date=datetime.now(), 
            role=BASE_ROLE,  
            hash_password=hashed_pswd,
            is_2fa=False
        )
        
        user_id: int = dbc.get_user_id_by_email(email)['id']
        dbc.create_first_collection(user_id=user_id, last_update_date=datetime.now())
        await delete_email_verification_code(email, redis_client)
        
        return {"status": True}

    except Exception as _ex:
        print(f"[app.py->add_user] Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/complete_2fa_registration")
async def complete_2fa_registration(data: Complete2FARegistration):
    try:
        email = data.email.strip().lower()
        totp_code = data.totp_code.strip()

        user = dbc.get_user_totp_secret_by_email(email)   

        if not user or not user.get("secret"):
            return {"status": False}

        totp = pyotp.TOTP(user["secret"])
        
        if totp.verify(totp_code, valid_window=1):
            dbc.confirm_2fa(email=email)      
            return {"status": True}
        else:
            return {"status": False}

    except Exception as ex:
        print(f"[complete_2fa_registration] Error :: {ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/remove_user")  # - корректно
def remove_user(request: RemoveUserRequest):
    print(request)
    try:
        result = dbc.remove_user(user_id=request.user_id, 
                                 admin_id=request.admin_id, 
                                 comment=request.comment)
        return result
    
    except Exception as _ex:
        print(f"[app.py->remove_user]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.post("/update_user_profile")
async def update_user_profile(request: UserProfileUpdate, user_id = Depends(get_current_user_id_from_redis)):
    try:
        user_email = dbc.get_user_email_by_id(user_id)['email']
        stored_hash = dbc.get_user_password(user_email)['pswd']

        if not verify_password(stored_hash, request.current_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        update_dict = {
            "new_name": request.new_name,
            "new_email": request.new_email,
        }
        if request.new_password:
            update_dict["new_password"] = hash_password(request.new_password)  

        dbc.update_user(user_id, update_dict)
        return {"status": True}
    
    except Exception as _ex:
        print(f"[app.py->update_user_profile]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

@app.post("/login_user")
async def login_user(request: LoginUserRequest, response: Response, redis_client = Depends(get_redis)):
    try:
        db_answer = dbc.get_user_password(user_email=request.user_email)
        if not db_answer or not verify_password(db_answer["pswd"], request.user_pswd):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wrond email or password"
            )

        user_id = int(db_answer["id"])
        session_id = await create_session(user_id, redis_client)

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",         
            max_age=60 * 60 * 24,
            path="/",
        )

        return {"status": "ok"}

    except Exception as _ex:
        print(f"[app.py->login_user]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

# -----------------
@app.get("/get_user_info")
async def get_user_info(request: Request, redis_client = Depends(get_redis)):
    try:
        session_id: str | None = request.cookies.get("session_id")
            
        if not session_id:
            print(f"[app.py->get_user_info]. Error :: Session not found. {session_id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")

        key: str = f"session:{session_id}"
        session_data: dict = await redis_client.hgetall(key)

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Сессия не найдена или истекла"
            )

        user_id_bytes = session_data.get(b"user_id") or session_data.get("user_id")
        
        if not user_id_bytes:
            print(f"[app.py->get_user_info]. Error :: Session missed user_id. {user_id_bytes}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session missed user_id")

        try:
            user_id: int = int(user_id_bytes)

        except (ValueError, TypeError):
            print(f"[app.py->get_user_info]. Error :: wrong user_id format. {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="wrong user_id format"
            )

        user_data = dbc.get_user_by_id(user_id)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "user_name": user_data["name"],
            "user_email": tls.censor_text(text=user_data["email"])
        }

    except Exception as _ex:
        print(f"[app.py->get_user_info]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
# -----------------
    
@app.get("/me")
async def get_me(user_id: int = Depends(get_current_user_id_from_redis)):
    try:
        user_data = dbc.get_user_by_id(user_id)   
        if not user_data:
            print(f"[app.py->get_me]. Cant find user with id {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        return user_data
    
    except Exception as _ex:
        print(f"[app.py->get_me]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
@app.get("/check_auth")
async def check_auth(user_id: int = Depends(get_current_user_id_from_redis)):
    try:
        if user_id:
            return True
        
        return False
    
    except Exception as _ex:
        print(f"[app.py->check_auth]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    

@app.post("/logout")
async def logout(request: Request, response: Response, redis_client = Depends(get_redis)):
    try:
        session_id: str | None = request.cookies.get("session_id")
    
        if session_id:
            await delete_session(session_id, redis_client)
        
        response.delete_cookie(key="session_id", path="/", 
                            httponly=True, secure=False, samesite="lax")
        
        return JSONResponse(content={"status": True}, status_code=status.HTTP_200_OK)
    
    except Exception as _ex:
        print(f"[app.py->logout]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")

@app.post("/send_email_with_code")
async def send_email_with_code(request_body: VerificationEmailRequest, 
                               redis_client = Depends(get_redis)):
    email: str = request_body.email.strip().lower()
    
    try:
        code: str = tls.generate_verification_code()
        await create_email_verification_code(email, code, redis_client)
        success: bool = tls.send_verification_code_email(code=code, to_email=email)
        
        if success:
            print(f"[app.py->send_techsup_mail]. Successfuly sended code {code} to {email}")
            return {"status": True}
        
        else:
            print(f"[app.py->send_techsup_mail]. can't send ver. code to {email}")
            return {"status": False}
            
    except Exception as _ex:
        print(f"[app.py->send_techsup_mail]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
    
# --------------------------------------------------
#               stats logic
# --------------------------------------------------

@app.post("/get_news_stats")  
def get_news_stats(request: TechSupRequest):
    try:
        stats: dict[str, int] = tls.get_stats(info=dbc.get_news_stats())
        source_ids: dict[int, str] = dbc.get_sources()
        

    except Exception as _ex:
        print(f"[app.py->get_news_stats]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")


# --------------------------------------------------
#               techsup logic
# --------------------------------------------------

@app.post("/send_techsup_mail")  
def send_techsup_mail(request: TechSupRequest):
    try:
        to_email: str = request.user_mail
        user_name: str = request.user_name
        theme: str = request.theme
        message: str = request.message

        dbc.add_support_appeal(to_email=to_email, name=user_name, theme=theme, message_text=message)
        tls.send_tech_support_email(to_email=to_email, name=user_name, theme=theme, message_text=message)

    except Exception as _ex:
        print(f"[app.py->send_techsup_mail]. Error :: {_ex}")
        raise HTTPException(status_code=500, detail="Server error")
