/* asteroids.js - скрипты страницы каталога астероидов */

let allAsteroids = [];
let filteredAsteroids = [];
let currentSort = { field: 'designation', order: 'asc' };
let activeFilters = {
    risk: 'all',
    diameter: null,
    orbit: null
};

// Пагинация - по 50 штук на страницу
const ITEMS_PER_PAGE = 50;
let currentPage = 1;
let totalPages = 1;
let totalAsteroids = 0;

async function loadAsteroids() {
    try {
        const countData = await api.getAsteroidsCount();
        totalAsteroids = countData.total;

        allAsteroids = await api.getAllAsteroids(0, 10000);
        filteredAsteroids = [...allAsteroids];
        sortAsteroids();
        updatePagination();
        renderTable();
    } catch (error) {
        console.error('Ошибка загрузки астероидов:', error);
        showTableError('Не удалось загрузить данные. Проверьте подключение к интернету или обратитесь к администратору.');
    }
}

function renderTable() {
    const tbody = document.getElementById('asteroids-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (filteredAsteroids.length === 0) {
        showTableError('Астероиды не найдены по заданным критериям. Попробуйте сбросить фильтры или выбрать другие параметры поиска.');
        return;
    }

    // Вычисляем индексы для текущей страницы
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const pageAsteroids = filteredAsteroids.slice(startIndex, endIndex);

    pageAsteroids.forEach(asteroid => {
        const riskClass = getRiskClass(asteroid.threat_assessment?.ts_max || 0);
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><a href="../asteroid_detail/asteroid_detail.html?name=${encodeURIComponent(asteroid.designation)}" class="asteroid-link">${asteroid.designation}</a></td>
            <td>${asteroid.name ? `<a href="../asteroid_detail/asteroid_detail.html?name=${encodeURIComponent(asteroid.designation)}" class="asteroid-link">${asteroid.name}</a>` : '—'}</td>
            <td>${asteroid.estimated_diameter_km.toFixed(3)}</td>
            <td>${asteroid.perihelion_au ? asteroid.perihelion_au.toFixed(4) : '—'}</td>
            <td>${asteroid.aphelion_au ? asteroid.aphelion_au.toFixed(4) : '—'}</td>
            <td>${asteroid.earth_moid_au.toFixed(4)}</td>
            <td>${asteroid.absolute_magnitude.toFixed(2)}</td>
            <td>${asteroid.albedo ? asteroid.albedo.toFixed(3) : '—'}</td>
            <td><span class="orbit-class">${asteroid.orbit_class}</span></td>
            <td><span class="risk-badge ${riskClass}">${getThreatLevelRu(asteroid.threat_assessment?.ts_max || 0)}</span></td>
        `;
        tbody.appendChild(row);
    });

    updateResultsCount();
    renderPagination();
}

// Обновляем счётчики результатов
const updateResultsCount = () => {
    const totalResults = document.getElementById('total-results');
    const totalCount = document.getElementById('total-count');
    const filteredCount = document.getElementById('filtered-count');

    if (totalResults) totalResults.textContent = filteredAsteroids.length;
    if (totalCount) totalCount.textContent = totalAsteroids;
    if (filteredCount) filteredCount.textContent = filteredAsteroids.length;
};

// фильтры
function applyFilters() {
    let filtered = [...allAsteroids];

    if (activeFilters.risk === 'high') {
        filtered = filtered.filter(a => (a.threat_assessment?.ts_max || 0) >= 2);
    } else if (activeFilters.risk === 'near-earth') {
        filtered = filtered.filter(a => a.earth_moid_au <= 0.05);
    }

    if (activeFilters.diameter === 'nasa') {
        filtered = filtered.filter(a => a.accurate_diameter === true);
    } else if (activeFilters.diameter === 'calculated') {
        filtered = filtered.filter(a => a.accurate_diameter === false);
    }

    if (activeFilters.orbit) {
        filtered = filtered.filter(a => a.orbit_class && a.orbit_class.toLowerCase() === activeFilters.orbit.toLowerCase());
    }

    filteredAsteroids = filtered;
    currentPage = 1; // Сброс на первую страницу при фильтрации
    sortAsteroids();
    updatePagination();
    renderTable();
}

function filterByRisk(risk) {
    document.querySelectorAll('.filter-group:nth-child(1) .filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    activeFilters.risk = risk;
    applyFilters();
}

function filterByDiameter(diameter) {
    document.querySelectorAll('.filter-group:nth-child(2) .filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    activeFilters.diameter = diameter;
    applyFilters();
}

// Быстрый фильтр по классу орбиты
function quickFilter(orbit) {
    document.querySelectorAll('.quick-filters .quick-filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    activeFilters.orbit = orbit === 'all' ? null : orbit;
    applyFilters();
}

function sortTable(field) {
    const buttons = document.querySelectorAll('.filter-group:nth-child(3) .filter-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    if (currentSort.field === field) {
        currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.field = field;
        currentSort.order = 'asc';
    }

    const arrow = currentSort.order === 'asc' ? ' ↑' : ' ↓';
    const baseText = event.target.textContent.replace(/[ ↑↓]/g, '');
    event.target.textContent = baseText + arrow;

    sortAsteroids();
    renderTable();
}

// Сортировка астероидов
const sortAsteroids = () => {
    const { field, order } = currentSort;
    const mult = order === 'asc' ? 1 : -1;

    filteredAsteroids.sort((a, b) => {
        let valA, valB;

        switch (field) {
            case 'designation':
                return mult * a.designation.localeCompare(b.designation);
            case 'diameter':
                valA = a.estimated_diameter_km || 0;
                valB = b.estimated_diameter_km || 0;
                return mult * (valA - valB);
            case 'moid':
                valA = a.earth_moid_au || 0;
                valB = b.earth_moid_au || 0;
                return mult * (valA - valB);
            case 'risk':
                valA = a.threat_assessment?.ts_max || 0;
                valB = b.threat_assessment?.ts_max || 0;
                return mult * (valA - valB);
            case 'magnitude':
                valA = a.absolute_magnitude || 0;
                valB = b.absolute_magnitude || 0;
                return mult * (valA - valB);
            case 'albedo':
                valA = a.albedo || 0;
                valB = b.albedo || 0;
                return mult * (valA - valB);
            default:
                return 0;
        }
    });
};


function getRiskClass(tsMax) {
    if (tsMax === 0) return 'risk-none';
    if (tsMax === 1) return 'risk-low';
    if (tsMax >= 2 && tsMax <= 3) return 'risk-medium';
    if (tsMax >= 4 && tsMax <= 5) return 'risk-high';
    return 'risk-critical';
}

function getThreatLevelRu(tsMax) {
    const levels = ['НУЛЕВОЙ', 'ОЧЕНЬ НИЗКИЙ', 'НИЗКИЙ', 'СРЕДНИЙ', 'ВЫСОКИЙ', 'КРИТИЧЕСКИЙ'];
    return levels[Math.min(tsMax, 5)] || 'НУЛЕВОЙ';
}

// Показываем ошибку если данных нет
const showTableError = (message) => {
    const tbody = document.getElementById('asteroids-table-body');
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:2rem;color:var(--text-secondary);">${message}</td></tr>`;
};

// Сбрасываем все фильтры к исходному состоянию
function resetAllFilters() {
    activeFilters = {
        risk: 'all',
        diameter: null,
        orbit: null
    };

    currentSort = { field: 'designation', order: 'asc' };

    document.querySelectorAll('.quick-filters .quick-filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.includes('Все')) {
            btn.classList.add('active');
        }
    });

    document.querySelectorAll('.filter-group:nth-child(1) .filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.includes('Все')) {
            btn.classList.add('active');
        }
    });

    document.querySelectorAll('.filter-group:nth-child(2) .filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.querySelectorAll('.filter-group:nth-child(3) .filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.includes('Обозначение')) {
            btn.classList.add('active');
        }
    });

    // Сбрасываем данные
    filteredAsteroids = [...allAsteroids];
    currentPage = 1;
    sortAsteroids();
    updatePagination();
    renderTable();
}

function updatePagination() {
    totalPages = Math.ceil(filteredAsteroids.length / ITEMS_PER_PAGE);
    if (currentPage > totalPages && totalPages > 0) {
        currentPage = totalPages;
    }
}

function renderPagination() {
    const container = document.getElementById('pagination-container');
    if (!container) return;

    container.innerHTML = '';

    if (totalPages <= 1) {
        return; // Не показываем пагинацию если всего одна страница
    }

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Пред.';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => goToPage(currentPage - 1);
    container.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => goToPage(1);
        container.appendChild(firstBtn);

        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'pagination-info';
            ellipsis.textContent = '...';
            container.appendChild(ellipsis);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.className = 'pagination-btn' + (i === currentPage ? ' active' : '');
        btn.textContent = i;
        btn.onclick = () => goToPage(i);
        container.appendChild(btn);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'pagination-info';
            ellipsis.textContent = '...';
            container.appendChild(ellipsis);
        }

        const lastBtn = document.createElement('button');
        lastBtn.className = 'pagination-btn';
        lastBtn.textContent = totalPages.toString();
        lastBtn.onclick = () => goToPage(totalPages);
        container.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'След. →';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => goToPage(currentPage + 1);
    container.appendChild(nextBtn);
}

function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    renderTable();

    const table = document.getElementById('asteroids-table');
    if (table) {
        table.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

document.addEventListener('DOMContentLoaded', loadAsteroids);
