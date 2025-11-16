from astroquery.mpc import MPC
import json
import csv
import os
from datetime import datetime

# Получаем данные обо всех NEO в данный момент
def get_neo() -> tuple:
    all_asteroids = MPC.query_objects("asteroid") # получаем данные обо всех астероидах
    
    neo_list_csv = [] # для csv
    neo_list_json = [] # для json
    
    for asteroid in all_asteroids:
        try:
            perihelion = float(asteroid['perihelion_distance']) # перигелий
            
            if perihelion <= 1.3:  # Значит это NEO
                is_pha = asteroid.get('pha', False) # является ли астероид потенциально опасным
                H_mag = float(asteroid['absolute_magnitude'])
                
                # Данные для CSV
                neo_list = [
                    asteroid.get("number"),
                    asteroid.get("name", ""),
                    asteroid.get("designation", ""),
                    perihelion,
                    float(asteroid['aphelion_distance']),
                    float(asteroid['earth_moid']),
                    H_mag,
                    asteroid.get("neo"),
                    is_pha,
                ]
                
                # Данные для JSON
                neo_dict = {
                    'number': asteroid['number'],
                    'name': asteroid.get('name', ''),
                    'designation': asteroid.get('designation', ''),
                    'perihelion_au': perihelion,
                    'aphelion_au': float(asteroid['aphelion_distance']),
                    'earth_moid_au': float(asteroid['earth_moid']),
                    'H_mag': H_mag,
                    'is_neo': asteroid.get("neo"),
                    'is_pha': is_pha,
                    'last_updated': datetime.now().isoformat()
                }
                
                neo_list_csv.append(neo_list)
                neo_list_json.append(neo_dict)
                
            
        except Exception as e:
            print(f"Ошибка при анализе астероидов: {e}")
            continue
        
    return (neo_list_csv, neo_list_json)

# Записываем информацию в json файл с датой в названии
def write_json(data: list[dict]) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"data/neo_data_{today}.json" # создаем название для файла
    
    # Добавляем метаданные
    output_data = {
        "metadata": {
            "date_generated": datetime.now().isoformat(),
            "total_objects": len(data),
            "data_source": "MPC (Minor Planet Center)",
            "description": "Near Earth Objects (NEO) data",
        },
        "neo_objects": data
    }
    
    with open(filename, "w", encoding='utf-8') as file:
        json.dump(output_data, file, indent=4, ensure_ascii=False)

# Записываем информацию в csv с датой в названии
def write_csv(data: list[list]) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"data/neo_data_{today}.csv" # создаем название для файла
    
    with open(filename, "w", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Создаем колонки с дополнительной информацией
        writer.writerow(["# Near Earth Objects Data"])
        writer.writerow([f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([f"# Total objects: {len(data)}"])
        writer.writerow([])  # Пустая строка
        
        # Основные колонки
        writer.writerow(
            (
                "номер",
                "Название", 
                "Обозначение",
                "Перигелий",
                "Афелий",
                "Минимальное расстояние до Земли",
                "Абсолютная магнитуда", 
                "Является NEO",
                "Потенциально опасен",
            )
        )
        
        # Записываем информацию
        writer.writerows(data)

def main():
    # Создаем директорию если нет
    if not os.path.exists("data"):
        os.makedirs("data")
    
    print("Запуск мониторинга околоземных астероидов...")
    print("Получение данных от MPC...")
    
    data_csv, data_json = get_neo()
    
    # Выводим основную статистику
    print(f"Получены данные о {len(data_json)} околоземных объектах")
    
    
    # Записываем данные
    write_csv(data_csv)
    print("Данные сохранены в CSV файл с текущей датой")
    
    write_json(data_json)
    print("Данные сохранены в JSON файл с текущей датой")
    
    # Итоговая статистика
    print(f"\nИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Всего NEO: {len(data_json)}")
    print(f"   Дата обновления: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
if __name__ == "__main__":
    main()