/* api.js - наш API клиент для общения с бэкендом 
 * чтобы не дублировать код обработки ошибок.
 */

const API_BASE = 'http://localhost:8000/api/v1';

// Базовая функция для всех запросов
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

// Функции для работы с астероидами 
// Получаем все астероиды с пагинацией 
async function getAllAsteroids(skip = 0, limit = null) {
    let url = `/asteroids/all?skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// считаем общее количество астероидов в базе
async function getAsteroidsCount() {
    return apiRequest('/asteroids/count');
}

async function getNearEarthAsteroids(maxMoid = 0.05, skip = 0, limit = null) {
    let url = `/asteroids/near-earth?max_moid=${maxMoid}&skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Фильтруем астероиды по классу орбиты
async function getAsteroidsByOrbitClass(orbitClass, skip = 0, limit = null) {
    let url = `/asteroids/orbit-class/${orbitClass}?skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Астероиды с точно измеренным диаметром 
async function getAsteroidsWithAccurateDiameter(skip = 0, limit = null) {
    let url = `/asteroids/accurate-diameter?skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Общая статистика по всем астероидам
async function getAsteroidsStatistics() {
    return apiRequest('/asteroids/statistics');
}

// Детальная информация по конкретному астероиду - основная инфа + сближения + угрозы
async function getAsteroidDetails(designation) {
    return apiRequest(`/asteroids/${encodeURIComponent(designation)}`);
}

// Берём ближайшие сближения - сортируются по дате на бэкенде
async function getUpcomingApproaches(limit = null) {
    let url = '/approaches/upcoming';
    if (limit !== null) {
        url += `?limit=${limit}`;
    }
    return apiRequest(url);
}

// Общее количество записей о сближениях в базе
async function getApproachesCount() {
    return apiRequest('/approaches/count');
}

// Самые близкие пролёты
async function getClosestApproaches(skip = 0, limit = null) {
    let url = `/approaches/closest?skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Самые быстрые сближения
async function getFastestApproaches(skip = 0, limit = null) {
    let url = `/approaches/fastest?skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Ищем сближения за конкретный период
async function getApproachesInPeriod(startDate, endDate, maxDistance = null, skip = 0, limit = null) {
    let url = `/approaches/in-period?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}&skip=${skip}`;
    if (maxDistance !== null) {
        url += `&max_distance=${maxDistance}`;
    }
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Статистика по всем сближениям
async function getApproachesStatistics() {
    return apiRequest('/approaches/statistics');
}

// Все сближения для конкретного астероида по его ID
async function getApproachesByAsteroidId(asteroidId, skip = 0, limit = null) {
    let url = `/approaches/by-id/${asteroidId}?skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Сближения по обозначению астероида
async function getApproachesByDesignation(designation, skip = 0, limit = null) {
    let url = `/approaches/by-designation/${encodeURIComponent(designation)}?skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Текущие угрозы - берём все астероиды у которых есть оценка риска
async function getCurrentThreats(minTs = 0, skip = 0, limit = null) {
    let url = `/threats/current?min_ts=${minTs}&skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Только высокий риск
async function getHighRiskThreats(skip = 0, limit = null) {
    let url = `/threats/high-risk?skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Фильтр по вероятности столкновения 
async function getThreatsByProbability(minProbability = 0, maxProbability = 1, skip = 0, limit = null) {
    let url = `/threats/by-probability?min_probability=${minProbability}&max_probability=${maxProbability}&skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Угрозы по энергии воздействия 
async function getThreatsByEnergy(minEnergy = 0, maxEnergy = null, skip = 0, limit = null) {
    let url = `/threats/by-energy?min_energy=${minEnergy}&skip=${skip}`;
    if (maxEnergy !== null) {
        url += `&max_energy=${maxEnergy}`;
    }
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}

// Статистика по угрозам
async function getThreatsStatistics() {
    return apiRequest('/threats/statistics');
}

// Конкретная угроза по обозначению астероида
async function getThreatByDesignation(designation) {
    return apiRequest(`/threats/${encodeURIComponent(designation)}`);
}

// Угрозы по категории воздействия
async function getThreatsByCategory(category, skip = 0, limit = null) {
    let url = `/threats/by-category/${encodeURIComponent(category)}?skip=${skip}`;
    if (limit !== null) {
        url += `&limit=${limit}`;
    }
    return apiRequest(url);
}


// Экспорт функций
window.api = {
    // Астероиды
    getAllAsteroids,
    getAsteroidsCount,
    getNearEarthAsteroids,
    getAsteroidsByOrbitClass,
    getAsteroidsWithAccurateDiameter,
    getAsteroidsStatistics,
    getAsteroidDetails,
    
    // Сближения
    getUpcomingApproaches,
    getApproachesCount,
    getClosestApproaches,
    getFastestApproaches,
    getApproachesInPeriod,
    getApproachesStatistics,
    getApproachesByAsteroidId,
    getApproachesByDesignation,
    
    // Угрозы
    getCurrentThreats,
    getHighRiskThreats,
    getThreatsByProbability,
    getThreatsByEnergy,
    getThreatsStatistics,
    getThreatByDesignation,
    getThreatsByCategory
};
