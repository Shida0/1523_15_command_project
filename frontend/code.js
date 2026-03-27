/* ==================================================================
   Фронтенд Asteroid Watch.
   Загружает все астероиды, сближения и угрозы из API,
   агрегирует их и отображает в таблице.
   ================================================================== */

const API_BASE = 'http://localhost:8000/api/v1';

let asteroids = [];
let currentSort = 'date';
let threatFilter = 'all';
let visibleCount = 50;
const step = 50;

const searchInput = document.getElementById('asteroidSearch');
const cardsGrid = document.getElementById('cardsGrid');
const loadMoreBtn = document.getElementById('loadMoreBtn');

function formatNumberWithSpaces(num) {
    return Math.round(num).toLocaleString('ru-RU');
}

async function loadData() {
    try {
        // Загрузка всех астероидов с пагинацией
        let allAsteroids = [];
        let skip = 0;
        const limit = 500;
        while (true) {
            const url = `${API_BASE}/asteroids/all?skip=${skip}&limit=${limit}`;
            const response = await fetch(url);
            if (!response.ok) break;
            const data = await response.json();
            if (data.length === 0) break;
            allAsteroids.push(...data);
            if (data.length < limit) break;
            skip += limit;
        }

        const asteroidMap = new Map();
        allAsteroids.forEach(ast => asteroidMap.set(ast.designation, ast));

        // Загрузка предстоящих сближений
        const approachesResp = await fetch(`${API_BASE}/approaches/upcoming?limit=1000`);
        const approaches = await approachesResp.json();
        const approachMap = new Map();
        approaches.forEach(app => {
            const des = app.asteroid_designation;
            if (!approachMap.has(des)) approachMap.set(des, app);
        });

        // Загрузка угроз
        let threats = [];
        try {
            const threatsResp = await fetch(`${API_BASE}/threats/current?limit=500`);
            threats = await threatsResp.json();
        } catch (e) {
            console.warn('Не удалось загрузить угрозы', e);
        }
        const threatMap = new Map();
        threats.forEach(th => threatMap.set(th.designation, th));

        // Формирование итогового массива
        const result = [];
        for (const [designation, approach] of approachMap.entries()) {
            const asteroid = asteroidMap.get(designation);
            if (!asteroid) continue;

            const sizeKm = asteroid.estimated_diameter_km || 0;
            const sizeMeters = sizeKm * 1000;
            const sizeStr = `${Math.round(sizeMeters)} м`;

            const distKm = approach.distance_km;
            const distStr = `${formatNumberWithSpaces(distKm)} км`;

            const approachDate = new Date(approach.approach_time);
            const dateStr = approachDate.toISOString().split('T')[0];

            const threatObj = threatMap.get(designation);
            let threatColor = 'green';
            if (threatObj && threatObj.ts_max !== undefined) {
                const ts = threatObj.ts_max;
                if (ts >= 5) threatColor = 'red';
                else if (ts >= 1) threatColor = 'yellow';
            }

            result.push({
                name: asteroid.name || asteroid.designation,
                date: dateStr,
                size: sizeStr,
                sizeVal: sizeMeters,
                distance: distStr,
                distVal: distKm,
                threat: threatColor,
            });
        }

        asteroids = result;
        const totalCountElem = document.getElementById('totalCount');
        if (totalCountElem) totalCountElem.textContent = result.length;

        renderCards(searchInput.value);
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        if (cardsGrid) {
            cardsGrid.innerHTML = '<div class="error-message">Ошибка загрузки данных. Попробуйте позже.</div>';
        }
    }
}

function renderCards(filterText = "") {
    if (!cardsGrid) return;

    let filtered = asteroids.filter(ast => {
        const matchesName = ast.name.toLowerCase().includes(filterText.toLowerCase());
        const matchesThreat = threatFilter === 'all' || ast.threat === threatFilter;
        return matchesName && matchesThreat;
    });

    filtered.sort((a, b) => {
        if (currentSort === 'date') return new Date(a.date) - new Date(b.date);
        if (currentSort === 'size') return b.sizeVal - a.sizeVal;
        if (currentSort === 'distance') return a.distVal - b.distVal;
        return 0;
    });

    cardsGrid.innerHTML = `
        <div class="table-header">
            <div>Астероид</div>
            <div>Дата сближения</div>
            <div>Размер (м)</div>
            <div>Расстояние</div>
            <div>Уровень угрозы</div>
        </div>
    `;

    const displayed = filtered.slice(0, visibleCount);
    displayed.forEach(ast => {
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

if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', () => {
        visibleCount += step;
        renderCards(searchInput.value);
    });
}

document.querySelectorAll('.threat-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        threatFilter = e.target.dataset.threat;
        visibleCount = step;
        document.querySelectorAll('.threat-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        renderCards(searchInput.value);
    });
});

document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        currentSort = e.target.dataset.sort;
        visibleCount = step;
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        renderCards(searchInput.value);
    });
});

if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        visibleCount = step;
        renderCards(e.target.value);
    });
}

loadData();