import logging
import time
from typing import List, Dict, Any, Optional
import requests
from astroquery.jplsbdb import SBDB
from .space_math import get_size_by_albedo, get_size_by_h_mag

logger = logging.getLogger(__name__)


class NASASBDBClient:    
    def get_asteroids(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetches asteroid data using a hybrid approach.
        1. Uses SBDB Query API to get a list of PHA designations.
        2. Uses astroquery.jplsbdb to get detailed data for each.
        """
        # --- STEP 1: Get list of Potentially Hazardous Asteroids (PHAs) ---
        logger.info("Fetching list of Potentially Hazardous Asteroids (PHAs) from NASA SBDB Query API...")

        query_url = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
        params = {
            'fields': 'pdes',  # We only need the primary designation
            'sb-group': 'pha', 
            'limit': limit or 3000  # PHAs are around ~2,000-3,000 objects
        }
        
        try:
            response = requests.get(query_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data:
                logger.error("No 'data' key in SBDB Query API response.")
                return []
                
            # Extract just the designations (pdes) from the response
            designations = [item[0] for item in data['data']]
            
            logger.info(f"SBDB Query API returned {len(designations)} PHAs.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch asteroid list from SBDB Query API: {e}")
            return []
        
        # --- STEP 2: Get detailed data for each asteroid using astroquery ---
        logger.info(f"Fetching detailed data for {len(designations)} PHAs using astroquery...")
        
        asteroids = []
        failed_designations = []
        
        for i, des in enumerate(designations):
            try:
                logger.debug(f"Processing {i+1}/{len(designations)}: {des}")
                
                result = SBDB.query(
                    des,
                    phys=True,           # Gets H-magnitude, albedo, diameter
                    full_precision=True  # Gets properly formatted numbers (e.g., 1.13, not 1.1)
                )
                
                # Debug: log what we actually received
                if i < 5:  # Log first 5 for debugging
                    logger.debug(f"Raw SBDB response for {des}: {result.keys()}")
                
                # --- Extract and transform the data for your AsteroidModel ---
                asteroid_info = self._parse_sbdb_to_model(result, des)
                
                if asteroid_info:
                    asteroids.append(asteroid_info)
                    if len(asteroids) % 10 == 0:  # More frequent updates for PHAs
                        logger.info(f"  Progress: {len(asteroids)}/{len(designations)} PHAs processed.")
                else:
                    failed_designations.append(des)
                    logger.warning(f"Failed to parse data for {des}")
                
                # RESPECTFUL DELAY - Critical to avoid being blocked
                time.sleep(2.0)  # Increased delay for more comprehensive queries
                
            except Exception as e:
                logger.warning(f"Failed to get data for designation '{des}': {e}")
                failed_designations.append(des)
                continue
        
        if failed_designations:
            logger.warning(f"Failed to fetch details for {len(failed_designations)} designations.")
        
        logger.info(f"Successfully fetched detailed data for {len(asteroids)} PHAs.")
        return asteroids

    def _parse_sbdb_to_model(self, sbdb_data: Dict, designation: str) -> Optional[Dict[str, Any]]:
        """
        Parses the raw SBDB result dictionary into your AsteroidModel format.
        Correctly handles astropy.units.Quantity objects.
        """
        def _extract_value(value, default=None):
            """
            Safely extracts a numeric value from various possible inputs:
            - Direct int/float
            - astropy.units.Quantity object (has .value attribute)
            - Dict with 'value' key (from JSON conversion)
            - String with units
            """
            if value is None:
                return default
            
            # Case 1: Already a number
            if isinstance(value, (int, float)):
                return float(value)
            
            # Case 2: astropy.units.Quantity object (from original response)
            if hasattr(value, 'value'):
                try:
                    return float(value.value)
                except (TypeError, ValueError):
                    pass
            
            # Case 3: Dictionary from JSON conversion
            if isinstance(value, dict) and 'value' in value:
                try:
                    return float(value['value'])
                except (TypeError, ValueError):
                    pass
            
            # Case 4: String - use original cleaning logic
            if isinstance(value, str):
                import re
                cleaned = value.strip()
                # Remove uncertainty notation
                cleaned = re.sub(r'[±~].*', '', cleaned)
                # Remove parentheses and brackets
                cleaned = re.sub(r'\(.*\)|\[.*\]', '', cleaned)
                # Remove units
                unit_pattern = r'\s*(km|m|s|mag|AU|au|ly|pc|°|deg)\s*'
                cleaned = re.sub(unit_pattern, '', cleaned, flags=re.IGNORECASE)
                # Remove remaining non-numeric characters
                cleaned = re.sub(r'[^-\d\.\+eE]', '', cleaned)
                if cleaned:
                    try:
                        return float(cleaned)
                    except ValueError:
                        pass
            
            return default

        try:
            obj = sbdb_data.get('object', {})
            orbit = sbdb_data.get('orbit', {})
            phys_par = sbdb_data.get('phys_par', {})
            
            # --- Basic Identification ---
            fullname = obj.get('fullname', '')
            name = None
            if fullname:
                parts = fullname.split('(')
                if len(parts) > 1:
                    name_part = parts[0].strip()
                    if name_part and not name_part.replace(' ', '').isdigit():
                        name = name_part
            
            # --- Orbital Parameters ---
            elements = orbit.get('elements', {})
            
            # CORRECTED: Extract from Quantity objects
            perihelion_au = _extract_value(elements.get('q'))
            aphelion_au = _extract_value(elements.get('ad'))
            
            # Earth MOID
            earth_moid_au = _extract_value(orbit.get('moid_earth'))
            if earth_moid_au is None:
                earth_moid_au = _extract_value(orbit.get('moid'))
            
            # --- Physical Parameters ---
            h_mag = _extract_value(phys_par.get('H'))
            
            # Use default if H is missing but don't skip
            if h_mag is None:
                h_mag = 18.0
                logger.warning(f"Asteroid {designation} missing H magnitude. Using default H={h_mag}")
            
            # Albedo and diameter - handle Quantity objects
            albedo = _extract_value(phys_par.get('albedo'))
            diameter_km = _extract_value(phys_par.get('diameter'))
            
            # Determine if diameter is accurate
            accurate_diameter = phys_par.get('diameter') is not None and diameter_km is not None and diameter_km > 0
            
            # Calculate diameter if not provided
            if not diameter_km or diameter_km <= 0:
                if albedo and albedo > 0:
                    try:
                        diameter_km = get_size_by_albedo(albedo, h_mag)
                    except ValueError:
                        diameter_km = get_size_by_h_mag(h_mag)
                        albedo = 0.15
                else:
                    diameter_km = get_size_by_h_mag(h_mag)
                    albedo = 0.15
                accurate_diameter = False
            
            # Ensure albedo has a valid value
            if not albedo or albedo <= 0:
                albedo = 0.15
            
            # --- Classification ---
            orbit_class_info = obj.get('orbit_class', {})
            orbit_class = orbit_class_info.get('name', '') if orbit_class_info else ''
            
            # --- Compile the data dictionary ---
            asteroid_dict = {
                'designation': designation,
                'name': name,
                'perihelion_au': perihelion_au,
                'aphelion_au': aphelion_au,
                'earth_moid_au': earth_moid_au,
                'absolute_magnitude': h_mag,
                'estimated_diameter_km': diameter_km,
                'accurate_diameter': accurate_diameter,
                'albedo': albedo,
                'orbit_class': orbit_class,
                'orbit_id': orbit.get('orbit_id'),
            }
            
            logger.debug(f"Parsed {designation}: H={h_mag}, diam={diameter_km}, peri={perihelion_au}")
            return asteroid_dict
            
        except Exception as e:
            logger.error(f"Error parsing SBDB data for {designation}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None