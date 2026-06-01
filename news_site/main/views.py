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