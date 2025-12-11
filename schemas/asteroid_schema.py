from pydantic import BaseModel, ConfigDict

class Asteroid(BaseModel):
    mpc_number: int
    name: str
    designation: str
    perihelion_au: float
    aphelion_au: float
    earth_moid_au: float
    absolute_magnitude: float
    estimated_diameter_km: float
    accurate_diameter: bool
    albedo: float
    is_neo: bool
    is_pha: bool