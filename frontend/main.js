/* main.js - общие функции для всех страниц 
 * Тут всякие вспомогательные штуки типа мобильного меню и инфе о Туринской шкале
 */

// Переключение мобильного меню
function toggleMobileMenu() {
    const navLinks = document.getElementById('nav-links');
    if (navLinks) {
        navLinks.classList.toggle('active');
    }
}

// Панель мобильных фильтров
function toggleMobileFilters() {
    const panel = document.getElementById('mobile-filters-panel');
    const icon = document.getElementById('filter-toggle-icon');
    if (panel && icon) {
        panel.classList.toggle('active');
        icon.textContent = panel.classList.contains('active') ? '▲' : '▼';
    }
}

// Показываем информацию о Туринской шкале при клике на уровень
function showTorinoInfo(level) {
    const descriptions = [
        'Нет риска. Вероятность столкновения практически нулевая.',
        'Нормальный уровень. Вероятность очень низкая.',
        'Требует внимания. Вероятность 1% или выше.',
        'Угроза столкновения. Может вызвать локальные разрушения.',
        'Высокая угроза. Может вызвать региональные разрушения.',
        'Серьёзная угроза с серьёзными региональными последствиями.',
        'Угроза глобальной катастрофы.',
        'Очень высокая угроза глобальных последствий.',
        'Неизбежная катастрофа с локальными разрушениями.',
        'Глобальная катастрофа. Климатические изменения.',
        'Глобальная коллизия. Массовое вымирание видов.'
    ];

    alert(`Туринская шкала: Уровень ${level}\n\n${descriptions[level] || 'Нет данных'}`);
}

// Плавный скролл для якорных ссылок
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            // Закрываем мобильное меню если открыто
            const navLinks = document.getElementById('nav-links');
            if (navLinks) {
                navLinks.classList.remove('active');
            }
        });
    });
});
