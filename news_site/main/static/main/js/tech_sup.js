// обработка запроса в тех. поддержку
const supportForm = document.getElementById('supportForm');
if (supportForm) {
    supportForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = document.getElementById('submitBtn');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Отправляем...';

        const data = {
            user_name: document.getElementById('name').value.trim(),
            user_mail: document.getElementById('email').value.trim(),
            theme: document.getElementById('subject').value,
            message: document.getElementById('message').value.trim()
        };

        try {
            const response = await fetch('http://127.0.0.1:8001/send_techsup_mail', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(data),
                signal: AbortSignal.timeout(10000)
            });

            if (response.ok) {
                showToast("Запрос в тех. поддержку был отправлен!", duration=2000,);
                supportForm.reset();           
            } 
            else {
                showToast("Ошибка сервера", duration=2000, type="red");
            }
        } 
        catch (error) {
            showToast("Не удалось отправить запрос", duration=2000, type="red");
        } 
        finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
}
