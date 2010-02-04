from google.appengine.ext import db

"""

Models are defined in this module. 

"""


class GeoID(db.Model): 
    #key_name - pretty name
    geo_id = db.IntegerProperty(required=True)
    lat = db.FloatProperty()
    lon = db.FloatProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    
    def coords(self):
      return self.lat, self.lon
