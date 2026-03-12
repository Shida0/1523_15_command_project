// 1. ФИКСИРОВАННЫЙ МАССИВ (Демо-данные)
// Здесь я оставил несколько примеров, ты можешь добавить сюда хоть 100 объектов
const asteroids = [
    { name: "Apophis 99942", date: "2029-04-13", size: "370 м", sizeVal: 370, distance: "31 000 км", distVal: 31000, threat: "red" },
    { name: "Bennu", date: "2182-09-24", size: "490 м", sizeVal: 490, distance: "200 000 км", distVal: 200000, threat: "red" },
    { name: "2023 DZ2", date: "2026-03-27", size: "70 м", sizeVal: 70, distance: "175 000 км", distVal: 175000, threat: "yellow" },
    { name: "Duende", date: "2028-02-15", size: "30 м", sizeVal: 30, distance: "27 700 км", distVal: 27700, threat: "green" },
    { name: "Toutatis", date: "2025-12-04", size: "5400 м", sizeVal: 5400, distance: "1 500 000 км", distVal: 1500000, threat: "green" }
    // ... добавь еще астероидов для теста пагинации
];

let currentSort = 'date'; 
let threatFilter = 'all';
let visibleCount = 50; 
const step = 50;       

const searchInput = document.getElementById('asteroidSearch');
const cardsGrid = document.getElementById('cardsGrid');
const loadMoreBtn = document.getElementById('loadMoreBtn'); 

// 2. ФУНКЦИЯ ДЛЯ ДЕМО-ЗАПУСКА (Заменяет загрузку из базы)
function initDemo() {
    // Сразу обновляем счетчик на плашке
    const totalCountElement = document.getElementById('totalCount');
    if (totalCountElement) {
        totalCountElement.textContent = asteroids.length;
    }
    
    // Сразу рисуем таблицу
    renderCards(); 
}

// 3. ФУНКЦИЯ ОТРИСОВКИ (Логика сохранена)
function renderCards(filterText = "") {
    if (!cardsGrid) return;

    // Фильтрация
    let filtered = asteroids.filter(ast => {
        const matchesName = ast.name.toLowerCase().includes(filterText.toLowerCase());
        const matchesThreat = threatFilter === 'all' || ast.threat === threatFilter;
        return matchesName && matchesThreat;
    });

    // Сортировка
    filtered.sort((a, b) => {
        if (currentSort === 'date') return new Date(a.date) - new Date(b.date);
        if (currentSort === 'size') return b.sizeVal - a.sizeVal;
        if (currentSort === 'distance') return a.distVal - b.distVal;
        return 0;
    });

    // Отрисовка шапки
    cardsGrid.innerHTML = `
        <div class="asteroid-row table-header">
            <div>Астероид</div>
            <div>Дата сближения</div>
            <div>Размер (м)</div>
            <div>Расстояние</div>
            <div>Уровень угрозы</div>
        </div>
    `;

    const displayedAsteroids = filtered.slice(0, visibleCount);

    displayedAsteroids.forEach(ast => {
        const row = document.createElement('div');
        row.className = 'asteroid-row';
        row.innerHTML = `
            <div>${ast.name}</div>
            <div>${new Date(ast.date).toLocaleDateString()}</div>
            <div>${ast.size}</div>
            <div>${ast.distance}</div>
            <div><div class="risk-indicator risk-${ast.threat}"></div></div>
        `;
        cardsGrid.appendChild(row);
    });

    if (loadMoreBtn) {
        loadMoreBtn.style.display = (visibleCount < filtered.length) ? 'block' : 'none';
    }
}

// 4. ОБРАБОТЧИКИ СОБЫТИЙ (Мгновенные, без плавности)
if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', () => {
        visibleCount += step; 
        renderCards(searchInput.value); 
    });
}

document.querySelectorAll('.threat-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        threatFilter = e.currentTarget.dataset.threat;
        visibleCount = 50; 
        document.querySelectorAll('.threat-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        renderCards(searchInput.value);
    });
});

document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        currentSort = e.currentTarget.dataset.sort;
        visibleCount = 50; 
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        renderCards(searchInput.value);
    });
});

if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        visibleCount = 50; 
        renderCards(e.target.value);
    });
}

// 5. ЗАПУСК
initDemo();