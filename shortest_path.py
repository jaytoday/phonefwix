# calculate the air distance between two given cities
# the map coordinates of each city are contained in a dictionary
# locations obtained from: WWW.ASTRO.COM
# longitude is east/west with zero at Greenwhich/London England
# latitude is north/south with zero at the equator
# tested with Python25     vegseat     10may2007

import math

city_locations = {
'Amarillo': ('35n13', '101w50', 'Texas USA'),
'Austin': ('30n16', '97w45', 'Texas USA'),
'Berlin': ('52n30', '13e22', 'Germany'),
'Boston': ('42n22', '71w04', 'Massachusetts USA'),
'Chicago': ('41n51', '87w39', 'Illinois USA'),
'Delhi': ('28n40', '77e13', 'India'),
'Denver': ('39n44', '104w59', 'Colorado USA'),
'Detroit': ('42n20', '83w03', 'Michigan USA'),
'Jerusalem': ('31n46', '35e14', 'Israel'),
'London': ('51n30', '0w10', 'England'),
'Madrid': ('40n24', '3w41', 'Spain'),
'Melbourne': ('37s49', '144e58', 'Australia'),
'Orlando': ('28n32', '81w23', 'Florida USA'),
'Paris': ('48n52', '2e20', 'France'),
'Reno': ('39n32', '119w49', 'Nevada USA'),
'Salt Lake City': ('40n46', '111w53', 'Utah USA'),
'Seattle': ('47n36', '122w20', 'Washington USA'),
'Tokyo': ('35n42', '139e46', 'Japan')
}

def city_coordinates(city):
    """
    given the coordinates of the city in WWW.ASTRO.COM format
    return the coordinates in radians, negative to the south and west
    """
    if city in city_locations:
        lat1 = city_locations[city][0]
        lng1 = city_locations[city][1]
        if 'n' in lat1:
            hr, mn = lat1.split('n')
            deg = float(hr)# + float(mn)/60
            lat_rad = math.radians(deg)
        elif 's' in lat1:
            hr, mn = lat1.split('s')
            deg = float(hr)# + float(mn)/60
            lat_rad = -math.radians(deg)
        if 'e' in lng1:
            hr, mn = lng1.split('e')
            deg = float(hr)# + float(mn)/60
            lng_rad = math.radians(deg)
        elif 'w' in lng1:
            hr, mn = lng1.split('w')
            deg = float(hr)# + float(mn)/60
            lng_rad = -math.radians(deg)
    else:
        print "city = %s not found" % city
    # coordinates in radians    
    return (lat_rad, lng_rad)

    
def city_distance(city1, city2):
    """
    calculate the distance (air) in miles between 2 cities given their coordinates
    """
    # get coordinates in radians
    lat1, lng1 = city_coordinates(city1)
    lat2, lng2 = city_coordinates(city2)
    # circumference in miles at equator, if you want km, use km value here
    circ = 24830.0  
    a = lng1 - lng2
    if a < 0.0:
        a = -a
    if a > math.pi:
        a = 2.0 * math.pi - a
    angle = math.acos(math.sin(lat2) * math.sin(lat1) + 
        math.cos(lat2) * math.cos(lat1) * math.cos(a))
    distance = circ * angle / (2.0 * math.pi)
    print "Shortest distance between %s and %s is %0.1f miles" % (city1, city2, distance)
    
# mind you these are air miles
city_distance('Detroit', 'Denver')
city_distance('Amarillo', 'Denver')
city_distance('Boston', 'Seattle')
city_distance('Berlin', 'Tokyo')
city_distance('Denver', 'Jerusalem')
city_distance('Detroit', 'Delhi')
city_distance('Detroit', 'Melbourne')

print '-'*60

# these three cities almost line up straight (should add up)
city_distance('Boston', 'Detroit')
city_distance('Detroit', 'Chicago')
city_distance('Boston', 'Chicago')
