/* approaches.js - скрипты страницы сближений */

let allApproaches = [];
let filteredApproaches = [];
let currentSort = { field: 'date', order: 'asc' };

// Пагинация - по 20 на страницу чтобы не грузить таблицу
const ITEMS_PER_PAGE = 20;
let currentPage = 1;
let totalPages = 1;
let totalApproaches = 0; // Общее количество сближений в БД

async function loadApproaches() {
    try {
        const countData = await api.getApproachesCount();
        totalApproaches = countData.total;

        allApproaches = await api.getUpcomingApproaches(0, 10000);
        filteredApproaches = [...allApproaches];
        sortApproaches();
        updatePagination();
        renderTable();
    } catch (error) {
        console.error('Ошибка загрузки сближений:', error);
        showNoData('Не удалось загрузить данные о сближениях. Проверьте подключение к серверу.');
    }
}

async function renderTable() {
    const tbody = document.getElementById('approaches-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (filteredApproaches.length === 0) {
        // Если сближений нет после фильтрации - предлагаем сбросить фильтры
        showNoData('Сближений не найдено. Попробуйте изменить параметры фильтрации или сбросить все фильтры.');
        return;
    }

    // Вычисляем индексы для текущей страницы
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const pageApproaches = filteredApproaches.slice(startIndex, endIndex);

    // Загружаем данные об астероидах для текущей страницы
    const enrichedData = await Promise.all(pageApproaches.map(async (approach) => {
        try {
            const asteroid = await api.getAsteroidDetails(approach.asteroid_designation);
            return {
                ...approach,
                magnitude: asteroid.absolute_magnitude,
                asteroid_diameter_km: asteroid.estimated_diameter_km,
                orbit_class: asteroid.orbit_class
            };
        } catch {
            // Если не удалось получить данные об астероиде показываем что есть
            return approach;
        }
    }));

    enrichedData.forEach(approach => {
        const row = document.createElement('tr');
        const distanceClass = getDistanceClass(approach.distance_au);
        const asteroidName = approach.asteroid_name || approach.asteroid_designation;

        row.innerHTML = `
            <td>${formatDateTime(approach.approach_time)}</td>
            <td>
                <a href="../asteroid_detail/asteroid_detail.html?name=${encodeURIComponent(approach.asteroid_designation)}" class="asteroid-link">
                    ${asteroidName}
                </a>
            </td>
            <td>
                <span class="distance-badge ${distanceClass}">${approach.distance_au.toFixed(4)}</span>
            </td>
            <td>${formatDistance(approach.distance_km)}</td>
            <td>${approach.velocity_km_s.toFixed(1)}</td>
            <td>${approach.magnitude ? approach.magnitude.toFixed(1) : '—'}</td>
            <td>${approach.asteroid_diameter_km ? approach.asteroid_diameter_km.toFixed(3) : '—'}</td>
            <td><span class="orbit-class">${approach.orbit_class || '—'}</span></td>
        `;
        tbody.appendChild(row);
    });

    updateCounts();
    renderPagination();
}

function getDistanceClass(distanceAu) {
    if (distanceAu < 0.01) return 'distance-close';
    if (distanceAu < 0.03) return 'distance-medium';
    return 'distance-far';
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric', month: 'long', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function formatDistance(km) {
    if (km >= 1000000) return `${(km / 1000000).toFixed(1)} млн`;
    if (km >= 1000) return `${(km / 1000).toFixed(0)} тыс.`;
    return km.toFixed(0);
}

function updateCounts() {
    const totalCount = document.getElementById('total-count');
    const filteredCount = document.getElementById('filtered-count');

    // Показываем общее количество сближений в БД (не только будущих)
    if (totalCount) totalCount.textContent = totalApproaches;
    if (filteredCount) filteredCount.textContent = filteredApproaches.length;
}

function sortBy(field) {
    const buttons = document.querySelectorAll('.table-filters .filter-btn');
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

    sortApproaches();
    renderTable();
}

function sortApproaches() {
    const { field, order } = currentSort;
    const mult = order === 'asc' ? 1 : -1;

    filteredApproaches.sort((a, b) => {
        if (field === 'date') {
            return mult * (new Date(a.approach_time) - new Date(b.approach_time));
        } else if (field === 'distance') {
            return mult * (a.distance_au - b.distance_au);
        } else if (field === 'velocity') {
            return mult * (b.velocity_km_s - a.velocity_km_s);
        }
        return 0;
    });
}

async function applyFilters() {
    const dateFrom = document.getElementById('filter-date-from').value;
    const dateTo = document.getElementById('filter-date-to').value;
    const maxDistance = document.getElementById('filter-max-distance').value;

    if (!dateFrom && !dateTo && !maxDistance) {
        // Если фильтры пустые показываем все
        filteredApproaches = [...allApproaches];
    } else {
        // Фильтруем локально
        filteredApproaches = allApproaches.filter(approach => {
            const approachDate = new Date(approach.approach_time);
            
            if (dateFrom && approachDate < new Date(dateFrom)) return false;
            if (dateTo && approachDate > new Date(dateTo)) return false;
            if (maxDistance && approach.distance_au > parseFloat(maxDistance)) return false;
            
            return true;
        });
    }

    currentPage = 1;
    sortApproaches();
    renderTable();
}

function resetFilters() {
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-date-to').value = '';
    document.getElementById('filter-max-distance').value = '';
    filteredApproaches = [...allApproaches];
    sortApproaches();
    renderTable();
}

function showNoData(message) {
    const tbody = document.getElementById('approaches-table-body');
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="8" class="no-data">${message}</td></tr>`;
}


function updatePagination() {
    totalPages = Math.ceil(filteredApproaches.length / ITEMS_PER_PAGE);
    // Если текущая страница больше общей переходим на последнюю
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

    // Кнопка "Предыдущая"
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Пред.';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => goToPage(currentPage - 1);
    container.appendChild(prevBtn);

    // Номера страниц
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    // Добавляем первую страницу если она не видна
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

    // Кнопки страниц в диапазоне
    for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.className = 'pagination-btn' + (i === currentPage ? ' active' : '');
        btn.textContent = i;
        btn.onclick = () => goToPage(i);
        container.appendChild(btn);
    }

    // Добавляем последнюю страницу если она не видна
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
    
    // Прокрутка к началу таблицы
    const table = document.getElementById('approaches-table');
    if (table) {
        table.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

document.addEventListener('DOMContentLoaded', loadApproaches);
