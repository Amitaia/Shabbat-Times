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
TIME_BEFORE_CHECK = 'time_before_check'
TIME_AFTER_CHECK = 'time_after_check'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'

SENSOR_TYPES = {
    'in': ['כניסת שבת','mdi:candle','in'],
    'out': ['צאת שבת', 'mdi:exit-to-app','out'],
    'is_shabbat': ['IN','mdi:candle','is_shabbat'],
    'is_holiday': ['OUT', 'mdi:candle','is_holiday'],
    'parasha': ['פרשת השבוע', 'mdi:book-open-variant','parasha'],
    'hebrew_date': ['תאריך עברי', 'mdi:calendar','hebrew_date'],
    'sunset': ['שקיעת החמה', 'mdi:weather-sunset','sunset'],

}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(GEOID): cv.string,
    vol.Required(LONGITUDE): cv.string,
    vol.Required(GEOID): cv.string,
    vol.Optional(HAVDALAH_MINUTES, default=42): int,
    vol.Optional(TIME_BEFORE_CHECK, default=10): int,
    vol.Optional(TIME_AFTER_CHECK, default=10): int,
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
    time_before = config.get(TIME_BEFORE_CHECK)
    time_after = config.get(TIME_AFTER_CHECK)

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [
                sensor_type.title(), '', 'mdi:flash']

        entities.append(Shabbat_Hagg(sensor_type,geoid,latitude,longitude,havdalah,time_before,time_after))

    add_entities(entities)


# pylint: disable=abstract-method

class Shabbat_Hagg(Entity):
    """Representation of a shabbat and hagg."""

    def __init__(self, sensor_type,geoid,latitude,longitude,havdalah,time_before,time_after):
        """Initialize the sensor."""
        self.type = sensor_type
        self._geoid = geoid
        self._latitude = latitude
        self._longitude = longitude
        self._havdalah = havdalah
        self._time_before = time_before
        self._time_after = time_after
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
        datetoday = datetime.date.today()
        fulltoday = datetime.datetime.today()
        winter = '+02:00','+0200'
        summer = '+03:00','+0300'
        zonetime = '',''
        with urllib.request.urlopen(
            "https://www.hebcal.com/shabbat/?cfg=json&geonameid="+str(self._geoid)+"&m="
            +str(self._havdalah)+"") as url:
            hebcal_decoded = json.loads(url.read().decode())
        if winter[0].__eq__(hebcal_decoded['items'][0]['date'][19:]):
            zonetime = winter
        else:
            zonetime = summer
        if self.type.__eq__('in'):
            self._state = hebcal_decoded['items'][0]['date'][11:16]
        elif self.type.__eq__('out'):
            self._state = hebcal_decoded['items'][3]['date'][11:16]
        elif self.type.__eq__('is_shabbat'):
            is_in = datetime.datetime.strptime(hebcal_decoded['items'][0]['date'].replace(zonetime[0],zonetime[1]), '%Y-%m-%dT%H:%M:%S%z')
            is_out = datetime.datetime.strptime(hebcal_decoded['items'][3]['date'].replace(zonetime[0],zonetime[1]), '%Y-%m-%dT%H:%M:%S%z')
            is_in = is_in - datetime.timedelta(minutes=int(self._time_before))
            is_out = is_out + datetime.timedelta(minutes=int(self._time_after))
            if is_in.replace(tzinfo=None) < fulltoday and is_out.replace(tzinfo=None) > fulltoday :
                self._state = 'True'
            else:
                self._state = 'False'
        elif self.type.__eq__('is_holiday'):
            self._state = hebcal_decoded['items'][3]['date']
        elif self.type.__eq__('parasha'):
            self._state = hebcal_decoded['items'][1]['hebrew'][5:]
        elif self.type.__eq__('hebrew_date'):
            with urllib.request.urlopen(
                "https://www.hebcal.com/converter/?cfg=json&gy="+str(datetoday.year)+"&gm="+str(
                    datetoday.month)+"&gd="+str(datetoday.day)+"&g2h=1") as url:
                sun_date = json.loads(url.read().decode())
                self._state = sun_date['hebrew']
        elif self.type.__eq__('sunset'):
            with urllib.request.urlopen(
                "https://api.sunrise-sunset.org/json?lat="+str(self._latitude)+"&lng="+str(self._longitude)+
                "&date=now&formatted=0") as url:
                sunset = json.loads(url.read().decode())
                sun_date = datetime.datetime.strptime(sunset['results']['sunset'].replace('+00:00','+0000'), '%Y-%m-%dT%H:%M:%S%z')
                sun_date = sun_date.astimezone(pytz.timezone("Asia/Jerusalem"))
                self._state = sun_date.strftime('%H:%M')
