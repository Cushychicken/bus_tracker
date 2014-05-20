import requests
import time
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

def bus_locs(dist):
    DAVIS_SQUARE = (42.396589, -71.122363)
    UNION_SQUARE = (42.380298, -71.096592)
    HOME = (42.387048, -71.114295)

    BUS_URL = 'http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=mbta&t=0'
    r = requests.get(BUS_URL)

    status = {
        'inbound' : False,
        'outbound': False  
    }

    soup = BeautifulSoup(r.text)
    for loc in soup.findAll('vehicle', routetag='87'):
        b = (float(loc.attrs['lat']), float(loc.attrs['lon']))
        print 'Distance to Davis:', str(haversine(b, DAVIS_SQUARE))
        print 'Distance to Union:', str(haversine(b, UNION_SQUARE))
        print 'Distance to Home :', str(haversine(b, HOME))
        print 'Bus direction    :', loc.attrs['dirtag']
        print 'Bus ID           :', loc.attrs['id']
        print

        if haversine(b, UNION_SQUARE) < dist['union_to_home'] and loc.attrs == '87_0_var1':
            status['outbound'] = True
        if haversine(b, DAVIS_SQUARE) < dist['davis_to_home'] and loc.attrs == '87_1_var1':
            status['inbound'] = True

    return status

        
if __name__ == '__main__':
    while True:
        status = bus_locs(distances)
        for k,v in status.iteritems():
            print k,v
        print
        time.sleep(60)


