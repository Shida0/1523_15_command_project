import logging
from utils import NASASBDBClient

logger = logging.getLogger(__name__)

asteroids = NASASBDBClient().get_asteroids(limit = 100)
print(asteroids)