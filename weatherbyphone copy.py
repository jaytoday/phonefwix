import os
import wsgiref.handlers
from xml.dom import minidom

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.api import urlfetch

BASE_URL = "http://weatherbyphone.appspot.com/"
WEATHER_API_URL = "http://weather.yahooapis.com/forecastrss?p="
WEATHER_API_NS = "http://xml.weather.yahoo.com/ns/rss/1.0"

# zipcodes http://www.census.gov/tiger/tms/gazetteer/zips.txt
# http://api.fwix.com/general/geos.format
FWIX_RECENT_URL = 'http://api.fwix.com/fetch/recent.json'

class WeatherPage(webapp.RequestHandler):
    """
    Accepts input digits from the caller, fetches the weather from an
    external site, and reads back the weather to the caller
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
        url = WEATHER_API_URL + zipcode
        result = urlfetch.fetch(url)
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
    # @start snippet
    def post(self):
        zipcode = self.request.get('Digits')
        if not zipcode:
            self._error("Invalid zip code.", BASE_URL)
            return
        
        # strip off extra digits and keys from the Digits we got back
        zipcode = zipcode.replace('#', '').replace('*', '')[:5]
        
        weatherxml = self._fetch(zipcode)
        if not weatherxml:
            self._error("Error fetching weather. Good Bye.")
            return
        
        try:
            xml_response(self, 'weather.xml', self._parse(weatherxml))
        except:
            self._error("Error parsing weather. Good Bye.")
        # @end snippet

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
        ('/weather', WeatherPage)],
        debug=True)
    # @end snippet
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
