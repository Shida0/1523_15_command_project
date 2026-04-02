/* threats.js - скрипты страницы угроз */

let allThreats = [];
let filteredThreats = [];
let currentSort = { field: 'ts_max', order: 'desc' };

async function loadThreats() {
    try {
        allThreats = await api.getCurrentThreats(0, 0, 10000);
        filteredThreats = [...allThreats];
        updateStats();
        sortThreats();
        renderTable();
    } catch (error) {
        console.error('Ошибка загрузки угроз:', error);
        showNoData('Не удалось загрузить данные об угрозах. Проверьте подключение к серверу.');
    }
}

function updateStats() {
    const total = allThreats.length;
    const highRisk = allThreats.filter(t => t.ts_max >= 5).length;
    const mediumRisk = allThreats.filter(t => t.ts_max >= 2 && t.ts_max <= 4).length;
    const lowRisk = allThreats.filter(t => t.ts_max <= 1).length;

    document.getElementById('total-threats').textContent = total;
    document.getElementById('high-risk-count').textContent = highRisk;
    document.getElementById('medium-risk-count').textContent = mediumRisk;
    document.getElementById('low-risk-count').textContent = lowRisk;

    // Показываем баннер если угроз нет 
    const banner = document.getElementById('no-threats-banner');
    if (banner) {
        banner.style.display = total === 0 ? 'flex' : 'none';
    }
}

function renderTable() {
    const tbody = document.getElementById('threats-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (filteredThreats.length === 0) {
        if (allThreats.length === 0) return;
        // Если после фильтрации ничего нет
        showNoData('Угроз не найдено по выбранным фильтрам. Попробуйте выбрать другой уровень риска или сбросить фильтры.');
        return;
    }

    filteredThreats.forEach(threat => {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>
                <a href="../asteroid_detail/asteroid_detail.html?name=${encodeURIComponent(threat.designation)}" class="asteroid-link">
                    ${threat.fullname || threat.designation}
                </a>
            </td>
            <td>
                <span class="torino-badge torino-${threat.ts_max}" title="${getTorinoDescription(threat.ts_max)}">
                    ${threat.ts_max}
                </span>
            </td>
            <td>${threat.ps_max ? threat.ps_max.toFixed(2) : '—'}</td>
            <td>${formatProbability(threat.ip)}</td>
            <td>${threat.energy_megatons ? threat.energy_megatons.toFixed(1) : '—'}</td>
            <td>
                <span class="impact-category ${getImpactClass(threat.impact_category)}">
                    ${threat.impact_category || '—'}
                </span>
            </td>
            <td>
                ${threat.impact_years && threat.impact_years.length > 0
                    ? `<div class="risk-years">${threat.impact_years.slice(0, 5).map(y => `<span class="risk-year">${y}</span>`).join('')}</div>`
                    : '—'
                }
            </td>
            <td><span class="risk-badge ${getRiskClass(threat.ts_max)}">${threat.threat_level_ru || '—'}</span></td>
            <td>${threat.diameter_km ? threat.diameter_km.toFixed(3) : '—'}</td>
            <td>${threat.velocity_km_s ? threat.velocity_km_s.toFixed(1) : '—'}</td>
            <td>${threat.absolute_magnitude ? threat.absolute_magnitude.toFixed(2) : '—'}</td>
            <td>${threat.n_imp || '—'}</td>
            <td>${threat.last_obs || '—'}</td>
            <td>${threat.torino_scale_ru || '—'}</td>
            <td>${threat.impact_probability_text_ru || '—'}</td>
        `;
        tbody.appendChild(row);
    });

    updateCounts();
}

function getTorinoDescription(level) {
    const descriptions = [
        'Нет риска', 'Нормальный', 'Внимание', 'Угроза', 'Высокий',
        'Серьёзный', 'Угроза', 'Опасный', 'Катастрофа', 'Глобальный', 'Коллизия'
    ];
    return descriptions[level] || '';
}

function formatProbability(prob) {
    if (!prob || prob === 0) return '0%';
    return `${(prob * 100).toFixed(4)}%`;
}

function getImpactClass(category) {
    if (!category) return 'impact-local';
    if (category.includes('глоб')) return 'impact-global';
    if (category.includes('регион')) return 'impact-regional';
    return 'impact-local';
}

function getRiskClass(tsMax) {
    if (tsMax === 0) return 'risk-none';
    if (tsMax === 1) return 'risk-low';
    if (tsMax >= 2 && tsMax <= 3) return 'risk-medium';
    if (tsMax >= 4 && tsMax <= 5) return 'risk-high';
    return 'risk-critical';
}

function updateCounts() {
    const totalCount = document.getElementById('total-count');
    const badge = document.getElementById('threats-count-badge');

    if (totalCount) totalCount.textContent = allThreats.length;
    if (badge) badge.textContent = filteredThreats.length;
}

async function filterByRisk(risk) {
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    try {
        if (risk === 'all') {
            filteredThreats = await api.getCurrentThreats(0, 0, 10000);
        } else if (risk === 'high') {
            filteredThreats = await api.getHighRiskThreats(0, 10000);
        } else if (risk === 'medium') {
            const all = await api.getCurrentThreats(0, 0, 10000);
            filteredThreats = all.filter(t => t.ts_max >= 2 && t.ts_max <= 4);
        } else if (risk === 'low') {
            const all = await api.getCurrentThreats(0, 0, 10000);
            filteredThreats = all.filter(t => t.ts_max <= 1);
        }

        allThreats = filteredThreats;
        updateStats();
        renderTable();
    } catch (error) {
        console.error('Ошибка фильтрации:', error);
        showNoData('Не удалось загрузить данные фильтра');
    }
}

function sortTable(field) {
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    if (currentSort.field === field) {
        currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.field = field;
        currentSort.order = 'desc';
    }

    const arrow = currentSort.order === 'asc' ? ' ↑' : ' ↓';
    const baseText = event.target.textContent.replace(/[ ↑↓]/g, '');
    event.target.textContent = baseText + arrow;

    sortThreats();
    renderTable();
}

function sortThreats() {
    const { field, order } = currentSort;
    const mult = order === 'asc' ? 1 : -1;

    filteredThreats.sort((a, b) => {
        let valA, valB;

        switch (field) {
            case 'ts_max':
                valA = a.ts_max || 0;
                valB = b.ts_max || 0;
                return mult * (valA - valB);
            case 'ps_max':
                valA = a.ps_max || -999;
                valB = b.ps_max || -999;
                return mult * (valA - valB);
            case 'probability':
                valA = a.ip || 0;
                valB = b.ip || 0;
                return mult * (valA - valB);
            case 'energy':
                valA = a.energy_megatons || 0;
                valB = b.energy_megatons || 0;
                return mult * (valA - valB);
            case 'designation':
                return mult * a.designation.localeCompare(b.designation);
            default:
                return 0;
        }
    });
}

function showNoData(message) {
    const tbody = document.getElementById('threats-table-body');
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="8" class="no-data">${message}</td></tr>`;
}

document.addEventListener('DOMContentLoaded', loadThreats);
