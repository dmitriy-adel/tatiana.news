from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any


class SearchNewsRequest(BaseModel):
    search_string: Optional[str] = None
    # filters: Optional[Dict[str, Any]] = None
    search_period: Optional[int] = 3

class SearchNewsBysourceIdRequest(BaseModel):
    source_id: int = 1

class AddNewsRequest(BaseModel):
    user_id: int
    search_string: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    current_news_max_pos: Optional[int] = None
    
class RemoveNewsRequest(BaseModel):
    user_id: int
    search_string: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    current_news_max_pos: Optional[int] = None
    
class UpdateNewsRequest(BaseModel):
    user_id: int
    search_string: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    current_news_max_pos: Optional[int] = None

class GetNewsInfoRequest(BaseModel):
    news_id: int


class CreateCollectionRequest(BaseModel):
    news_collection_name: str
    news_collection_description: str

class UpdateCollectionRequest(BaseModel):
    news_collection_id: int
    new_news_collection_name: str 
    new_news_collection_description: str 

class RemoveCollectionRequest(BaseModel):
    user_id: int
    news_collection_id: int

class AddNewsInCollectionRequest(BaseModel):
    news_collection_ids: list[int]
    news_id: int

class RemoveNewsInCollectionRequest(BaseModel):
    user_id: int
    news_collection_id: int
    news_id: int

class AddUserRequest(BaseModel):
    user_name: str
    user_email: str
    user_pswd: str
    verification_code: str

class RemoveUserRequest(BaseModel):
    user_id: int
    admin_id: int
    comment: str

class UpdateUserRequest(BaseModel):
    user_id: int
    new_user_name: Optional[str] = None
    new_user_email: Optional[str] = None
    new_user_pswd: Optional[str] = None


class TechSupRequest(BaseModel):
    user_name: str
    user_mail: str
    message: str
    theme: str

class LoginUserRequest(BaseModel):
    user_email: str
    user_pswd: str

class UserProfileUpdate(BaseModel):
    new_name: str
    new_email: str
    new_password: str | None = None
    current_password: str

class VerificationEmailRequest(BaseModel):
    email: EmailStr
  
class RemoveNewsCollectionRequest(BaseModel):
    collection_id: int

class ChangeCollectionsFillRequest(BaseModel):
    to_add: list[int]          
    to_remove: list[int]       
    news_id: int

class GetCollectionNewsRequest(BaseModel):
    collection_id: int

class GetNewsCommentsRequest(BaseModel):
    news_id: int
    last_comment_id: Optional[int] = None
    limit: int

class LikeDislikeRequest(BaseModel):
    comment_id: int

class AddUserCommentRequest(BaseModel):
    news_id: int
    comment_text: str
    replied_at_id: Optional[int] = None

class Complete2FARegistration(BaseModel):
    email: str
    totp_code: str
