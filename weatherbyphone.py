import os
import wsgiref.handlers
from xml.dom import minidom

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.api import urlfetch

BASE_URL = 'http://' + os.environ['HTTP_HOST'] + "/"
WEATHER_API_URL = "http://weather.yahooapis.com/forecastrss?p="
WEATHER_API_NS = "http://xml.weather.yahoo.com/ns/rss/1.0"

# zipcodes http://www.census.gov/tiger/tms/gazetteer/zips.txt
# http://api.fwix.com/general/geos.format
FWIX_RECENT_URL = 'http://api.fwix.com/fetch/recent.json?'

class NewsPage(webapp.RequestHandler):
    """
    Accepts input digits from the caller, fetches the news from an
    external site, and reads back the news to the caller
    """
    def get(self):
        self.post()
    
    def _error(self, msg, redirecturl=None):
        templatevalues = {
            'msg': msg,
            'redirecturl': redirecturl
        }
        xml_response(self, 'error.xml', templatevalues)
    
    def _fetch(self, zipcode):
        url = FWIX_RECENT_URL
        import random
        geo_id = random.sample(range(50),1)[0]
        args = {
        'geo_id' : geo_id
        }
        import urllib
        args_enc = args_enc = urllib.urlencode(args)
        result = urlfetch.fetch(url + args_enc, method='GET')
        if result.status_code != 200:
            return None
        return result.content
    
    def _parse(self, xml):
        dom = minidom.parseString(xml)
        conditions = dom.getElementsByTagNameNS(WEATHER_API_NS,
            'condition')[0]
        location = dom.getElementsByTagNameNS(WEATHER_API_NS,
            'location')[0]
        return {
            'location': '%s, %s' % (location.getAttribute('city'),
                location.getAttribute('region')),
            'conditions': conditions.getAttribute('text'),
            'temp': conditions.getAttribute('temp')
        }
        
    def _parsefwixjson(self, json):
        from django.utils import simplejson
        from encoding import htmlencode
        obj = simplejson.loads(json)
        for item in obj['result']:
         item['title'] = htmlencode(item['title'])
         # same for summary...
        return obj
        
    # @start snippet
    def post(self):
        zipcode = self.request.get('Digits')
        if not zipcode:
            self._error("Invalid zip code.", BASE_URL)
            return
        
        # strip off extra digits and keys from the Digits we got back
        zipcode = zipcode.replace('#', '').replace('*', '')[:5]
        
        try:
          fwixxml = self._fetch(zipcode)
        except:
            self._error("Error fetching fwix data. Good Bye.")
            return
        try:
            json_response(self, 'fwix.xml', self._parsefwixjson(fwixxml))
        except:
            self._error("Error parsing fwixdata. Good Bye.")
        # @end snippet


def json_response(handler, page, templatevalues=None):
    """
    Renders an XML response using a provided template page and values
    """
    path = os.path.join(os.path.dirname(__file__), page)
    handler.response.headers["Content-Type"] = "text/xml"
    handler.response.out.write(template.render(path, templatevalues))


# @start snippet
def xml_response(handler, page, templatevalues=None):
    """
    Renders an XML response using a provided template page and values
    """
    path = os.path.join(os.path.dirname(__file__), page)
    handler.response.headers["Content-Type"] = "text/xml"
    handler.response.out.write(template.render(path, templatevalues))

class GatherPage(webapp.RequestHandler):
    """
    Initial user greeting.  Plays the welcome audio file then reads the
    "enter zip code" message.  The Play and Say are wrapped in a Gather
    verb to collect the 5 digit zip code from the caller.  The Gather
    will post the results to /weather
    """
    def get(self):
        self.post()
    
    def post(self):
        templatevalues = {
            'postprefix': BASE_URL,
        }
        xml_response(self, 'gather.xml', templatevalues)
# @end snippet

def main():
	# @start snippet
    application = webapp.WSGIApplication([ \
        ('/', GatherPage),
        ('/news', NewsPage)],
        debug=True)
    # @end snippet
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
