from astroquery.mpc import MPC
from astroquery.jplsbdb import SBDB
from datetime import datetime
import logging

from utils.space_math import *

logger = logging.Logger()

# Получаем данные обо всех NEO в данный момент
def get_neo() -> tuple:
    all_asteroids = MPC.query_objects("asteroid") # получаем данные обо всех астероидах
    out_data = []
    
    for asteroid in all_asteroids:
        try:
            perihelion = float(asteroid['perihelion_distance']) # перигелий
            
            if perihelion <= 1.3:  # Значит это NEO
                ast_id = asteroid["number"]                
                is_pha = asteroid.get('pha', False) # является ли астероид потенциально опасным
                H_mag = float(asteroid['absolute_magnitude'])
                
                phys_data = SBDB.query(ast_id, phys=True).get('physical_parameters') # обращаемся к другой базе данных где может быть диаметр
                if phys_data:
                    albedo = phys_data.get("albedo")
                    diameter = phys_data.get("diameter")
                    accurate_diameter = True
                    
                    if not diameter and albedo:
                        diameter = get_size_by_albedo(albedo, H_mag) # расчитываем диаметр по альбедо
                    else:
                        accurate_diameter = False
                        diameter = get_size_by_h_mag(H_mag) # диаметр не точен
                                                                
                else:
                    accurate_diameter = False
                    diameter = get_size_by_h_mag(H_mag)
                    
            # все наши данные на 1 астероид
            ast_data = { 
                "number": asteroid["number"],
                "name": asteroid.get("name"),
                "designation": asteroid.get("designation"),
                "perihelion": perihelion,
                "aphelion": asteroid.get("aphelion_distance"),
                "earth_moid": asteroid.get("earth_moid"),
                "is_neo": True,
                "is_pha": is_pha,
                "H_mag": H_mag,
                "diameter": diameter,
                "accurate_diameter": accurate_diameter,
                "last_updated": datetime.now().isoformat()
            }
            
            out_data.append(ast_data)
                
        except Exception as e:
            logger.error(f"Ошибка при анализе астероидов: {e}")
            continue
        
        finally:
            return out_data
        
