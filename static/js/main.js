// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация телеграм веб-приложения
    const tg = window.Telegram.WebApp;
    if (tg) {
        tg.expand();
        
        // Стилизация под цвет темы Telegram
        if (tg.colorScheme === 'dark') {
            document.documentElement.classList.add('dark-theme');
        }
        
        // Активация кнопки Back если не на главной странице
        const isMainPage = window.location.pathname === '/';
        if (!isMainPage) {
            tg.BackButton.show();
            tg.BackButton.onClick(() => {
                window.history.back();
            });
        } else {
            tg.BackButton.hide();
        }
        
        // Подсветка активного пункта меню
        const currentPath = window.location.pathname;
        document.querySelectorAll('.nav-item').forEach(item => {
            const href = item.getAttribute('href');
            if (href === currentPath) {
                item.classList.add('active');
            }
        });
    }
    
    // Функция форматирования даты
    window.formatDate = function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    };
    
    // Функция отображения ошибок
    window.showError = function(message) {
        if (tg) {
            tg.showPopup({
                title: 'Ошибка',
                message: message,
                buttons: [{type: 'ok'}]
            });
        } else {
            alert(`Ошибка: ${message}`);
        }
    };
    
    // Функция отображения уведомлений об успехе
    window.showSuccess = function(message, callback) {
        if (tg) {
            tg.showPopup({
                title: 'Успех',
                message: message,
                buttons: [{type: 'ok'}]
            }, function() {
                if (callback && typeof callback === 'function') {
                    callback();
                }
            });
        } else {
            alert(message);
            if (callback && typeof callback === 'function') {
                callback();
            }
        }
    };
    
    // Функция подтверждения действия
    window.confirmAction = function(message, confirmCallback) {
        if (tg) {
            tg.showPopup({
                title: 'Подтверждение',
                message: message,
                buttons: [
                    {type: 'cancel', text: 'Отмена'},
                    {type: 'destructive', text: 'Подтвердить'}
                ]
            }, function(buttonId) {
                if (buttonId === 'destructive' && confirmCallback && typeof confirmCallback === 'function') {
                    confirmCallback();
                }
            });
        } else {
            if (confirm(message) && confirmCallback && typeof confirmCallback === 'function') {
                confirmCallback();
            }
        }
    };
});