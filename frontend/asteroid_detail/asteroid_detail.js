/* asteroid_detail.js - загрузка и отображение деталей астероида */

async function loadAsteroidData() {
    const urlParams = new URLSearchParams(window.location.search);
    const designation = urlParams.get('name');

    if (!designation) {
        showError('Не указано обозначение астероида в URL параметре.');
        return;
    }

    try {
        const asteroid = await api.getAsteroidDetails(designation);

        if (!asteroid) {
            showError('Астероид с таким обозначением не найден в базе данных.');
            return;
        }

        displayAsteroidData(asteroid);
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        showError('Не удалось загрузить данные об астероиде. Проверьте подключение к серверу или попробуйте позже.');
    }
}

function displayAsteroidData(asteroid) {
    // Заголовок страницы
    const title = document.getElementById('asteroid-title');
    const subtitle = document.getElementById('asteroid-subtitle');
    const breadcrumb = document.getElementById('breadcrumb-asteroid');

    const fullName = `${asteroid.designation}${asteroid.name ? ' (' + asteroid.name + ')' : ''}`;
    title.textContent = fullName;
    breadcrumb.textContent = fullName;
    subtitle.textContent = `Подробная информация об астероиде ${asteroid.designation}`;

    // Основная информация
    document.getElementById('designation').textContent = asteroid.designation;
    document.getElementById('name').textContent = asteroid.name || '—';
    document.getElementById('diameter').textContent = `${asteroid.estimated_diameter_km.toFixed(3)} км`;
    document.getElementById('diameter-source').textContent = asteroid.accurate_diameter ? 'Измерен NASA' : 'Расчётный';
    document.getElementById('absolute-magnitude').textContent = asteroid.absolute_magnitude.toFixed(2);
    document.getElementById('albedo').textContent = asteroid.albedo ? asteroid.albedo.toFixed(3) : '—';

    // Орбитальная информация
    document.getElementById('orbit-class').textContent = asteroid.orbit_class;
    document.getElementById('orbit-id').textContent = asteroid.orbit_id || '—';
    document.getElementById('perihelion').textContent = `${asteroid.perihelion_au.toFixed(3)} а.е.`;
    document.getElementById('aphelion').textContent = `${asteroid.aphelion_au.toFixed(3)} а.е.`;
    document.getElementById('moid').textContent = `${asteroid.earth_moid_au.toFixed(4)} а.е.`;

    // Угроза и риск - данные из NASA Sentry
    const threat = asteroid.threat_assessment;
    if (threat) {
        document.getElementById('impact-probability').textContent = threat.ip ? `${(threat.ip * 100).toFixed(6)}%` : '0%';

        const turinScaleEl = document.getElementById('turin-scale');
        turinScaleEl.textContent = threat.ts_max;
        turinScaleEl.style.background = getTurinColor(threat.ts_max);
        turinScaleEl.style.color = '#fff';

        document.getElementById('palermo-scale').textContent = threat.ps_max ? threat.ps_max.toFixed(2) : '—';
        document.getElementById('energy').textContent = threat.energy_megatons ? `${threat.energy_megatons.toFixed(1)} Мт` : '—';
        document.getElementById('impact-category').textContent = threat.impact_category || '—';
        document.getElementById('threat-level').textContent = getThreatLevelRu(threat.ts_max);

        // Года риска берём из threat_assessment или из close_approaches
        const impactYears = threat.impact_years || [];
        const riskYearsSection = document.getElementById('risk-years-section');
        const riskYearsEl = document.getElementById('risk-years');

        if (impactYears.length > 0) {
            riskYearsSection.style.display = 'block';
            riskYearsEl.innerHTML = impactYears
                .map(year => `<span class="risk-year">${year}</span>`)
                .join('');
        } else {
            riskYearsSection.style.display = 'none';
        }
    } else {
        // Нет данных об угрозе - показываем нулевые значения
        document.getElementById('impact-probability').textContent = '0%';
        const turinScaleEl = document.getElementById('turin-scale');
        turinScaleEl.textContent = '0';
        turinScaleEl.style.background = getTurinColor(0);
        turinScaleEl.style.color = '#fff';
        document.getElementById('palermo-scale').textContent = '—';
        document.getElementById('energy').textContent = '—';
        document.getElementById('impact-category').textContent = '—';
        document.getElementById('threat-level').textContent = 'НУЛЕВОЙ';
        document.getElementById('risk-years-section').style.display = 'none';
    }

    // Сближения с Землёй
    displayApproaches(asteroid.close_approaches, asteroid.designation);
}

function displayApproaches(approaches, designation) {
    const approachesContent = document.getElementById('approaches-content');

    if (!approaches || approaches.length === 0) {
        // Пробуем загрузить сближения отдельно
        loadApproachesForAsteroid(designation);
        return;
    }

    const approachesList = document.createElement('div');
    approachesList.className = 'approaches-list';

    approaches.forEach(approach => {
        const approachItem = document.createElement('div');
        approachItem.className = 'approach-item';
        approachItem.innerHTML = `
            <div class="approach-header">
                <span class="approach-date">📅 ${formatDateTime(approach.approach_time)}</span>
                <span class="approach-distance">📏 ${(approach.distance_au * 1000).toFixed(0)} тыс. км</span>
            </div>
            <div class="approach-grid">
                <div class="approach-info">
                    <span class="approach-info-label">Расстояние (а.е.)</span>
                    <span class="approach-info-value">${approach.distance_au.toFixed(4)}</span>
                </div>
                <div class="approach-info">
                    <span class="approach-info-label">Скорость (км/с)</span>
                    <span class="approach-info-value">${approach.velocity_km_s.toFixed(1)}</span>
                </div>
                <div class="approach-info">
                    <span class="approach-info-label">Расстояние (км)</span>
                    <span class="approach-info-value">${formatDistance(approach.distance_km)}</span>
                </div>
            </div>
        `;
        approachesList.appendChild(approachItem);
    });

    approachesContent.innerHTML = '';
    approachesContent.appendChild(approachesList);
}

// Загружаем сближения для астероида если их нет в основных данных
async function loadApproachesForAsteroid(designation) {
    const approachesContent = document.getElementById('approaches-content');

    try {
        const approaches = await api.getApproachesByDesignation(designation, 0, 10);

        if (!approaches || approaches.length === 0) {
            approachesContent.innerHTML = '<p class="no-data">Нет данных о предстоящих сближениях</p>';
            return;
        }

        const approachesList = document.createElement('div');
        approachesList.className = 'approaches-list';

        approaches.forEach(approach => {
            const approachItem = document.createElement('div');
            approachItem.className = 'approach-item';
            approachItem.innerHTML = `
                <div class="approach-header">
                    <span class="approach-date">📅 ${formatDateTime(approach.approach_time)}</span>
                    <span class="approach-distance">📏 ${(approach.distance_au * 1000).toFixed(0)} тыс. км</span>
                </div>
                <div class="approach-grid">
                    <div class="approach-info">
                        <span class="approach-info-label">Расстояние (а.е.)</span>
                        <span class="approach-info-value">${approach.distance_au.toFixed(4)}</span>
                    </div>
                    <div class="approach-info">
                        <span class="approach-info-label">Скорость (км/с)</span>
                        <span class="approach-info-value">${approach.velocity_km_s.toFixed(1)}</span>
                    </div>
                    <div class="approach-info">
                        <span class="approach-info-label">Расстояние (км)</span>
                        <span class="approach-info-value">${formatDistance(approach.distance_km)}</span>
                    </div>
                </div>
            `;
            approachesList.appendChild(approachItem);
        });

        approachesContent.innerHTML = '';
        approachesContent.appendChild(approachesList);
    } catch (error) {
        console.error('Ошибка загрузки сближений:', error);
        approachesContent.innerHTML = '<p class="no-data">Не удалось загрузить данные о сближениях</p>';
    }
}

const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
};

const formatDistance = (km) => {
    if (km >= 1000000) {
        return `${(km / 1000000).toFixed(1)} млн`;
    }
    if (km >= 1000) {
        return `${(km / 1000).toFixed(0)} тыс.`;
    }
    return km.toFixed(0);
};

const getTurinColor = (tsMax) => {
    if (tsMax === 0) return '#10b981';
    if (tsMax === 1) return '#84cc16';
    if (tsMax >= 2 && tsMax <= 3) return '#eab308';
    if (tsMax >= 4 && tsMax <= 5) return '#f97316';
    return '#ef4444';
};

function getThreatLevelRu(tsMax) {
    const levels = ['НУЛЕВОЙ', 'ОЧЕНЬ НИЗКИЙ', 'НИЗКИЙ', 'СРЕДНИЙ', 'ВЫСОКИЙ', 'КРИТИЧЕСКИЙ'];
    return levels[Math.min(tsMax, 5)] || 'НЕИЗВЕСТНЫЙ';
}

function showError(message) {
    const title = document.getElementById('asteroid-title');
    const subtitle = document.getElementById('asteroid-subtitle');

    title.textContent = 'Ошибка';
    subtitle.textContent = message;

    const detailContainer = document.querySelector('.detail-container');
    if (detailContainer) {
        detailContainer.innerHTML = `
            <div class="detail-card">
                <div class="card-content">
                    <p class="no-data">${message}</p>
                    <div style="margin-top: 2rem; text-align: center;">
                        <a href="../asteroids/asteroids.html" class="nav-btn btn-primary">
                            ← К каталогу астероидов
                        </a>
                    </div>
                </div>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadAsteroidData();
});
