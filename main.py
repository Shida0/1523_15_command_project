"""
Asteroid Watch - API для мониторинга околоземных астероидов.

Приложение предоставляет информацию о:
- Астероидах, сближающихся с Землёй
- Оценках угроз столкновения
- Статистике и аналитике
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import asteroid_router, approach_router, threat_router


# === ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ ===
app = FastAPI(
    title="Asteroid Watch API",
    description="""
## 🪨 Asteroid Watch - Мониторинг околоземных астероидов

API предоставляет доступ к данным о:
- **Астероидах** - информация о характеристиках и орбитах
- **Сближениях** - календарь прохождений вблизи Земли
- **Угрозах** - оценки риска столкновения

### Основные возможности:
- 📊 Получение статистики по астероидам
- 🔍 Поиск по обозначению, классу орбиты, MOID
- 📅 Календарь предстоящих сближений
- ⚠️ Оценки угроз по шкале Турина
    """,
    version="1.0.0",
    contact={
        "name": "Asteroid Watch Team",
    },
    license_info={
        "name": "MIT",
    },
)


# === НАСТРОЙКА CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === ПОДКЛЮЧЕНИЕ РОУТЕРОВ ===
app.include_router(asteroid_router, prefix="/api/v1")
app.include_router(approach_router, prefix="/api/v1")
app.include_router(threat_router, prefix="/api/v1")


# === КОРНЕВОЙ ЭНДПОИНТ ===
@app.get("/", tags=["Root"])
async def root():
    """
    🌟 Добро пожаловать в Asteroid Watch API!
    
    Используйте /docs для просмотра документации и тестирования эндпоинтов.
    """
    return {
        "message": "Welcome to Asteroid Watch API",
        "docs": "/docs",
        "endpoints": {
            "asteroids": "/api/v1/asteroids",
            "approaches": "/api/v1/approaches",
            "threats": "/api/v1/threats"
        }
    }


# === HEALTH CHECK ===
@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка работоспособности API."""
    return {"status": "healthy"}


# === ЗАПУСК ПРИЛОЖЕНИЯ ===
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
