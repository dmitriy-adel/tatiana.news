let lastLoadedCommentId = null;   // для пагинации
let isLoadingComments = false;

// инициализация буферной страницы и получение id текущей новости
function initNewsBufferPage() {
    const saveBtn = document.getElementById('save-news-button');
    if (!saveBtn) return;

    // Получаем ID новости из URL (/news/123/)
    const pathParts = window.location.pathname.split('/');
    currentNewsId = pathParts[pathParts.length - 2];

    const dropdown = document.getElementById('collections-dropdown');

    saveBtn.addEventListener('click', async function(e) {
        e.stopPropagation(); 
        dropdown.classList.toggle('active');

        if (dropdown.classList.contains('active')) {
            await loadUserCollections();
        }
    });

    // закрытие при клике вне
    document.addEventListener('click', function(e) {
        if (!saveBtn.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('active');
            selectedCollections.clear();
        }
    });

    // закрытие по крестику
    document.getElementById('dropdown-close').addEventListener('click', () => {
        dropdown.classList.remove('active');
        selectedCollections.clear();
    });

    initCreateCollectionModal();
    initComments();
}

// отрисовка списка коллекций в дропдауне
function renderCollections(collections) {
    const listContainer = document.getElementById('collections-list');
    listContainer.innerHTML = '';

    if (collections.length === 0) {
        listContainer.innerHTML = '<div class="no-collections">У вас пока нет коллекций</div>';
        initialCollections.clear();
        selectedCollections.clear();
        updateSaveButtonState();
        return;
    }

    initialCollections.clear();
    selectedCollections.clear();

    collections.forEach(coll => {
        const collectionId = parseInt(coll.collection_id);

        const newsId = Number(currentNewsId);
        const isInitiallyInCollection = Array.isArray(coll.collection_news_ids) 
            && coll.collection_news_ids.some(id => Number(id) === newsId);

        if (isInitiallyInCollection) {
            initialCollections.add(collectionId);
            selectedCollections.add(collectionId); 
        }

        const item = document.createElement('div');
        item.className = 'collection-item';

        item.innerHTML = `
            <div class="collection-content">
                <label class="collection-label">
                    <input type="checkbox" class="collection-checkbox" 
                        data-collection-id="${collectionId}"
                        ${isInitiallyInCollection ? 'checked' : ''}>
                    <div class="collection-info">
                        <div class="collection-name">${coll.collection_name}</div>
                        ${coll.collection_comment ? `<div class="collection-comment">${coll.collection_comment}</div>` : ''}
                        <div class="collection-meta">${coll.collection_total_news} новостей</div>
                    </div>
                </label>

                <button class="delete-collection-btn" 
                        data-collection-id="${collectionId}"
                        title="Удалить коллекцию">
                    🗑
                </button>
            </div>
        `;

        const deleteBtn = item.querySelector('.delete-collection-btn');
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm('Удалить коллекцию?')) return;

            try {
                const response = await fetch('http://127.0.0.1:8001/remove_news_collection', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ collection_id: collectionId })
                });

                if (!response.ok) throw new Error('Ошибка удаления');

                initialCollections.delete(collectionId);
                selectedCollections.delete(collectionId);

                await loadUserCollections();
            } catch (err) {
                showToast(message='Ошибка сервера', duration=2000, type='red');
            }
        });

        const checkbox = item.querySelector('.collection-checkbox');
        checkbox.addEventListener('change', function() {
            const id = parseInt(this.dataset.collectionId);

            if (this.checked) {
                selectedCollections.add(id);
            } else {
                selectedCollections.delete(id);
            }

            updateSaveButtonState();
        });

        listContainer.appendChild(item);
    });

    updateSaveButtonState();
}

function updateSaveButtonState() {
    const saveBtn = document.getElementById('save-selected-btn');
    if (!saveBtn) return;

    const hasChanges = hasAnyChanges();
    saveBtn.disabled = !hasChanges;
}

function hasAnyChanges() {
    if (selectedCollections.size !== initialCollections.size) {
        return true;
    }
    
    for (let id of selectedCollections) {
        if (!initialCollections.has(id)) {
            return true;
        }
    }

    for (let id of initialCollections) {
        if (!selectedCollections.has(id)) {
            return true;
        }
    }

    return false; 
}

function initCreateCollectionModal() {
    const openBtn = document.getElementById('new-collection-btn');
    const modal = document.getElementById('create-collection-modal');

    const closeBtn = document.getElementById('create-modal-close');
    const cancelBtn = document.getElementById('create-collection-cancel');
    const confirmBtn = document.getElementById('create-collection-confirm');

    const nameInput = document.getElementById('collection-name');
    const descInput = document.getElementById('collection-description');
    const errorBlock = document.getElementById('create-collection-error');

    if (!openBtn || !modal) return;

    const dropdownClose = document.getElementById('dropdown-close');
    openBtn.addEventListener('click', () => {
        if (dropdownClose) {
            dropdownClose.click(); 
        }
        modal.classList.remove('hidden');

        errorBlock.textContent = '';
        nameInput.value = '';
        descInput.value = '';
    });

    const closeModal = () => modal.classList.add('hidden');

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    confirmBtn.addEventListener('click', async () => {
        const name = nameInput.value.trim();
        const description = descInput.value.trim();

        if (!name) {
            errorBlock.textContent = 'Введите название коллекции';
            nameInput.classList.add('error');
            return;
        }

        nameInput.classList.remove('error');

        const payload = {
            news_collection_name: name,
            news_collection_description: description
        };

        try {
            const response = await fetch('http://127.0.0.1:8001/create_news_collection', {
                method: 'POST',
                credentials: 'include', 
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload),
                signal: AbortSignal.timeout(15000)
            });

            if (!response.ok) {
                showToast(message="Ошибка сервера", duration=2000, type='red')
            }

            closeModal();

            if (typeof loadCollections === 'function') {
                loadCollections();
            }

        } catch (err) {
            showToast(message='Ошибка сервера', duration=2000, type='red');
            errorBlock.textContent = 'Не удалось создать коллекцию';
        }
    });
}

async function loadUserCollections() {
    const listContainer = document.getElementById('collections-list');

    if (!currentUser) {
        listContainer.innerHTML = '<div class="auth-hint">Авторизуйтесь, чтобы получить доступ к коллекциям</div>';;
    }
    else {
        const listContainer = document.getElementById('collections-list');
        listContainer.innerHTML = '<div class="loading">Загрузка коллекций...</div>';

        try {
            const response = await fetch('http://127.0.0.1:8001/get_user_news_collections', {
                method: 'GET',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                signal: AbortSignal.timeout(10000)
            });

            if (!response.ok) throw new Error('Ошибка сервера');

            const collections = await response.json();
            renderCollections(collections);

        } catch (error) {
            showToast(message='Ошибка сервера', duration=2000, type='red')
            listContainer.innerHTML = '<div class="error">Не удалось загрузить коллекции</div>';
        }
    }
}

function getChangesForSave() {
    const toAdd = [];
    const toRemove = [];

    for (let id of selectedCollections) {
        if (!initialCollections.has(id)) {
            toAdd.push(id);
        }
    }

    for (let id of initialCollections) {
        if (!selectedCollections.has(id)) {
            toRemove.push(id);
        }
    }

    return { toAdd, toRemove };
}

// сохранение новости в выбранные коллекции
document.addEventListener('click', async function(e) {
    if (e.target.id !== 'save-selected-btn') return;

    const changes = getChangesForSave();

    // Если ничего не изменилось — просто закрываем
    if (changes.toAdd.length === 0 && changes.toRemove.length === 0) {
        document.getElementById('collections-dropdown').classList.remove('active');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8001/change_collections_fill', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                to_add: changes.toAdd,      
                to_remove: changes.toRemove, 
                news_id: parseInt(currentNewsId)
            })
        });

        if (!response.ok) {
            throw new Error('Ошибка при сохранении');
        }

        showToast('Изменения сохранены', 2000, 'blue');

        initialCollections = new Set(selectedCollections);

        document.getElementById('collections-dropdown').classList.remove('active');
        await loadUserCollections();

    } catch (err) {
        showToast(message='Ошибка сервера', duration=2000, type='red')
    }
});

function initComments() {
    const pathParts = window.location.pathname.split('/');
    currentNewsId = pathParts[pathParts.length - 2];

    const commentInput = document.getElementById('new-comment-input');
    const sendBtn = document.getElementById('send-comment-btn');
    const loadMoreBtn = document.createElement('button');
    loadMoreBtn.id = 'load-more-comments';
    loadMoreBtn.className = 'new_buffer_load-more-btn';
    loadMoreBtn.textContent = 'Загрузить ещё';
    loadMoreBtn.style.display = 'none';
    document.getElementById('comments-list').after(loadMoreBtn);

    if (!commentInput || !sendBtn) return;

    // Поведение плейсхолдера
    commentInput.addEventListener('focus', () => {
        if (commentInput.value === '') commentInput.placeholder = '';
    });
    commentInput.addEventListener('blur', () => {
        if (commentInput.value === '') commentInput.placeholder = 'Ваш комментарий...';
    });

    commentInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendComment();
    });

    sendBtn.addEventListener('click', sendComment);
    loadMoreBtn.addEventListener('click', loadMoreComments);

    // Первая загрузка
    loadComments();
}

async function loadComments(append = false) {
    if (isLoadingComments || !currentNewsId) return;
    isLoadingComments = true;

    const container = document.getElementById('comments-list');
    const loadMoreBtn = document.getElementById('load-more-comments');

    if (!append) {
        container.innerHTML = '<div class="loading">Загрузка комментариев...</div>';
        lastLoadedCommentId = null;
    }

    try {
        const payload = {
            news_id: parseInt(currentNewsId),
            limit: 15
        };

        if (lastLoadedCommentId !== null) {
            payload.last_comment_id = lastLoadedCommentId;
        }

        const response = await fetch('http://127.0.0.1:8001/get_news_comments', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Ошибка загрузки комментариев');

        const data = await response.json();
        const comments = data.comments || [];

        if (comments.length === 0 && !append) {
            container.innerHTML = '<div class="no-comments">Пока нет комментариев. Будьте первым!</div>';
            loadMoreBtn.style.display = 'none';
            return;
        }

        renderComments(comments, append);

        if (comments.length > 0) {
            lastLoadedCommentId = comments[comments.length - 1].id;
        }

        loadMoreBtn.style.display = data.has_more ? 'block' : 'none';

    } catch (err) {
        console.error(err);
        if (!append) {
            container.innerHTML = '<div class="error">Не удалось загрузить комментарии</div>';
        }
    } finally {
        isLoadingComments = false;
    }
}

function renderComments(comments, append = false) {
    const container = document.getElementById('comments-list');

    if (!append) {
        container.innerHTML = '';
    }

    comments.forEach(comment => {
        const commentEl = createCommentElement(comment);
        container.appendChild(commentEl);
    });
}

function createCommentElement(comment) {
    const div = document.createElement('div');
    div.className = 'comment-item';
    div.innerHTML = `
        <div class="comment-header">
            <div class="comment-user">${escapeHtml(comment.user_name)}</div>
            <div class="comment-date">${formatDate(comment.created_at)}</div>
        </div>
        <div class="comment-text">${escapeHtml(comment.comment_text)}</div>
        
        <div class="comment-actions">
            <div class="comment-action like-btn" data-comment-id="${comment.id}">
                ❤️ <span class="like-count">${comment.likes}</span>
            </div>
            <div class="comment-action dislike-btn" data-comment-id="${comment.id}">
                👎 <span class="dislike-count">${comment.dislikes}</span>
            </div>
            <div class="comment-reply">
                ↩️ Ответить
            </div>
        </div>
    `;

    // Лайк и дизлайк
    div.querySelector('.like-btn').addEventListener('click', function() {
        addReaction(this.dataset.commentId, 'like');
    });

    div.querySelector('.dislike-btn').addEventListener('click', function() {
        addReaction(this.dataset.commentId, 'dislike');
    });

    return div;
}

async function loadMoreComments() {
    await loadComments(true);
}

async function sendComment() {
    const input = document.getElementById('new-comment-input');
    const sendBtn = document.getElementById('send-comment-btn');
    const text = input.value.trim();

    if (!text || !currentNewsId) return;

    sendBtn.disabled = true;
    sendBtn.textContent = 'Отправка...';

    try {
        const response = await fetch('http://127.0.0.1:8001/add_user_comment', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                news_id: parseInt(currentNewsId),
                comment_text: text
            })
        });

        if (!response.ok) throw new Error();

        input.value = '';

        // После добавления нового комментария — перезагружаем с начала
        lastLoadedCommentId = null;
        await loadComments(false);

    } catch (err) {
        alert('Не удалось отправить комментарий');
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Отправить';
    }
}

async function addReaction(commentId, type) {
    if (!commentId) return;

    const url = type === 'like' 
        ? 'http://127.0.0.1:8001/add_like' 
        : 'http://127.0.0.1:8001/add_dislike';

    try {
        await fetch(url, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comment_id: parseInt(commentId) })
        });

        // После реакции обновляем весь список (можно оптимизировать позже)
        await loadComments(false);

    } catch (err) {
        console.error('Ошибка реакции:', err);
    }
}

// Вспомогательные функции
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
    });
}