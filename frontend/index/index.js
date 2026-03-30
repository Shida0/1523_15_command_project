/* index.js - скрипты главной страницы 
 * Загружаем статистику и показываем первые 15 астероидов для превью
 */

const ITEMS_PER_PAGE = 15;
let allAsteroids = [];
let filteredAsteroids = [];

async function loadPageData() {
    await loadStatistics();
    await loadAsteroids();
}

async function loadStatistics() {
    try {
        const [asteroidsStats, approachesStats, threatsStats] = await Promise.allSettled([
            api.getAsteroidsStatistics(),
            api.getApproachesStatistics(),
            api.getThreatsStatistics()
        ]);

        if (asteroidsStats.status === 'fulfilled' && asteroidsStats.value) {
            document.getElementById('stat-total-asteroids').textContent =
                formatNumber(asteroidsStats.value.total_asteroids || 0);
        }

        if (approachesStats.status === 'fulfilled' && approachesStats.value) {
            document.getElementById('stat-total-approaches').textContent =
                formatNumber(approachesStats.value.total_approaches || 0);
        }

        if (threatsStats.status === 'fulfilled' && threatsStats.value) {
            document.getElementById('stat-total-threats').textContent =
                formatNumber(threatsStats.value.total_threats || 0);
            document.getElementById('stat-high-risk').textContent =
                formatNumber(threatsStats.value.high_risk_count || 0);
        }
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
        // Если статистика не загрузилась
        document.getElementById('stat-total-asteroids').textContent = '—';
        document.getElementById('stat-total-approaches').textContent = '—';
        document.getElementById('stat-total-threats').textContent = '—';
        document.getElementById('stat-high-risk').textContent = '—';
    }
}

// Получаем список астероидов для главной таблицы, показываем первые 15
async function loadAsteroids() {
    try {
        allAsteroids = await api.getAllAsteroids();
        filteredAsteroids = [...allAsteroids];
        renderTable(filteredAsteroids);
    } catch (error) {
        console.error('Ошибка загрузки астероидов:', error);
        showTableError('Не удалось загрузить данные. Проверьте подключение к серверу.');
    }
}

function formatNumber(num) {
    return num.toLocaleString('ru-RU');
}

// Рендерим таблицу с астероидами
function renderTable(data) {
    const tbody = document.getElementById('asteroid-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    const pageData = data.slice(0, ITEMS_PER_PAGE);

    if (pageData.length === 0) {
        // Если данных нет - показываем сообщение с предложением сбросить фильтры
        showTableError('Астероиды не найдены. Попробуйте сбросить фильтры или выбрать другой критерий.');
        return;
    }

    pageData.forEach(asteroid => {
        const riskClass = getRiskClass(asteroid.threat_assessment?.ts_max || 0);
        const sourceClass = asteroid.accurate_diameter ? 'source-nasa' : 'source-calculated';
        const sourceText = asteroid.accurate_diameter ? 'NASA' : 'Расчёт';
        const sourceIcon = asteroid.accurate_diameter ? '✓' : '≈';

        const row = document.createElement('tr');
        row.innerHTML = `
            <td><a href="../asteroid_detail/asteroid_detail.html?name=${encodeURIComponent(asteroid.designation)}" class="asteroid-link">${asteroid.designation}</a></td>
            <td>${asteroid.name ? `<a href="../asteroid_detail/asteroid_detail.html?name=${encodeURIComponent(asteroid.designation)}" class="asteroid-link">${asteroid.name}</a>` : '—'}</td>
            <td>${asteroid.estimated_diameter_km.toFixed(3)}</td>
            <td>${asteroid.earth_moid_au.toFixed(4)}</td>
            <td>${asteroid.absolute_magnitude.toFixed(2)}</td>
            <td>${asteroid.albedo ? asteroid.albedo.toFixed(3) : '—'}</td>
            <td><span class="orbit-class">${asteroid.orbit_class}</span></td>
            <td><span class="risk-badge ${riskClass}">${asteroid.threat_assessment ? getThreatLevelRu(asteroid.threat_assessment.ts_max) : 'НУЛЕВОЙ'}</span></td>
        `;
        tbody.appendChild(row);
    });

    const showingCount = document.getElementById('total-count');
    if (showingCount) {
        showingCount.textContent = data.length;
    }
}

// Фильтрация таблицы по риску - все/высокий/околоземные
function filterTable(filter, btnElement = null) {
    const desktopButtons = document.querySelectorAll('.desktop-filters .filter-btn');
    const mobileButtons = document.querySelectorAll('.mobile-filters-panel .filter-btn');

    desktopButtons.forEach(btn => btn.classList.remove('active'));
    mobileButtons.forEach(btn => btn.classList.remove('active'));

    if (btnElement) {
        btnElement.classList.add('active');
    } else if (event && event.target.classList.contains('filter-btn')) {
        event.target.classList.add('active');
    } else {
        const matchingDesktop = Array.from(desktopButtons).find(btn => btn.textContent.includes(getFilterText(filter)));
        const matchingMobile = Array.from(mobileButtons).find(btn => btn.textContent.includes(getFilterText(filter)));
        if (matchingDesktop) matchingDesktop.classList.add('active');
        if (matchingMobile) matchingMobile.classList.add('active');
    }

    let filtered = allAsteroids;

    if (filter === 'high-risk') {
        filtered = allAsteroids.filter(a => (a.threat_assessment?.ts_max || 0) >= 2);
    } else if (filter === 'near-earth') {
        filtered = allAsteroids.filter(a => a.earth_moid_au <= 0.05);
    }

    filteredAsteroids = filtered;
    renderTable(filteredAsteroids);
}

function getFilterText(filter) {
    const texts = {
        'all': 'Все',
        'high-risk': 'Высокий',
        'near-earth': 'Околоземные'
    };
    return texts[filter] || '';
}

function getRiskClass(tsMax) {
    if (tsMax === 0) return 'risk-none';
    if (tsMax === 1) return 'risk-low';
    if (tsMax >= 2 && tsMax <= 3) return 'risk-medium';
    if (tsMax >= 4 && tsMax <= 5) return 'risk-high';
    return 'risk-critical';
}

function getThreatLevelRu(tsMax) {
    const levels = ['НУЛЕВОЙ', 'ОЧЕНЬ НИЗКИЙ', 'НИЗКИЙ', 'СРЕДНИЙ', 'ВЫСОКИЙ', 'КРИТИЧЕСКИЙ'];
    return levels[Math.min(tsMax, 5)] || 'НЕИЗВЕСТНЫЙ';
}

function showTableError(message) {
    const tbody = document.getElementById('asteroid-table-body');
    if (!tbody) return;

    tbody.innerHTML = `
        <tr>
            <td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-secondary);">${message}</td>
        </tr>
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    loadPageData();
});
