import os
import logging
import wsgiref.handlers
from xml.dom import minidom

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.api import urlfetch

from memoize import memoize

BASE_URL = 'http://' + os.environ['HTTP_HOST']
GOOGLE_API_KEY = 'ABQIAAAAp9MeKRzg4enDIIhNtuGobxQJd39p99H69tZXJ0vV-96GQICKVxRRV-KOwlUhjLK88byEptmQ8RfbTA'
# zipcodes http://www.census.gov/tiger/tms/gazetteer/zips.txt
# http://api.fwix.com/general/geos.format
FWIX_FETCH_URL = 'http://api.fwix.com/fetch/%s.json?'
FWIX_GEOS_URL = 'http://api.fwix.com/general/geos.json?'
SUMMARY_MIN = 80

NEWS_TYPES = {'recent': 'breaking', 'top': "today's most popular"}
DEFAULT_NEWS_TYPE = 'recent'

class IndexPage(webapp.RequestHandler):
  def get(self):
    context = {}
    html_response(self, 'index.html', context)


class Phone(webapp.RequestHandler):
    """
    Initial user greeting.  Plays the welcome audio file then reads the
    "enter zip code" message.  The Play and Say are wrapped in a Gather
    verb to collect the 5 digit zip code from the caller.  The Gather
    will post the results to /weather
    """
    def get(self):
        self.post()
    
    def post(self):
        if len(self.request.path.split('phone/')) > 1:
          is_news_type = True
          news_type = self.request.path.split('phone/')[1]
        else:
          is_news_type = False
          news_type = DEFAULT_NEWS_TYPE
        news_types = NEWS_TYPES.keys()
        news_types.remove(news_type)
        other_news_type = news_types[0]
        
        # but what if they press the pound key?
        if is_news_type and not self.request.get('Digits'):
          news_type, other_news_type = other_news_type, news_type 
        
        self.context = {
            'postprefix': BASE_URL,
            'is_news_type': is_news_type,
            'news_type': news_type,
            'news_type_description': NEWS_TYPES[news_type],
            'other_news_type_description': NEWS_TYPES[other_news_type]
        }
        # get news if Digits are sent 
        if self.request.get('Digits'): return self.get_news()
        
        xml_response(self, 'gather.xml', self.context)


    
    """
    Accepts input digits from the caller, fetches the news from an
    external site, and reads back the news to the caller
    """


    def get_news(self):
        zipcode = self.request.get('Digits')
        # strip off extra digits and keys from the Digits we got back
        zipcode = zipcode.replace('#', '').replace('*', '')[:5]
        try:
          place, (lat, lng) = get_coordinates_for_zipcode(zipcode)
          logging.info('Geo Data: %s: %s, %s' % (place, str(lat), str(lng)) )
          geo_id = get_closest_geo_id(lat, lng)
          logging.info('Geo ID: %d' % geo_id)
          fwixxml = self.fetchfwixdata(geo_id, 
          fetch_type=self.context['news_type'])
        except FailError:
          self._error("Error fetching fwix data. Good Bye.")
          return
        try:
            self.context['results'] = self._parsefwixjson(fwixxml)
            self.context['place'] = place.split(str(zipcode))[0]
            xml_response(self, 'fwix.xml', self.context)
        except FailError:
            self._error("Error parsing fwixdata. Good Bye.")


    def fetchfwixdata(self, geo_id, fetch_type='recent'): # or top
        #import random
        #geo_id = random.sample(range(50),1)[0]
        fetch_url = FWIX_FETCH_URL % fetch_type
        args = {
        'geo_id' : geo_id
        }
        import urllib
        args_enc = args_enc = urllib.urlencode(args)
        result = urlfetch.fetch(fetch_url + args_enc, method='GET')
        if result.status_code != 200:
            return None
        return result.content

        
    def _parsefwixjson(self, json):
        logging.info('Fwix JSON: %s' % json)
        from django.utils import simplejson
        from encoding import htmlencode
        fwix_dict = simplejson.loads(json)
        results = []

        for item in fwix_dict['result']:
           if len(item['summary']) < SUMMARY_MIN:
            continue
           item['title'] = htmlencode(item['title'].replace('&','and'))
           item['summary'] = htmlencode(item['summary'].split('-')[-1].replace('&','and'))
           # same for summary...
           results.append(item)
        return results

    def _error(self, msg, redirecturl=None):
        context = {
            'msg': msg,
            'redirecturl': redirecturl
        }
        xml_response(self, 'error.xml', context)
            

class FailError(Exception):
  def __init__(self, error_msg):
    logging.warning(error_msg)
    
    
class UpdateGeoIds(webapp.RequestHandler):
  def get(self):
    from models import GeoID
    response = urlfetch.fetch(FWIX_GEOS_URL)
    from django.utils import simplejson
    response_dict = simplejson.loads(response.content)
    entities = []
    for result in response_dict['result']:
      entity = GeoID.get_by_key_name(result['pretty'])
      if entity: continue
      entity = GeoID(key_name = result['pretty'],
      geo_id = int(result['id']),
      lat = float(result['lat']),
      lon = float(result['lon']))
      entities.append(entity)
    db.put(entities)
    
    

@memoize()
def get_coordinates_for_zipcode(zipcode):
    from geopy import geocoders  
    g = geocoders.Google(GOOGLE_API_KEY)
    place, (lat, lng) = g.geocode(zipcode)
    return place, (lat, lng)

@memoize()
def get_closest_geo_id(lat, lng):
    from geopy import distance as geopy_distance
    from models import GeoID
    geo_ids = GeoID.all().fetch(1000)
    distances = []
    for geo_id in geo_ids:
      distances.append(
      {'distance': int(geopy_distance.distance(
      geo_id.coords(), (lat, lng)).miles),
       'geo_id': geo_id.geo_id,
       'place': geo_id.key().name()
      })
    distances = sort_by_key(distances, 'distance', reverse=False)
    return distances[0]['geo_id']

   

def sort_by_key(seq,attr, reverse=True):
    intermed = [ (seq[i][attr], i, seq[i]) for i in xrange(len(seq)) ]
    intermed.sort()
    if reverse: intermed.reverse() # ranked from greatest to least
    return [ tup[-1] for tup in intermed ]
       
"""

Rendering Methods

"""   
   

def xml_response(handler, page, context=None):
    """
    Renders an XML response using a provided template page and values
    """
    path = os.path.join(os.path.dirname(__file__), page)
    handler.response.headers["Content-Type"] = "text/xml"
    handler.response.out.write(template.render(path, context))
    

def html_response(handler, page, context=None):
    """
    Renders an XML response using a provided template page and values
    """
    path = os.path.join(os.path.dirname(__file__), page)
    handler.response.headers["Content-Type"] = "text/html"
    handler.response.out.write(template.render(path, context))
   
    
def main():
    application = webapp.WSGIApplication([ \
        ('/', IndexPage),
        
        ('/phone', Phone),
        ('/phone/recent', Phone),
        ('/phone/top', Phone),
        
        ('/update_geoids', UpdateGeoIds)
        ],
        debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
