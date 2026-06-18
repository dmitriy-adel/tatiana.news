// ====================== Категории новостей ======================

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
            showToast("Ошибка сервера", 2000, "red");
        } else {
            const classesDict = await response.json();
            allNewsClasses = Object.entries(classesDict);

            currentCategoryIndex = 0;
            updateItemsPerPage();
            renderVisibleCategories();
        }

    } catch (error) {
        container.innerHTML = `<div class="loading-text">Не удалось загрузить категории. Обновите страницу через несколько секунд</div>`;
    }
}

function updateItemsPerPage() {
    const container = document.getElementById('categoriesContainer');
    if (!container) return;

    const sidebar = document.querySelector('.tabs');
    const sidebarWidth = sidebar ? sidebar.offsetWidth : 240;

    let availableWidth = window.innerWidth - sidebarWidth - 180;

    if (availableWidth < 300) {
        availableWidth = container.clientWidth || window.innerWidth * 0.65;
    }

    const pillWidth = getCurrentPillWidth();
    const gap = 12;

    const effectiveWidthPerItem = pillWidth + 38; 

    itemsPerPage = Math.max(2, Math.floor(availableWidth / effectiveWidthPerItem));

    console.log('%c[ДИНАМИКА] itemsPerPage', 'color:#0af',
        `${itemsPerPage} | available=${Math.round(availableWidth)}px | effectiveItem=${effectiveWidthPerItem}px`);
}

function renderVisibleCategories() {
    const container = document.getElementById('categoriesContainer');
    if (!container) return;

    container.innerHTML = '';

    const end = Math.min(currentCategoryIndex + itemsPerPage, allNewsClasses.length);
    const visible = allNewsClasses.slice(currentCategoryIndex, end);

    visible.forEach(([classId, className]) => {
        const pill = document.createElement('div');
        pill.className = 'category-pill';
        pill.textContent = className;
        pill.dataset.id = classId;

        pill.addEventListener('click', () => {
            const url = `http://127.0.0.1:8000/search/?source_id=${encodeURIComponent(classId)}`;
            window.open(url, '_blank');
        });

        container.appendChild(pill);
    });

    updateScrollButtons();
}

function scrollCategories(direction) {
    const container = document.getElementById('categoriesContainer');
    if (!container) return;

    const firstPill = container.querySelector('.category-pill');
    if (!firstPill) return;

    const scrollAmount = firstPill.offsetWidth + 12;

    container.scrollBy({
        left: direction * scrollAmount,
        behavior: 'smooth'
    });

    setTimeout(updateScrollButtons, 350);
}

function updateScrollButtons() {
    const container = document.getElementById('categoriesContainer');
    const leftBtn = document.getElementById('scrollLeftBtn');
    const rightBtn = document.getElementById('scrollRightBtn');

    if (!container || !leftBtn || !rightBtn) return;

    const scrollLeft = Math.round(container.scrollLeft);
    const maxScroll = Math.round(container.scrollWidth - container.clientWidth);

    const hasOverflow = maxScroll > 30;

    if (!hasOverflow) {
        leftBtn.classList.remove('visible');
        rightBtn.classList.remove('visible');
        return;
    }

    leftBtn.classList.add('visible');
    rightBtn.classList.add('visible');

    leftBtn.style.opacity = (scrollLeft <= 8) ? '0.35' : '1';
    rightBtn.style.opacity = (scrollLeft >= maxScroll - 8) ? '0.35' : '1';
}

function getCurrentPillWidth() {
    const w = window.innerWidth;
    if (w < 480)  return 100;
    if (w < 768)  return 120;
    if (w < 1200) return 145;
    return 160;
}

let resizeTimeout;
window.addEventListener('resize', () => {
    if (allNewsClasses.length === 0) return;

    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                console.log('%c[DEBUG] RESIZE start', 'color:#fa0', 
                    `window=${window.innerWidth}px | currentIndex=${currentCategoryIndex} | itemsPerPage=${itemsPerPage}`);

                const firstVisibleId = allNewsClasses[currentCategoryIndex]?.[0];
                const oldItemsPerPage = itemsPerPage;

                updateItemsPerPage();

                console.log('%c[DEBUG] after updateItemsPerPage', 'color:#fa0',
                    `old=${oldItemsPerPage} → new=${itemsPerPage}`);

                if (itemsPerPage < oldItemsPerPage) {
                    currentCategoryIndex = Math.max(0, currentCategoryIndex - (oldItemsPerPage - itemsPerPage));
                    console.log('%c[DEBUG] уменьшили currentCategoryIndex из-за сжатия', 'color:#0f0', currentCategoryIndex);
                }

                if (firstVisibleId) {
                    const idx = allNewsClasses.findIndex(([id]) => id === firstVisibleId);
                    if (idx !== -1) {
                        currentCategoryIndex = Math.max(0, idx - (itemsPerPage - 1));
                    }
                }

                currentCategoryIndex = Math.min(
                    currentCategoryIndex,
                    Math.max(0, allNewsClasses.length - itemsPerPage)
                );

                console.log('%c[DEBUG] final currentCategoryIndex', 'color:#0af', currentCategoryIndex);

                renderVisibleCategories();

                const rendered = document.querySelectorAll('#categoriesContainer .category-pill').length;
                console.log('%c[DEBUG] ОТРИСОВАНО В DOM:', 'color:#f0f; font-weight:bold', rendered);
            });
        });
    }, 80);
});


// !!====================== Категории новостей ======================!!

// ====================== Блоки новостей ======================

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

function createNewsSection(className, newsArray) {
    const section = document.createElement('div');
    section.className = 'news-section';

    section.innerHTML = `
        <h2 class="section-title">${className}</h2>
        <div class="news-grid">
            <div class="left-column"></div>
            
            <div class="right-column"></div>
        </div>
    `;

    const leftColumn = section.querySelector('.left-column');
    const rightColumn = section.querySelector('.right-column');

    for (let i = 0; i < Math.min(2, newsArray.length); i++) {
        leftColumn.appendChild(createBigNewsCard(newsArray[i]));
    }

    for (let i = 2; i < newsArray.length; i++) {
        rightColumn.appendChild(createSmallNewsItem(newsArray[i]));
    }

    return section;
}

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
        openNews(news.id);  
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

    if (document.getElementById('newsFeed')) { 
        loadMainNewsFeed();
    }

});
