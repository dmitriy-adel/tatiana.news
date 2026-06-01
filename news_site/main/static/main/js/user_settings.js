// инициализация страницы настроек
function initUserSettingsPage() {
    if (window.location.pathname.includes('/user_settings')) {        
        loadUserSettings();
        setupSaveButtonLogic();
        initPasswordModal();      
    }
}

// инициализация модального окна подтверждения пароля
function initPasswordModal() {  // обновил
    const modal = document.getElementById('settings-password-modal');
    if (!modal) return;

    const closeBtn = document.getElementById('modal-close');
    const cancelBtn = document.getElementById('modal-cancel-btn');
    const confirmBtn = document.getElementById('modal-confirm-btn');
    const passwordInput = document.getElementById('modal-current-password');
    const errorDiv = document.getElementById('modal-error');

    const closeModal = () => {
        modal.classList.add('hidden');
        if (passwordInput) passwordInput.value = '';
        if (errorDiv) errorDiv.textContent = '';
    };

    // Крестик
    if (closeBtn) closeBtn.onclick = closeModal;

    // Кнопка Отмена
    if (cancelBtn) cancelBtn.onclick = closeModal;

    // Кнопка Подтвердить
    if (confirmBtn) {
        confirmBtn.onclick = async () => {
            const currentPassword = passwordInput ? passwordInput.value.trim() : '';

            if (!currentPassword) {
                errorDiv.textContent = 'Введите текущий пароль';
                return;
            }

            if (!currentModalData) {
                errorDiv.textContent = 'Ошибка: данные не найдены';
                return;
            }

            confirmBtn.disabled = true;
            errorDiv.textContent = '';

            try {
                const payload = {
                    new_name: currentModalData.new_name,
                    new_email: currentModalData.new_email,
                    new_password: currentModalData.new_password || null,
                    current_password: currentPassword
                };

                const response = await fetch('http://127.0.0.1:8001/update_user_profile', {  // TODO тут
                    method: 'POST',
                    credentials: 'include',        
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload),
                    signal: AbortSignal.timeout(15000)
                });

                const result = await response.json().catch(() => ({}));

                if (response.ok) {
                    showToast('Профиль успешно обновлён!', 2500, "blue");
                    closeModal();
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    const errorMsg = result.detail || result.message || 'Ошибка обновления профиля';
                    errorDiv.textContent = errorMsg;
                    showToast(errorMsg, 3000, "red");
                }
            } catch (err) {
                console.error(err);
                errorDiv.textContent = 'Ошибка соединения с сервером';
                showToast('Ошибка соединения', 3000, "red");
            } finally {
                if (confirmBtn) confirmBtn.disabled = false;
            }
        };
    }

    // закрытие по клику во вне
    modal.onclick = (event) => {
        if (event.target === modal) closeModal();
    };
}

// подгрузка данных юзера и цензурирование почты
async function loadUserSettings() {
    const nameField = document.getElementById('settings-name');
    const emailField = document.getElementById('settings-email');
    if (!nameField || !emailField) return;

    try {
        const response = await fetch('http://127.0.0.1:8001/get_user_info', {
            method: 'GET',
            credentials: 'include',        
            headers: {
                'Content-Type': 'application/json'
            },
            signal: AbortSignal.timeout(10000)
        });

        if (response.ok) {
            const data = await response.json();
            nameField.value = data.user_name || '';
            emailField.value = data.user_email || '';
            showToast('Данные загружены', duration=2000, type="blue");
        } 
        else if (response.status === 401) {
            showToast('Сессия истекла. Войдите заново.', duration=2000, type="red");
        } 
        else {
            showToast('Не удалось загрузить профиль', duration=2000, type="red");
        }
    } 
    catch (err) {
        showToast('Ошибка подключения', duration=2000, type="red");
    }
}

// логика кнопки сохранения изменений
function setupSaveButtonLogic() {
    const saveBtn = document.getElementById('btn-settings-save');
    const cancelBtn = document.getElementById('btn-settings-cancel');

    if (!saveBtn || !cancelBtn) return;

    const fields = [
        'settings-name',
        'settings-email',
        'settings-new-password',
        'settings-confirm-password'
    ];

    let isChanged = false;

    const markChanged = () => {
        if (!isChanged) {
            isChanged = true;
            saveBtn.disabled = false;
            cancelBtn.disabled = false;
            cancelBtn.style.background = '#dc3545';
        }
    };

    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', markChanged);
        }
    });

    // кнопка сохранить
    saveBtn.addEventListener('click', () => {
        const name = document.getElementById('settings-name')?.value.trim() || '';
        const email = document.getElementById('settings-email')?.value.trim() || '';
        let newPassword = document.getElementById('settings-new-password')?.value.trim() || '';
        const confirmPassword = document.getElementById('settings-confirm-password')?.value.trim() || '';

        // проверка совпадения новых паролей
        if (newPassword && newPassword !== confirmPassword) {
            showToast('Новые пароли не совпадают', 3000, "red");
            return;
        }

        if (!newPassword) newPassword = null;
        currentModalData = {
            new_name: name,
            new_email: email,
            new_password: newPassword
        };

        const modal = document.getElementById('settings-password-modal');
        if (modal) {
            modal.classList.remove('hidden');
            // Фокус на поле пароля
            setTimeout(() => {
                document.getElementById('modal-current-password')?.focus();
            }, 100);
        }
    });

    // кнопка отменить
    cancelBtn.addEventListener('click', () => {
        if (confirm('Отменить все изменения и перезагрузить страницу?')) {
            window.location.reload();
        }
    });
}

// прослушка
document.addEventListener('DOMContentLoaded', function() {
    initUserSettingsPage();
});
