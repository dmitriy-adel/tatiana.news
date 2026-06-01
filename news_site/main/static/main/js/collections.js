// Основная функция загрузки страницы
async function loadUserCollections() {
    const container = document.getElementById('collections-container');
    container.innerHTML = '<div class="loading">Загрузка коллекций...</div>';

    if (!currentUser) {
        console.log(currentUser, 'current user')
        container.innerHTML = `
            <div class="auth-required">
                <p>Для доступа к коллекциям необходимо войти в аккаунт.</p>
                <button onclick="openLoginModal(event)" class="blue-btn">Войти</button>
            </div>
        `;
        console.warn('какой-то...');
        showToast('Требуется авторизация', 2500, 'red');
    }

    // === Дальше идёт загрузка коллекций (твой код) ===
    try {
        const response = await fetch('http://127.0.0.1:8001/get_user_news_collections', {
            method: 'GET',
            credentials: 'include',
            signal: AbortSignal.timeout(15000)
        });

        if (!response.ok) throw new Error('Ошибка сервера');

        const collections = await response.json();

        if (collections.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>У вас пока нет коллекций.</p>
                    <button onclick="createNewCollection()" class="blue-btn">Создать коллекцию</button>
                </div>
            `;
            return;
        }

        // let html = '<div class="collections-grid">';

        // collections.forEach(coll => {
        //     html += `
        //         <div class="collection-card">
        //             <div class="collection-header">
        //                 <h3 onclick="openCollection(${coll.collection_id}, '${escapeHtml(coll.collection_name)}')">
        //                     ${escapeHtml(coll.collection_name)}
        //                 </h3>
        //                 <div class="settings-btn" onclick="showCollectionMenu(event, ${coll.collection_id}, '${escapeHtml(coll.collection_name)}', '${escapeHtml(coll.collection_comment || '')}')">
        //                     ⚙️
        //                 </div>
        //             </div>
                    
        //             ${coll.collection_comment ? `<p class="comment">${escapeHtml(coll.collection_comment)}</p>` : ''}
                    
        //             <div class="collection-meta">
        //                 <span class="news-count">${coll.collection_total_news} новостей</span>
        //                 <span class="updated">Обновлено: ${coll.collection_last_updated_at}</span>
        //             </div>
        //         </div>
        //     `;
        // });

        let html = '<div class="collections-grid">';

        collections.forEach(coll => {
            html += `
                <div class="collection-card" onclick="openCollection(${coll.collection_id}, '${escapeHtml(coll.collection_name)}')">
                    <div class="collection-header">
                        <h3>${escapeHtml(coll.collection_name)}</h3>
                        <div class="settings-btn" onclick="showCollectionMenu(event, ${coll.collection_id}, '${escapeHtml(coll.collection_name)}', '${escapeHtml(coll.collection_comment || '')}')">
                            ⚙️
                        </div>
                    </div>
                    
                    ${coll.collection_comment ? `<p class="comment">${escapeHtml(coll.collection_comment)}</p>` : ''}
                    
                    <div class="collection-meta">
                        <span class="news-count">${coll.collection_total_news} новостей</span>
                        <span class="updated">Обновлено: ${coll.collection_last_updated_at}</span>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

        html += '</div>';
        container.innerHTML = html;

    } catch (err) {
        console.error(err);
        container.innerHTML = `<div class="error-state">Не удалось загрузить коллекции.<br><button onclick="loadUserCollections()" class="blue-btn">Повторить</button></div>`;
    }
}

function showCollectionMenu(e, collectionId, name, comment) {
    e.stopImmediatePropagation(); // чтобы не открывалась коллекция при клике на шестерёнку
    document.querySelectorAll('.collection-menu').forEach(m => m.remove());

    const menu = document.createElement('div');
    menu.className = 'collection-menu';
    menu.style.position = 'absolute';
    menu.style.background = 'white';
    menu.style.border = '1px solid #ccc';
    menu.style.borderRadius = '8px';
    menu.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    menu.style.padding = '8px 0';
    menu.style.zIndex = '1000';
    menu.innerHTML = `
        <div class="menu-item" onclick="editCollection(${collectionId}, '${escapeHtml(name)}', '${escapeHtml(comment)}')">Настройки</div>
        <div class="menu-item" style="color: #d32f2f;" onclick="deleteCollection(${collectionId})">Удалить</div>
    `;

    // Позиционируем меню рядом с кнопкой
    const rect = e.currentTarget.getBoundingClientRect();
    menu.style.top = `${rect.bottom + window.scrollY + 5}px`;
    menu.style.left = `${rect.left + window.scrollX - 100}px`;

    document.body.appendChild(menu);

    // Закрытие меню при клике вне его
    setTimeout(() => {
        document.addEventListener('click', function handler(ev) {
            if (!menu.contains(ev.target)) {
                menu.remove();
                document.removeEventListener('click', handler);
            }
        });
    }, 10);
}

function editCollection(collectionId, name, comment) {
    currentEditingCollection = { id: collectionId, name: name, comment: comment };

    document.getElementById('edit-collection-name').value = name;
    document.getElementById('edit-collection-description').value = comment || '';

    document.getElementById('edit-collection-error').textContent = '';
    document.getElementById('edit-collection-modal').classList.remove('hidden');
}

async function saveCollectionChanges() {
    if (!currentEditingCollection) return;

    const newName = document.getElementById('edit-collection-name').value.trim();
    const newDescription = document.getElementById('edit-collection-description').value.trim();
    const errorEl = document.getElementById('edit-collection-error');

    if (!newName) {
        errorEl.textContent = 'Название коллекции не может быть пустым';
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8001/update_news_collection', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                news_collection_id: currentEditingCollection.id,
                new_news_collection_name: newName,
                new_news_collection_description: newDescription
            }),
            signal: AbortSignal.timeout(10000)
        });

        if (!response.ok) throw new Error('Ошибка обновления');

        closeEditModal();
        showToast('Коллекция успешно обновлена');
        loadUserCollections(); // перезагружаем список

    } catch (err) {
        console.error(err);
        document.getElementById('edit-collection-error').textContent = 'Не удалось сохранить изменения';
    }
}

async function deleteCollection(collectionId) {
    if (!confirm('Вы действительно хотите удалить эту коллекцию?')) {
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8001/remove_news_collection', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ collection_id: collectionId }),
            signal: AbortSignal.timeout(10000)
        });

        if (!response.ok) throw new Error('Ошибка удаления');

        showToast('Коллекция удалена');
        loadUserCollections();

        // Если удаляем открытую коллекцию — закрываем панель
        if (selectedCollectionId === collectionId) {
            document.getElementById('collection-detail').classList.add('hidden');
        }

    } catch (err) {
        console.error(err);
        alert('Не удалось удалить коллекцию');
    }
}

function closeEditModal() {
    document.getElementById('edit-collection-modal').classList.add('hidden');
    currentEditingCollection = null;
}

function formatNewsDate(dateStr) {
    if (!dateStr) return '';

    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
        return dateStr; 
    }

    return new Intl.DateTimeFormat('ru-RU', {
        day: 'numeric',
        month: 'long',      
        year: 'numeric',
        // hour: '2-digit',
        // minute: '2-digit',
        hour12: false
    }).format(date);
}

// async function openCollection(collectionId, collectionName) {
//     selectedCollectionId = collectionId;
    
//     document.getElementById('collection-detail').classList.remove('hidden');
//     // document.getElementById('detail-collection-name').textContent = collectionName;
//     document.getElementById('detail-collection-name').textContent = `Имя коллекции: ${collectionName}`;

//     const newsContainer = document.getElementById('news-list');
//     newsContainer.innerHTML = '<div class="loading">Загрузка новостей...</div>';

//     try {
//         const response = await fetch('http://127.0.0.1:8001/get_collection_news', {
//             method: 'POST',
//             credentials: 'include',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ collection_id: collectionId }),
//             signal: AbortSignal.timeout(15000)
//         });

//         if (!response.ok) throw new Error('Ошибка загрузки новостей');

//         const news = await response.json();

//         if (news.length === 0) {
//             newsContainer.innerHTML = '<p class="empty">В коллекции пока нет новостей.</p>';
//             return;
//         }

//         let html = '';
//         news.forEach(item => {
//             const formattedDate = formatNewsDate(item.news_created_at);
//             html += `
//                 <div class="news-item" onclick="openNews(${item.news_id})">
//                     <h4>${escapeHtml(item.news_title)}</h4>
//                     <p class="news-source">${escapeHtml(item.news_source_name)} • ${formattedDate}</p>
//                     ${item.news_text ? `<p class="news-preview">${escapeHtml(item.news_text.substring(0, 150))}...</p>` : ''}
//                 </div>
//             `;
//         });

//         newsContainer.innerHTML = html;

//     } catch (error) {
//         console.error(error);
//         newsContainer.innerHTML = '<p class="error">Не удалось загрузить новости коллекции.</p>';
//     }
// }
async function openCollection(collectionId, collectionName) {
    console.log('🔥 openCollection ВЫЗВАНА!', { collectionId, collectionName }); // ← добавили для диагностики

    selectedCollectionId = collectionId;
    
    const panel = document.getElementById('collection-detail');
    panel.style.display = 'flex';

    document.getElementById('detail-collection-name').textContent = `Имя коллекции: ${collectionName}`;

    const newsContainer = document.getElementById('news-list');
    newsContainer.innerHTML = '<div class="loading">Загрузка новостей...</div>';

    try {
        const response = await fetch('http://127.0.0.1:8001/get_collection_news', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ collection_id: collectionId }),
            signal: AbortSignal.timeout(15000)
        });

        if (!response.ok) throw new Error('Ошибка загрузки новостей');

        const news = await response.json();

        if (news.length === 0) {
            newsContainer.innerHTML = '<p class="empty">В коллекции пока нет новостей.</p>';
            return;
        }

        let html = '';
        news.forEach(item => {
            const formattedDate = formatNewsDate(item.news_created_at);
            html += `
                <div class="news-item" onclick="openNews(${item.news_id})">
                    <h4>${escapeHtml(item.news_title)}</h4>
                    <p class="news-source">${escapeHtml(item.news_source_name)} • ${formattedDate}</p>
                    ${item.news_text ? `<p class="news-preview">${escapeHtml(item.news_text.substring(0, 150))}...</p>` : ''}
                </div>
            `;
        });

        newsContainer.innerHTML = html;

    } catch (error) {
        console.error(error);
        newsContainer.innerHTML = '<p class="error">Не удалось загрузить новости коллекции.</p>';
    }
}

function openNews(newsId) {
    window.location.href = `http://127.0.0.1:8000/news/${newsId}/`;
}

// function closeDetailPanel() {
//     document.getElementById('collection-detail').classList.add('hidden');
// }

function closeDetailPanel() {
    const panel = document.getElementById('collection-detail');
    panel.style.display = 'none';                    // ← только это изменили
}

// Защита от XSS
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// Создание новой коллекции (заглушка — можешь доработать)
function createNewCollection() {
    alert('Функция создания коллекции будет добавлена позже');
    // Здесь можно открыть модальное окно создания
}

document.addEventListener('DOMContentLoaded', () => {
    loadUserCollections();
});