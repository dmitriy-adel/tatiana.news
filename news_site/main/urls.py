from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main'),
    path('collections/', views.collections, name='collections'),
    path('tech_sup/', views.tech_sup, name='tech_sup'),
    path('user_agreement/', views.user_agreement, name='user_agreement'),
    path('user_settings/', views.user_settings, name='user_settings'),
    path('stats/', views.stats, name='stats'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
]

path('get_tech_sup_appeal/', views.get_tech_sup_appeal, name='get_tech_sup_appeal'),
