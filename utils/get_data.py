from astroquery.mpc import MPC
from astroquery.jplsbdb import SBDB
from datetime import datetime
import logging

from .space_math import *

logger = logging.getLogger(__name__)

# Получаем данные обо всех NEO в данный момент
def get_neo() -> tuple:
    all_asteroids = MPC.query_objects("asteroid") # получаем данные обо всех астероидах
    out_data = []
    
    for asteroid in all_asteroids:
        try:
            perihelion = float(asteroid['perihelion_distance']) # перигелий
            
            if perihelion <= 1.3:  # Значит это NEO
                ast_id = asteroid.get("number")
                if ast_id:
                    ast_id = int(ast_id) if ast_id.isdigit() else None          
                          
                is_pha = asteroid.get('pha', False) # является ли астероид потенциально опасным
                H_mag = float(asteroid['absolute_magnitude'])
                
                phys_data = SBDB.query(ast_id, phys=True).get('physical_parameters') # обращаемся к другой базе данных где может быть диаметр
                if phys_data:
                    albedo = phys_data.get("albedo", 0.15)
                    diameter = phys_data.get("diameter")
                    
                    if diameter:
                        accurate_diameter = True
                    else:
                        # Диаметр по альбедо или по стандартному
                        if albedo and albedo != 0.15:
                            diameter = get_size_by_albedo(albedo, H_mag)
                        else:
                            diameter = get_size_by_h_mag(H_mag)
                        accurate_diameter = False
                else:
                    albedo = 0.15
                    diameter = get_size_by_h_mag(H_mag)
                    accurate_diameter = False
                    
                # все наши данные на 1 астероид
                ast_data = { 
                    "mpc_number": asteroid["number"],
                    "name": asteroid.get("name"),
                    "designation": asteroid.get("designation"),
                    "perihelion_au": perihelion,
                    "aphelion_au": float(asteroid.get("aphelion_distance")),
                    "earth_moid_au": float(asteroid.get("earth_moid")),
                    "is_neo": True,
                    "is_pha": is_pha,
                    "absolute_magnitude": H_mag,
                    "estimated_diameter_km": diameter,
                    "accurate_diameter": accurate_diameter,
                    "albedo": albedo,
                    "last_updated": datetime.now()
                }
                
                out_data.append(ast_data)
                
                logger.info(f"Данные для астероида {asteroid.get('name')} ({asteroid['number']}) были получены!")
                
        except Exception as e:
            logger.error(f"Ошибка при анализе астероидов: {e}")
            continue
        
    return out_data
        
