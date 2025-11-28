from astroquery.jplhorizons import Horizons
from datetime import datetime, timedelta
import json
import time
from astropy.time import Time

def get_neo_data() -> list:
    with open("data/neo_data.json") as file:
        src = json.load(file)
        return src["neo_objects"]

def get_current_close_approaches(days=30):
    """
    Получает астероиды, которые реально приближаются к Земле в ближайшие дни
    """
    neo_catalog = get_neo_data()
    
    close_approaches = []
    
    test_asteroids = [a for a in neo_catalog if a.get('is_pha')]
    
    # время нынешнее и через 30 дней
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    
    print(f"Запрашиваемый период: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    
    # проходимся по всем потенциально опасным астероидам 
    for asteroid in test_asteroids:
        try:
            print(f"Обрабатывается {asteroid['name']}...")
            
            # Здесь мы стмотрим на астероид в период времени от нынешнего момента до того который будет через 30 дней
            obj = Horizons(
                id=str(asteroid['number']),
                location='399',
                id_type=None,
                epochs={
                    "start": start_date.strftime('%Y-%m-%d'),
                    "stop": end_date.strftime('%Y-%m-%d'),
                    "step": "1d"
                }
            )
            
            # Получаем эфемериды для реального временного периода - что то типа координат астероида прямо сейчас
            eph = obj.ephemerides()
            
            print(f"Получены данные для {asteroid['name']}: {len(eph)} записей")
            
            # Ищем близкие подходы с более реалистичным порогом
            for position in eph:
                distance_au = float(position['delta'])
                if distance_au < 0.05:
                    approach_info = {
                        'asteroid': asteroid['name'],
                        'asteroid_number': asteroid['number'],
                        'approach_date': position['datetime_str'],
                        'distance_au': distance_au,
                        'distance_km': distance_au * 149597870.7,
                        'velocity_km_s': float(position['delta_rate']) if 'delta_rate' in position.colnames else 0,
                    }
                    close_approaches.append(approach_info)
            
            # Задержка чтобы не перегружать сервер
            time.sleep(2)
                    
        except Exception as e:
            print(f"Ошибка для астероида {asteroid.get('name', asteroid['number'])}: {e}")
            continue
    
    # Сортируем по расстоянию (от ближайшего к дальнему)
    close_approaches.sort(key=lambda x: x['distance_au'])
    
    return close_approaches

# Запускаем и выводим результат
# Это все необязательно - потом при создании сайта нужно будет удалить
print("=== СИСТЕМА МОНИТОРИНГА АСТЕРОИДОВ ===")
print(f"Текущая дата: {datetime.now().strftime('%Y-%m-%d')}")

print("\n🔍 Поиск близких сближений в ближайшие 30 дней...")
approaches = get_current_close_approaches(30)

print(f"\n📊 Найдено близких сближений: {len(approaches)}")

if approaches:
    print("\n⚠️  БЛИЗКИЕ СБЛИЖЕНИЯ:")
    for approach in approaches:
        print(f"• {approach['asteroid']}:")
        print(f"  Дата: {approach['approach_date']}")
        print(f"  Расстояние: {approach['distance_au']:.4f} а.е. ({approach['distance_km']:.0f} км)")
        print(f"  Скорость: {approach['velocity_km_s']:.1f} км/с")
        if 'current_distance_note' in approach:
            print(f"  Примечание: {approach['current_distance_note']}")
        print()
else:
    print("✅ В указанный период близких сближений не обнаружено")

print(f"\n💡 Примечание: Система ищет сближения ближе 0.05 а.е. (7.5 млн км)")
print(f"   Текущий год: {datetime.now().year}")