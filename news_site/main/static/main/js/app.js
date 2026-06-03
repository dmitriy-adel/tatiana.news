// ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================

let currentUser = null;
let codeInputsInitialized = false;
let currentModalData = null;  

let selectedCollectionId = null;
let currentEditingCollection = null;

const SEARCH_KEY = 'search_history'; // история поиска
const MAX_HISTORY = 4;

const searchInput = document.getElementById('searchInput');
const dropdown = document.getElementById('searchHistoryDropdown');
const searchWrapper = document.getElementById('searchWrapper');

let currentNewsId = null;  // добавление новости в коллекцию
let selectedCollections = new Set();
let initialCollections = new Set();   

let currentSetupEmail = null;  // для генерации кода аутентификации

let allNewsClasses = [];          // для категорий на главной странице
let currentCategoryIndex = 0;
let itemsPerPage = 6;

// !!==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================!!

// ====================== НАВИГАЦИЯ ======================

// Здесь просто переадресация по страницам
function goHome() { window.location.href = '/'; }
function goCollections() { window.location.href = '/collections'; }
function goStats() { window.location.href = '/stats'; }
function goSupport() { window.location.href = '/tech_sup'; }
function goAgreement() { window.location.href = '/user_agreement'; }
function goToSettings() {window.location.href = '/user_settings';}

// !!====================== НАВИГАЦИЯ ======================!!

// ==================== АВТОРИЗАЦИЯ ====================

/*validateAndSendLogin*/ 
// валидация данных и отправка запроса на логин
async function validateAndLogin() {
    const emailField = document.getElementById('login_email');
    const passField = document.getElementById('login_password');

    // сброс ошибок
    [emailField, passField].forEach(field => field.classList.remove('error'));

    if (!emailField.value.trim() || !passField.value.trim()) {
        if (!emailField.value.trim()) emailField.classList.add('error');
        if (!passField.value.trim()) passField.classList.add('error');
        return;
    }

    const payload = {
        user_email: emailField.value.trim(),
        user_pswd: passField.value.trim()
    };

    try {
        const response = await fetch('http://127.0.0.1:8001/login_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'include',
            signal: AbortSignal.timeout(10000)   
        });

        if (!response.ok) {
            showToast('Неверный email или пароль', duration=2000, type="red");       
        }
        else {
            closeModal('loginModal');
            showToast('Вы успешно вошли! 👋', duration=2000,);

            await updateUIAfterLogin();
        }

    } catch (error) {
        showToast('Ошибка сервера 1', duration=2000, type="red");
    }
}

/* validateAndSend*/ 
// валидация данных и отправка запроса на регистрацию
async function validateAndRegister() {
    const nameField  = document.getElementById('reg_name');
    const emailField = document.getElementById('reg_email');
    const passField  = document.getElementById('reg_password');

    let valid = true;

    [nameField, emailField, passField].forEach(field => {
        field.classList.remove('error');
    });

    if (!nameField.value.trim())  { nameField.classList.add('error');  valid = false; }
    if (!emailField.value.trim()) { emailField.classList.add('error'); valid = false; }
    if (!passField.value.trim())  { passField.classList.add('error');  valid = false; }

    if (!valid) return;

    const payload = {
        user_name:         nameField.value.trim(),
        user_email:        emailField.value.trim().toLowerCase(),
        user_pswd:         passField.value.trim()
    };

    const email = payload.user_email;

    try {
        const codeRes = await fetch('http://127.0.0.1:8001/send_email_with_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email }),
            signal: AbortSignal.timeout(10000)
        });

        const codeData = await codeRes.json();

        if (!codeData.status) {
            showToast('Ошибка сервера', duration=2000, type="red");
        }
        else {
            showToast('Код успешно отправлен!', duration=2000);
            closeModal('registerModal');
            openVerCodeModalRegister(email, payload);
        }
    } 
    catch (error) {
        showToast('Ошибка при отправке кода подтверждения', duration=2000, type="red");
    }
}

// Выход из аккаунта
async function logout() {
    try {
        const res = await fetch('http://127.0.0.1:8001/logout', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: AbortSignal.timeout(10000)
        });

        if (!res.ok) {
            showToast('Ошибка сервера 3', duration=2000, type="red");       
        }
        else {
            currentUser = null;
            updateProfileMenu(false);
            showToast('Вы вышли из аккаунта', duration=2000,);
        }

    } catch (e) {
        showToast('Ошибка сети при выходе', duration=2000, type="red");
    }
}

// Глобальное обновление UI после логина
async function updateUIAfterLogin() {
    try {
        const response = await fetch('http://127.0.0.1:8001/me', {
            method: 'GET',
            credentials: 'include',
            signal: AbortSignal.timeout(10000)
        });

        if (!response.ok) {
            // throw new Error('Не авторизован');
            showToast("Ошибка сервера 4", duration=2000, type="red")
        }
        else {
            currentUser = await response.json();
            updateProfileMenu(true);
        }

    } catch (e) {
        currentUser = null;
        updateProfileMenu(false);
        showToast("Непредвиденная ошибка", duration=2000, type="red")
    }
}

// Обновление меню профиля
function updateProfileMenu(isLoggedIn) {
    const menu = document.getElementById('profileMenu');
    menu.innerHTML = '';

    if (isLoggedIn) {
        menu.innerHTML = `
            <div onclick="goToSettings()">Настройки</div>
            <div onclick="logout()">Выйти</div>
        `;
    } else {
        menu.innerHTML = `
            <div onclick="openLoginModal(event)">Войти</div>
            <div onclick="openRegisterModal(event)">Зарегистрироваться</div>
        `;
    }
}

/* submitVerificationCode*/
// Отправка кода на сервер в процессе регистрации пользователя 
async function submitVerCodeUserLogin() {
    const code = getVerificationCode();   
    
    if (code.length !== 4) {
        showToast('Введите все 4 цифры', 2000, 'red');
        return;
    }

    const payload = {
        ...window.currentRegPayload,
        verification_code: code
    };

    const email = payload.user_email;

    try {
        const response = await fetch('http://127.0.0.1:8001/add_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: AbortSignal.timeout(10000)
        });

        const data = await response.json();

        if (data.status === true) {
            
            if (email === 'dimablago210@gmail.com') {
                document.getElementById('verifyEmailModal').classList.add('hidden');
                open2FASetupModal(email, data.qr_code);
                return;
            }
            
            document.getElementById('verifyEmailModal').classList.add('hidden');
            showToast('Регистрация прошла успешно! 🎉', 2000);
            
            delete window.currentRegPayload;
            delete window.currentRegEmail;
            
        } else {
            showToast("Ошибка сервера 5", 2000, "red");
            document.querySelectorAll('.code-digit').forEach(input => {
                input.classList.add('error');
            });
            document.getElementById('codeError').classList.remove('hidden');
        }
    } catch (error) {
        showToast('Ошибка сервера 6', 2000, 'red');
    }
}

function initCodeInputs() {
    if (codeInputsInitialized) return;

    const container = document.getElementById('codeInputs');
    const inputs = Array.from(container.querySelectorAll('.code-digit'));

    inputs.forEach((input, index) => {
        input.addEventListener('input', () => {
            input.value = input.value.replace(/\D/g, '').slice(0, 1);

            if (input.value.length === 1 && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }

            if (isCodeComplete()) {
                setTimeout(submitVerCodeUserLogin, 50);
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && input.value === '' && index > 0) {
                inputs[index - 1].focus();
            }
        });

        input.addEventListener('paste', (e) => {
            e.preventDefault();

            let pastedText = (e.clipboardData || window.clipboardData)
                .getData('text')
                .trim();

            pastedText = pastedText.replace(/\D/g, '');
            if (pastedText.length === 0) return;

            for (let i = 0; i < inputs.length; i++) {
                if (i < pastedText.length) {
                    inputs[i].value = pastedText[i];
                } else {
                    inputs[i].value = ''; 
                }
            }

            const lastIndex = Math.min(pastedText.length, inputs.length) - 1;
            if (lastIndex >= 0) {
                inputs[lastIndex].focus();
            }

            if (isCodeComplete()) {
                setTimeout(submitVerCodeUserLogin, 50);
            }
        });
    });

    codeInputsInitialized = true;
}

// 2fa логика
function open2FASetupModal(email, qrBase64) {
    currentSetupEmail = email;
    const img = document.getElementById('qrCodeImage');
    img.src = qrBase64;                    
    
    const container = document.getElementById('totpCodeInputs');
    container.innerHTML = '';
    
    for (let i = 0; i < 6; i++) {
        const input = document.createElement('input');
        input.type = 'text';
        input.maxLength = 1;
        input.className = 'code-digit totp-digit';
        input.inputMode = 'numeric';
        input.pattern = '\\d*';
        input.autocomplete = 'one-time-code';
        input.oninput = function() {
            handleTOTPCodeInput(this);
        };
        container.appendChild(input);
    }
    
    document.getElementById('setup2FAModal').classList.remove('hidden');
    document.getElementById('verifyEmailModal').classList.add('hidden'); 
}

function handleTOTPCodeInput(currentInput) {
    const value = currentInput.value;
    if (value.length === 1 && /^\d$/.test(value)) {
        const inputs = document.querySelectorAll('.totp-digit');
        const index = Array.from(inputs).indexOf(currentInput);
        
        if (index < inputs.length - 1) {
            inputs[index + 1].focus();
        }
    }
    
}

function getTOTPCode() {
    return Array.from(document.querySelectorAll('.totp-digit'))
                .map(i => i.value)
                .join('');
}

function close2FAModal() {
    document.getElementById('setup2FAModal').classList.add('hidden');
    currentSetupEmail = null;
}

async function submit2FACode() {
    const code = getTOTPCode();
    
    if (code.length !== 6) {
        showToast('Введите все 6 цифр', 2000, 'red');
        return;
    }

    if (!currentSetupEmail) return;

    try {
        const response = await fetch('http://127.0.0.1:8001/complete_2fa_registration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: currentSetupEmail,
                totp_code: code
            }),
            signal: AbortSignal.timeout(10000)
        });

        const data = await response.json();

        if (data.status === true) {
            close2FAModal();
            showToast('Регистрация прошла успешно! 🎉 2FA включена', 2500);
            
            delete window.currentRegPayload;
            delete window.currentRegEmail;
        } else {
            document.getElementById('totpCodeError').classList.remove('hidden');
            showToast('Неверный код Google Authenticator', 2000, 'red');
            
            document.querySelectorAll('.totp-digit').forEach(input => input.value = '');
            document.querySelectorAll('.totp-digit')[0].focus();
        }
    } catch (error) {
        showToast('Ошибка сервера при проверке 2FA', 2000, 'red');
    }
}

// Прослушка для категорий новостей. Вызывает метод подгрузки классов новостей при загрузке страницы 
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    initScrollToTop();
});

// !!==================== АВТОРИЗАЦИЯ ====================!

// !!====================== НАСТРОЙКИ ПРОФИЛЯ ======================!!

// ====================== МОДАЛЬНЫЕ ОКНА ======================

// Функция для открытия окна логина пользователя 
function openLoginModal(event) {
    event.stopPropagation();
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');

    loginModal.classList.remove('hidden');
    registerModal.classList.add('hidden'); 
}

// Функция для открытия окна регистрации пользователя 
function openRegisterModal(event) {
    event.stopPropagation();
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');

    registerModal.classList.remove('hidden');
    loginModal.classList.add('hidden'); 
}

/* showVerificationModal*/
// Функция для отикрытия окна ввода кода верификации в профиле. TODO переименовать
function openVerCodeModalRegister(email, payload) {
    document.getElementById('verify_email_display').textContent = email;

    window.currentRegPayload = payload;
    window.currentRegEmail = email;

    const modal = document.getElementById('verifyEmailModal');
    modal.classList.remove('hidden');

    resetVerCodeInputsInModal();
    initCodeInputs();                    
    
    setTimeout(() => {
        document.querySelector('.code-digit').focus();
    }, 100);
}

// Универсальная функция для закрытия модалки
function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
}


// TODO поменять вызов этой функции на вызов универсального закрытия модалки
function closeVerifyModal() {
    document.getElementById('verifyEmailModal').classList.add('hidden');
    resetVerCodeInputsInModal();
}

// TODO поменять вызов этой функции на вызов универсального закрытия модалки
function closeCancelModal() {
    const modal = document.getElementById('settings-cancel-modal');
    if (!modal) return;

    modal.classList.add('hidden');
}

// !!====================== МОДАЛЬНЫЕ ОКНА ======================!!


// ====================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ======================

// Всплывающе уведомление
function showToast(message, duration = 2000, type = 'blue') {
    const toast = document.getElementById('toast');
    const toastText = document.getElementById('toast-text');

    // Сбрасываем все возможные классы цвета
    toast.classList.remove('toast-blue', 'toast-red');

    // Добавляем нужный класс
    if (type === 'red') {
        toast.classList.add('toast-red');
    } 
    else {
        toast.classList.add('toast-blue');  
    }

    toastText.textContent = message;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// проверяет, аутентифицирован ли пользователь. сейчас этот запрос отправляет при каждой смене страницы, что может нагружать бэк. подумать, надо ли перерабатывать и как можно это сделать
async function checkAuth() {
    try {
        const response = await fetch('http://127.0.0.1:8001/check_auth', {
            method: 'GET',
            credentials: 'include',
            signal: AbortSignal.timeout(10000)
        });

        if (response.ok) {
            currentUser = await response.json();
            updateProfileMenu(true);
        } 
        else {
            currentUser = null;
            updateProfileMenu(false);
        }

    } 
    catch (e) {
        currentUser = null;
        updateProfileMenu(false);
    }
}

// Собирает код верификации из отдельных окошек в одно значение
function getVerificationCode() {
    let code = '';
    document.querySelectorAll('.code-digit').forEach(input => {
        code += input.value.trim();
    });
    return code;
}

// Проверяет, заполнены ли окна для ввода кода верификации
function isCodeComplete() {
    return Array.from(document.querySelectorAll('.code-digit'))
                .every(input => input.value.length === 1);
}

/*resetCodeInputs*/
// функция обнуления ввода верификационного кода в модальное окно. TODO переименовать
function resetVerCodeInputsInModal() {
    document.querySelectorAll('.code-digit').forEach(input => {
        input.value = '';
        input.classList.remove('error');
    });
    document.getElementById('codeError').classList.add('hidden');
}

// Вроде как, показывает меню профиля (настройки, выйти)
function toggleProfileMenu() {
    const menu = document.getElementById('profileMenu');
    menu.classList.toggle('hidden');
}

// ====================== ПРОСЛУШКА ======================

// Функция для закрытия модалок при клике во вне. TODO посмотреть, есть ли еще модалки, которые можно сюда добавить 
window.addEventListener('click', function(e) {
    const profile = document.querySelector('.profile');
    const menu = document.getElementById('profileMenu');

    if (profile && !profile.contains(e.target)) {
        menu.classList.add('hidden');
    }

    ['loginModal', 'registerModal', 'settings-cancel-modal'].forEach(id => {
        const modal = document.getElementById(id);
        if (modal && !modal.classList.contains('hidden') && !modal.contains(e.target)) {
            modal.classList.add('hidden');
        }
    });
});

// Вроде как, функция для сокрытия модалки, аналогичная той, что выше. TODO сверить функции и удалить ненужную
window.addEventListener('click', function(e){
    const modals = ['loginModal','registerModal'];
    modals.forEach(id => {
        const modal = document.getElementById(id);
        if(!modal.classList.contains('hidden') && !modal.contains(e.target)) {
            modal.classList.add('hidden');
        }
    });

    const profileMenu = document.getElementById('profileMenu');
    if(!document.querySelector('.profile').contains(e.target)) {
        profileMenu.classList.add('hidden');
    }
});

// !!====================== ПРОСЛУШКА ======================!!

// ======================== НОВОЕ. НАДО РАЗБИТЬ ПО БЛОКАМ ================================

// Показывать/скрывать кнопку "Наверх" + учитывать футер
function handleScrollToTopButton() {
    const btn = document.getElementById('scrollToTopBtn');
    if (!btn) return;

    const scrollY = window.scrollY;
    const footer = document.querySelector('.footer');

    let shouldShow = scrollY > 400;

    // Если футер виден на экране — поднимаем кнопку выше
    if (footer) {
        const footerRect = footer.getBoundingClientRect();
        const isFooterVisible = footerRect.top < window.innerHeight && footerRect.bottom > 0;

        if (isFooterVisible) {
            document.body.classList.add('footer-visible');
        } else {
            document.body.classList.remove('footer-visible');
        }
    }

    if (shouldShow) {
        btn.classList.add('show');
    } else {
        btn.classList.remove('show');
    }
}

// Плавный скролл наверх
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Инициализация кнопки "Наверх"
function initScrollToTop() {
    const btn = document.getElementById('scrollToTopBtn');
    if (!btn) return;

    window.addEventListener('scroll', handleScrollToTopButton);
    window.addEventListener('resize', handleScrollToTopButton);
    btn.addEventListener('click', scrollToTop);
    setTimeout(handleScrollToTopButton, 300);
}

// ИСТОРИЯ ПОИСКА РАЗБИТЬ ПО БЛОКАМ 

function getSearchHistory() {
    return JSON.parse(localStorage.getItem(SEARCH_KEY) || '[]');
}

function saveSearchHistory(query) {
    if (!query.trim()) return;

    let history = getSearchHistory();
    // убираем дубликаты
    history = history.filter(q => q !== query);
    history.unshift(query);
    history = history.slice(0, MAX_HISTORY);

    localStorage.setItem(SEARCH_KEY, JSON.stringify(history));
}

function removeFromHistory(query) {
    let history = getSearchHistory();
    history = history.filter(q => q !== query);
    localStorage.setItem(SEARCH_KEY, JSON.stringify(history));
    renderHistory(); // перерисовываем с учётом текущего ввода
}

// Главная функция отрисовки с фильтрацией
function renderHistory(filter = '') {
    const history = getSearchHistory();
    const lowerFilter = filter.toLowerCase().trim();

    // Фильтруем: запрос должен НАЧИНАТЬСЯ с введённого текста
    let filteredHistory = history.filter(item => 
        item.toLowerCase().startsWith(lowerFilter)
    );

    if (filteredHistory.length === 0) {
        dropdown.classList.add('hidden');
        searchWrapper.classList.remove('active');
        dropdown.innerHTML = '';
        return;
    }

    dropdown.innerHTML = filteredHistory.map(item => `
        <div class="history-item">
            <div class="history-left">
                <span class="history-icon">↺</span>
                <span class="history-text">${item}</span>
            </div>
            <span class="history-remove" data-value="${item}">✕</span>
        </div>
    `).join('');

    dropdown.classList.remove('hidden');
    searchWrapper.classList.add('active');
}

// ==================== СОБЫТИЯ ====================

// Основное событие — ввод текста
searchInput.addEventListener('input', () => {
    const currentValue = searchInput.value;
    renderHistory(currentValue);
});

// Фокус на input (показываем полную историю, если ничего не введено)
searchInput.addEventListener('focus', () => {
    if (!searchInput.value.trim()) {
        renderHistory(''); // показываем всё
    }
});

// Клик по элементу истории
dropdown.addEventListener('click', (e) => {
    const item = e.target.closest('.history-item');
    if (!item) return;

    // Нажали на крестик
    if (e.target.classList.contains('history-remove')) {
        const value = e.target.dataset.value;
        removeFromHistory(value);
        return;
    }

    // Выбрали элемент
    const textEl = item.querySelector('.history-text');
    const value = textEl.textContent;

    searchInput.value = value;
    dropdown.classList.add('hidden');
    searchWrapper.classList.remove('active');

    // Можно сразу запустить поиск
    // console.log('Search:', value);
});

// Enter → сохранить в историю
searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const query = searchInput.value.trim();
        if (query) {
            saveSearchHistory(query);
            dropdown.classList.add('hidden');
            searchWrapper.classList.remove('active');

            console.log('Search performed:', query);
            // Здесь можно добавить вызов реального поиска
        }
    }
});

// Клик вне области поиска → скрыть дропдаун
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-wrapper')) {
        dropdown.classList.add('hidden');
        searchWrapper.classList.remove('active');
    }
});
