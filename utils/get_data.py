from astroquery.mpc import MPC
from astroquery.jplsbdb import SBDB
import logging

from .space_math import *

logger = logging.getLogger(__name__)

def get_neo() -> list:
    try:
        all_asteroids = MPC.query_objects("asteroid")
    except Exception as e:
        logger.error(f"Ошибка при запросе к MPC: {e}")
        return []
    
    out_data = []
    
    for asteroid in all_asteroids:
        try:
            perihelion = float(asteroid['perihelion_distance'])
            
            if perihelion <= 1.3:
                ast_id = asteroid.get("number")
                
                # Преобразование строки 'Y'/'N' в boolean
                pha_value = asteroid.get('pha', False)
                if isinstance(pha_value, str):
                    is_pha = pha_value.upper() == 'Y'
                else:
                    is_pha = bool(pha_value)
                
                H_mag = float(asteroid['absolute_magnitude'])
                
                name = asteroid.get('name')
                if not name or name == 'None':
                    name = f"Unknown_{asteroid.get('number')}"
                
                # Обработка физических данных с обработкой исключений
                phys_data = None
                try:
                    if ast_id:
                        phys_data = SBDB.query(ast_id, phys=True).get('physical_parameters')
                except Exception as e:
                    logger.warning(f"Не удалось получить данные SBDB для {ast_id}: {e}")
                    phys_data = None
                
                if phys_data:
                    albedo = phys_data.get("albedo", 0.15)
                    diameter = phys_data.get("diameter")
                    
                    if albedo is None or albedo <= 0:
                        albedo = 0.15
                    
                    if diameter:
                        accurate_diameter = True
                    else:
                        if albedo and albedo > 0:
                            try:
                                diameter = get_size_by_albedo(albedo, H_mag)
                            except ValueError:
                                diameter = get_size_by_h_mag(H_mag)
                                albedo = 0.15
                        else:
                            diameter = get_size_by_h_mag(H_mag)
                            albedo = 0.15
                        accurate_diameter = False
                else:
                    albedo = 0.15
                    diameter = get_size_by_h_mag(H_mag)
                    accurate_diameter = False
                
                # Получение дополнительных полей
                aphelion = asteroid.get("aphelion_distance")
                earth_moid = asteroid.get("earth_moid")
                
                ast_data = {
                    "mpc_number": ast_id,
                    "name": name,
                    "designation": asteroid.get("designation"),
                    "perihelion_au": perihelion,
                    "aphelion_au": float(aphelion) if aphelion else None,
                    "earth_moid_au": float(earth_moid) if earth_moid else None,
                    "is_neo": True,
                    "is_pha": is_pha,
                    "absolute_magnitude": H_mag,
                    "estimated_diameter_km": diameter,
                    "accurate_diameter": accurate_diameter,
                    "albedo": albedo,
                }
                
                out_data.append(ast_data)
                
                logger.info(f"Данные для астероида {name} ({ast_id}) были получены!")
                
        except Exception as e:
            logger.error(f"Ошибка при анализе астероида: {e}")
            continue
        
    return out_data
