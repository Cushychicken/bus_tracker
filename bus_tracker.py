import requests
import logging
from logging.handlers import TimedRotatingFileHandler  
import time
import RPi.GPIO as gpio
from bs4 import BeautifulSoup
from math import radians, cos, sin, asin, sqrt

def km_to_miles(km):
    """
    Because this is AMERICA, dammit
    """
    return 0.6214 * km

def haversine(coord1, coord2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [coord1[1], coord1[0], coord2[1], coord2[0]])

    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
        
    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km_to_miles(km) 

# Known locations
DAVIS_SQUARE = (42.396589, -71.122363)
UNION_SQUARE = (42.380298, -71.096592)
HOME = (42.387048, -71.114295)

distances = {
    'davis_to_union': haversine(DAVIS_SQUARE, UNION_SQUARE),
    'davis_to_home' : haversine(DAVIS_SQUARE, HOME),
    'union_to_home' : haversine(UNION_SQUARE, HOME)
    }

def bus_locs(dist, logger):
    DAVIS_SQUARE = (42.396589, -71.122363)
    UNION_SQUARE = (42.380298, -71.096592)
    HOME = (42.387048, -71.114295)

    BUS_URL = 'http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=mbta&t=0'
    r = requests.get(BUS_URL)
    logger.debug('Request info: %s', r)
    status = {
        'inbound' : False,
        'outbound': False  
    }

    soup = BeautifulSoup(r.text)
    for loc in soup.findAll('vehicle', routetag='87'):
        b = (float(loc.attrs['lat']), float(loc.attrs['lon']))
        logger.debug('Bus %s Position: %s', loc.attrs['id'], b)

        records = {
            'home' : str(haversine(b, HOME)),
            'union_sq' : str(haversine(b, UNION_SQUARE)),
            'davis_sq' : str(haversine(b, DAVIS_SQUARE)),
            'drxn' : loc.attrs['dirtag']
        }

        if (
            haversine(b, UNION_SQUARE) < dist['union_to_home'] and 
            haversine(b, HOME) < dist['union_to_home'] and 
            loc.attrs['dirtag'].startswith('87_0')
           ):
            status['outbound'] = True
        if (
            haversine(b, DAVIS_SQUARE) < dist['davis_to_home'] and 
            haversine(b, HOME) < dist['davis_to_home'] and 
            loc.attrs['dirtag'].startswith('87_1')
           ):
            status['inbound'] = True

        logger.debug('Bus %s Dist: %s Status: %s', loc.attrs['id'], records, status) 

    return status

        
if __name__ == '__main__':

    # Configuring logging information
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    handler = TimedRotatingFileHandler('tracker.log', when='midnight')
    handle2 = TimedRotatingFileHandler('businfo.log', when='midnight')
    handler.setLevel(logging.INFO)
    handle2.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handle2.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(handle2)
    logger.info('Tracker starting') 

    RED_LED = 25
    BLU_LED = 24

    # Configuring all them GPIO fellers
    logger.info('Starting GPIO setup')
    gpio.setwarnings(False) # We're all adults here, right?
    gpio.setmode(gpio.BCM)
    gpio.setup(RED_LED, gpio.OUT)
    gpio.setup(BLU_LED, gpio.OUT)
    logger.info('GPIO setup complete')

    logger.info('Entering bus tracking loop...')
    while True:
        logger.info('Updating bus info')
        status = bus_locs(distances, logger)
        bus_status =  dict(status.iteritems())
        logger.info('Updating LEDs')
        logger.debug('Led Status : %s', bus_status)
        gpio.output(RED_LED, not status['inbound'])
        gpio.output(BLU_LED, not status['outbound'])
        logger.info('LEDs updated, sleeping...') 
        time.sleep(60)
        logger.info('Sleep complete')

