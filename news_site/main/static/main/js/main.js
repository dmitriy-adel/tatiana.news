// ====================== Категории новостей ======================

// подгрузка категорий новостей, которые крутятся в верхней части страницы
async function loadNewsClasses() {
    const container = document.getElementById('categoriesContainer');
    if (!container) return;

    try {
        const response = await fetch('http://127.0.0.1:8001/get_news_classes', {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: AbortSignal.timeout(10000)
        });

        if (!response.ok) {
            showToast("Ошибка сервера", duration=2000, type="red")
        }
        else {
            const classesDict = await response.json();
            container.innerHTML = '';

            Object.entries(classesDict).forEach(([classId, className]) => {
                const pill = document.createElement('div');
                pill.className = 'category-pill';
                pill.textContent = className;
                pill.dataset.id = classId;
                container.appendChild(pill);
            });

            updateScrollButtons();
            setTimeout(updateScrollButtons, 100);
        }

    } catch (error) {
        container.innerHTML = `<div class="loading-text">Не удалось загрузить категории. Обновите страницу через несколько секунд</div>`;
    }
}

// функция скролла категорий новостей в верхней части страницы
function scrollCategories(direction) {
    const container = document.getElementById('categoriesContainer');
    if (!container) return;

    // Прокрутка ровно на один элемент (минимальное изменение)
    const firstPill = container.querySelector('.category-pill');
    if (!firstPill) return;

    const scrollAmount = firstPill.offsetWidth + 12; // 12 = gap из CSS

    container.scrollBy({
        left: direction * scrollAmount,
        behavior: 'smooth'
    });

    setTimeout(updateScrollButtons, 350);
}

// Отображение кнопок для скорлла ленты
function updateScrollButtons() {
    const container = document.getElementById('categoriesContainer');
    const leftBtn = document.getElementById('scrollLeftBtn');
    const rightBtn = document.getElementById('scrollRightBtn');

    if (!container || !leftBtn || !rightBtn) return;

    const scrollLeft = container.scrollLeft;
    const maxScroll = container.scrollWidth - container.clientWidth;

    const hasOverflow = maxScroll > 15;   // небольшой запас

    if (!hasOverflow) {
        leftBtn.classList.remove('visible');
        rightBtn.classList.remove('visible');
        return;
    }

    leftBtn.classList.toggle('visible', scrollLeft > 10);
    rightBtn.classList.toggle('visible', scrollLeft < maxScroll - 10);
}

// !!====================== Категории новостей ======================!!

// ====================== Блоки новостей ======================

// подгружает последние новости и отображает их на главную страницу
async function loadMainNewsFeed() {
    const feedContainer = document.getElementById('newsFeed');
    if (!feedContainer) return;

    feedContainer.innerHTML = '<div class="loading-text">Загружаем новости...</div>';

    try {
        const response = await fetch('http://127.0.0.1:8001/get_last_news', {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: AbortSignal.timeout(15000)
        });

        if (!response.ok) {
            throw new Error('Server error');
        }

        const groupedNews = await response.json();
        feedContainer.innerHTML = '';

        Object.entries(groupedNews).forEach(([className, newsArray]) => {
            if (!newsArray || newsArray.length === 0) return;

            const section = createNewsSection(className, newsArray);
            feedContainer.appendChild(section);
        });

    } catch (error) {
        console.error(error);
        feedContainer.innerHTML = `
            <div class="loading-text" style="color: #f66;">
                Не удалось загрузить новости. Попробуйте обновить страницу.
            </div>`;
    }
}

//Создаёт один блок-секцию для класса новостей
function createNewsSection(className, newsArray) {
    const section = document.createElement('div');
    section.className = 'news-section';

    section.innerHTML = `
        <h2 class="section-title">${className}</h2>
        <div class="news-grid">
            <!-- Левая колонка — 2 большие карточки -->
            <div class="left-column"></div>
            
            <!-- Правая колонка — список -->
            <div class="right-column"></div>
        </div>
    `;

    const leftColumn = section.querySelector('.left-column');
    const rightColumn = section.querySelector('.right-column');

    // Первые 2 новости — большие карточки
    for (let i = 0; i < Math.min(2, newsArray.length); i++) {
        leftColumn.appendChild(createBigNewsCard(newsArray[i]));
    }

    // Остальные — в правый список (начиная с 3-й)
    for (let i = 2; i < newsArray.length; i++) {
        rightColumn.appendChild(createSmallNewsItem(newsArray[i]));
    }

    return section;
}

// карточки новостей
function createBigNewsCard(news) {
    const card = document.createElement('div');
    card.className = 'news-card big';
    card.dataset.newsId = news.id;

    card.innerHTML = `
        <div class="card-content">
            <h3 class="news-title">${news.title}</h3>
            <p class="news-text">${news.text ? news.text.substring(0, 180) + '...' : ''}</p>
            <div class="news-meta">
                <span class="source">${news.source_id || 'Источник'}</span>
                <span class="time">${formatTimeAgo(news.created_at)}</span>
            </div>
        </div>
    `;

    card.addEventListener('click', () => {
        openNews(news.id);   // ← сюда потом сделаем переход на новость
    });

    return card;
}

function createSmallNewsItem(news) {
    const item = document.createElement('div');
    item.className = 'news-item small';
    item.dataset.newsId = news.id;

    item.innerHTML = `
        <div class="item-content">
            <h4 class="news-title">${news.title}</h4>
            <div class="news-meta">
                <span class="source">${news.source_id || ''}</span>
                <span class="time">${formatTimeAgo(news.created_at)}</span>
            </div>
        </div>
    `;

    item.addEventListener('click', () => {
        openNews(news.id);
    });

    return item;
}

// октрытие новости в буферной странице
function openNews(newsId) {
    if (!newsId) {
        showToast(message='newsId не передан', direction=3000, type="red");
        return;
    } else {
        window.location.href = `/news/${newsId}/`;
    }
    
}

// форматирование времени добавления новости
function formatTimeAgo(createdAt) {
    // createdAt приходит как строка ISO или timestamp
    const date = new Date(createdAt);
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return 'только что';
    if (diffMin < 60) return `${diffMin} мин назад`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours} ч назад`;
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

// !!====================== Блоки новостей ======================!!

// ====================== Прослушка ======================

// автоматическая подгрузка всей инфы по новосятм
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('categoriesContainer')) {
        loadNewsClasses();

        const leftBtn  = document.getElementById('scrollLeftBtn');
        const rightBtn = document.getElementById('scrollRightBtn');

        if (leftBtn)  leftBtn.addEventListener('click', () => scrollCategories(-1));
        if (rightBtn) rightBtn.addEventListener('click', () => scrollCategories(1));

        const container = document.getElementById('categoriesContainer');
        if (container) {
            container.addEventListener('scroll', updateScrollButtons);
            window.addEventListener('resize', updateScrollButtons);
        }
    }

    if (document.getElementById('newsFeed')) { // НОВОЕ
        loadMainNewsFeed();
    }

});

// !!====================== Прослушка ======================!!
