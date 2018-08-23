import logging
import urllib
import json
import datetime
import pytz
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_SCAN_INTERVAL, CONF_RESOURCES)
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(seconds=60)

SENSOR_PREFIX = 'Shabbat '
GEOID = 'geoid'
HAVDALAH_MINUTES = 'havdalah_calc'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'

SENSOR_TYPES = {
    'in': ['כניסת שבת','mdi:candle','in'],
    'out': ['צאת שבת', 'mdi:exit-to-app','out'],
    'in_auto': ['IN','mdi:candle','in_auto'],
    'out_auto': ['OUT', 'mdi:exit-to-app','out_auto'],
    'parasha': ['פרשת השבוע', 'mdi:book-open-variant','parasha'],
    'hebrew_date': ['תאריך עברי', 'mdi:calendar','hebrew_date'],
    'sunset': ['שקיעת החמה', 'mdi:weather-sunset','sunset'],

}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(GEOID): cv.string,
    vol.Required(LONGITUDE): cv.string,
    vol.Required(GEOID): cv.string,
    vol.Optional(HAVDALAH_MINUTES, default=42): int,
    vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the shabbat config sensors."""
    havdalah = config.get(HAVDALAH_MINUTES)
    geoid = config.get(GEOID)
    latitude = config.get(LATITUDE)
    longitude = config.get(LONGITUDE)

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [
                sensor_type.title(), '', 'mdi:flash']

        entities.append(Shabbat_Hagg(sensor_type,geoid,latitude,longitude,havdalah))

    add_entities(entities)


# pylint: disable=abstract-method

class Shabbat_Hagg(Entity):
    """Representation of a shabbat and hagg."""

    def __init__(self, sensor_type,geoid,latitude,longitude,havdalah):
        """Initialize the sensor."""
        self.type = sensor_type
        self._geoid = geoid
        self._latitude = latitude
        self._longitude = longitude
        self._havdalah = havdalah
        self._name = SENSOR_PREFIX + SENSOR_TYPES[self.type][2]
        self._friendly_name = SENSOR_TYPES[self.type][0]
        self._icon = SENSOR_TYPES[self.type][1]
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name
    
    @property
    def friendly_name(self):
        """Return the name of the sensor."""
        return self._friendly_name
    
    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
        
    @Throttle(SCAN_INTERVAL)
    def update(self):
        """update our sensor state."""
        today = datetime.date.today()
        with urllib.request.urlopen(
            "https://www.hebcal.com/shabbat/?cfg=json&geonameid="+str(self._geoid)+"&m="
            +str(self._havdalah)+"") as url:
            hebcal_decoded = json.loads(url.read().decode())
        if self.type == 'in':
            self._state = hebcal_decoded['items'][0]['date'][11:16]
        elif self.type == 'out':
            self._state = hebcal_decoded['items'][2]['date'][11:16]
        elif self.type == 'in_auto':
            self._state = hebcal_decoded['items'][0]['date']
        elif self.type == 'out_auto':
            self._state = hebcal_decoded['items'][2]['date']
        elif self.type == 'parasha':
            self._state = hebcal_decoded['items'][1]['hebrew'][5:]
        elif self.type == 'hebrew_date':
            with urllib.request.urlopen(
                "https://www.hebcal.com/converter/?cfg=json&gy="+str(today.year)+"&gm="+str(
                    today.month)+"&gd="+str(today.day)+"&g2h=1") as url:
                sun_date = json.loads(url.read().decode())
                self._state = sun_date['hebrew']
        elif self.type == 'sunset':
            with urllib.request.urlopen(
                "https://api.sunrise-sunset.org/json?lat="+str(self._latitude)+"&lng="+str(self._longitude)+
                "&date=now&formatted=0") as url:
                sunset = json.loads(url.read().decode())
                sun_date = datetime.datetime.strptime(sunset['results']['sunset'].replace('+00:00','+0000'), '%Y-%m-%dT%H:%M:%S%z')
                sun_date = sun_date.astimezone(pytz.timezone("Asia/Jerusalem"))
                self._state = sun_date.strftime('%H:%M')
