from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


def main_page(request):
    return render(request, 'main/main.html')

def collections(request):
    return render(request, 'main/collections.html')

def tech_sup(request):
    return render(request, 'main/tech_sup.html')

def user_agreement(request):
    return render(request, 'main/user_agreement.html')

def user_settings(request):
    return render(request, 'main/user_settings.html')

def stats(request):
    return render(request, 'main/stats.html')

def analytics_ib(request):
    return render(request, 'main/analytics_ib.html')

@csrf_exempt
def get_tech_sup_appeal(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Получено обращение:", data)   

            return JsonResponse({'status': 'success', 'message': 'Обращение получено'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=405)


import requests
from django.shortcuts import render
from django.http import Http404

def news_detail(request, news_id):
    try:
        # Отправляем POST-запрос на твой внешний сервис
        response = requests.post(
            'http://localhost:8001/get_news_info',
            json={'news_id': news_id},      # тело запроса
            timeout=10
        )
        
        # Проверяем статус
        response.raise_for_status()
        
        data = response.json()   # предполагаем, что возвращается JSON
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        raise Http404(f"Новость с ID {news_id} не найдена или сервис недоступен")
    
    # Проверяем, что данные пришли
    if not data or 'error' in data:
        raise Http404(f"Новость с ID {news_id} не найдена")

    # Передаём данные в шаблон
    context = {
        'title': data.get('title'),
        'text': data.get('text'),
        'url': data.get('url'),
        'source_name': data.get('source_name'),
        'source_main_url': data.get('source_main_url'),   # если приходит
        'created_at': data.get('created_at') or data.get('published_at'),
        # можно добавить другие поля: key_words, tags и т.д.
    }
    
    return render(request, 'news/news_buffer.html', context)


import requests
from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import News, NewsClass


def search_view(request):
    source_id = request.GET.get('source_id', '').strip()
    category_param = request.GET.get('category', '').strip()
    search_text = request.GET.get('text', '').strip()

    # ====================== РЕЖИМ: Внешний сервис по source_id ======================
    if source_id:
        try:
            response = requests.post(
                'http://127.0.0.1:8001/get_news_by_category_id',
                json={'source_id': source_id},
                timeout=12
            )
            response.raise_for_status()
            data = response.json()

            # Поддерживаем оба формата: {"news": [...]} и просто [...]
            if isinstance(data, dict):
                external_news = data.get('news', [])
            else:
                external_news = data

            # Получаем имя для заголовка (если передаётся в GET)
            # source_name = request.GET.get('source_name', f'ID {source_id}')

            context = {
                'external_news': external_news,
                'source_id': source_id,
                # 'source_name': source_name,
                'is_external': True,
            }
            return render(request, 'search/search.html', context)

        except requests.exceptions.RequestException as e:
            context = {
                'error': f'Не удалось загрузить новости. Попробуйте позже.',
                'source_id': source_id,
                'is_external': True,
            }
            return render(request, 'search/search.html', context)

    # ====================== Обычный режим (локальная БД) ======================
    news_list = News.objects.select_related('news_class', 'source').all()

    current_class = None
    if category_param:
        current_class = NewsClass.objects.filter(name__iexact=category_param).first()
        if current_class:
            news_list = news_list.filter(news_class=current_class)

    if search_text:
        news_list = news_list.filter(
            Q(title__icontains=search_text) |
            Q(text__icontains=search_text) |
            Q(key_words__icontains=search_text)
        )

    paginator = Paginator(news_list, 12)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    context = {
        'page_obj': page_obj,
        'news_classes': NewsClass.objects.all().order_by('name'),
        'current_class': current_class,
        'search_text': search_text,
        'category_param': category_param,
        'is_external': False,
    }
    return render(request, 'search/search.html', context)