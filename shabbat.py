"""
Platform to get Shabbath Times And Shabbath information for Home Assistant.

Document will come soon...
"""
import logging
import urllib
import json
import codecs
import pathlib
import datetime
import time
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, CONF_RESOURCES)
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

SENSOR_PREFIX = 'Shabbat '
HAVDALAH_MINUTES = 'havdalah_calc'
TIME_BEFORE_CHECK = 'time_before_check'
TIME_AFTER_CHECK = 'time_after_check'

SENSOR_TYPES = {
    'in': ['כניסת שבת', 'mdi:candle', 'in'],
    'out': ['צאת שבת', 'mdi:exit-to-app', 'out'],
    'is_shabbat': ['IN', 'mdi:candle', 'is_shabbat'],
    'parasha': ['פרשת השבוע', 'mdi:book-open-variant', 'parasha'],
    'hebrew_date': ['תאריך עברי', 'mdi:calendar', 'hebrew_date'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LATITUDE): cv.latitude,
    vol.Optional(CONF_LONGITUDE): cv.longitude,
    vol.Optional(HAVDALAH_MINUTES, default=42): int,
    vol.Optional(TIME_BEFORE_CHECK, default=10): int,
    vol.Optional(TIME_AFTER_CHECK, default=10): int,
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
    """Set up the shabbat config sensors."""
    havdalah = config.get(HAVDALAH_MINUTES)
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    time_before = config.get(TIME_BEFORE_CHECK)
    time_after = config.get(TIME_AFTER_CHECK)
    
    if None in (latitude, longitude):
        _LOGGER.error("Latitude or longitude not set in Home Assistant config")
        return
    
    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()
        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [
                sensor_type.title(), '', 'mdi:flash']
        entities.append(Shabbat(hass, sensor_type, hass.config.time_zone, latitude, longitude,
                                havdalah, time_before, time_after))
    async_add_entities(entities, True)

class Shabbat(Entity):
    """Create shabbat sensor."""

    shabbat_db = None
    hebrew_date_db = None
    shabbatin = None
    shabbatout = None
    file_time_stamp = None
    friday = None
    saturday = None
    config_path = None
    
    def __init__(self, hass, sensor_type, timezone, latitude, longitude,
                 havdalah, time_before, time_after):
        """Initialize the sensor."""
        self.type = sensor_type
        self._latitude = latitude
        self._longitude = longitude
        self._timezone = timezone
        self._havdalah = havdalah
        self._time_before = time_before
        self._time_after = time_after
        self.config_path = hass.config.path()+"/custom_components/sensor/"
        self._friendly_name = SENSOR_TYPES[self.type][0]
        self.update_db()
        self._state = None
        self.get_full_time_in()
        self.get_full_time_out()
        
        #_LOGGER.debug("Sensor %s initialized", self.type)

    @property
    def name(self):
        """Return the name of the sensor."""
        return SENSOR_PREFIX + SENSOR_TYPES[self.type][2]

    @property
    def friendly_name(self):
        """Return the name of the sensor."""
        return self._friendly_name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return SENSOR_TYPES[self.type][1]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    #@Throttle(SCAN_INTERVAL)
    async def async_update(self):
        """Update our sensor state."""
        self.update_db()
        if self.type.__eq__('in'):
            self._state = self.get_time_in()
        elif self.type.__eq__('out'):
            self._state = self.get_time_out()
        elif self.type.__eq__('is_shabbat'):
            self._state = self.is_shabbat()
        elif self.type.__eq__('parasha'):
            self._state = self.get_parasha()
        elif self.type.__eq__('hebrew_date'):
            self._state = self.get_hebrew_date()

    def create_db_file(self):
        """Create the json db."""
        self.set_days()
        with urllib.request.urlopen(
            "https://www.hebcal.com/hebcal/?v=1&cfg=fc&start="
            + str(self.friday) + "&end=" + str(self.saturday)
            + "&ss=on&c=on&geo=pos&latitude=" + str(self._latitude)
            + "&longitude=" + str(self._longitude)
            + "&tzid=" + str(self._timezone)
            + "&m=" + str(self._havdalah) + "&s=on"
        ) as shabbat_url:
            data = json.loads(shabbat_url.read().decode())
        with codecs.open(self.config_path+'shabbat_data.json', 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, skipkeys=False, ensure_ascii=False, indent=4, separators=None, default=None,
                      sort_keys=True)
        with urllib.request.urlopen(
            "https://www.hebcal.com/converter/?cfg=json&gy="
            + str(datetime.date.today().year) + "&gm=" + str(datetime.date.today().month)
            + "&gd=" + str(datetime.date.today().day) + "&g2h=1"
        ) as heb_url:
            heb_date = json.loads(heb_url.read().decode())
        with codecs.open(self.config_path+'hebdate_data.json', 'w', encoding='utf-8') as outfile:
            json.dump(heb_date, outfile, skipkeys=False, ensure_ascii=False, indent=4, separators=None, default=None,
                      sort_keys=True)

    def update_db(self):
        """Update the db."""
        if self.file_time_stamp is None or self.file_time_stamp != datetime.date.today() : #or pathlib.Path('shabbat_data.json').is_file() or pathlib.Path('hebdate_data.json').is_file()
            self.file_time_stamp = datetime.date.today()
            self.create_db_file()
        with open(self.config_path+'shabbat_data.json', encoding='utf-8') as data_file:
            self.shabbat_db = json.loads(data_file.read())
        with open(self.config_path+'hebdate_data.json', encoding='utf-8') as hebdata_file:
            self.hebrew_date_db = json.loads(hebdata_file.read())
        self.get_full_time_in()
        self.get_full_time_out()

    def set_days(self):
        """Set the friday and saturday."""
        weekday = self.set_friday(datetime.date.today().isoweekday())
        self.friday = datetime.date.today()+datetime.timedelta(days=weekday)
        self.saturday = datetime.date.today()+datetime.timedelta(
            days=weekday+1)

    @classmethod
    def set_friday(cls, day):
        """Set friday day."""
        switcher = {
            7: 5,
            1: 4,
            2: 3,
            3: 2,
            4: 1,
            5: 0,
            6: -1,
        }
        return switcher.get(day)

    # get shabbat entrace
    def get_time_in(self):
        """Get shabbat entrace."""
        result = ''
        for extract_data in self.shabbat_db:
            if extract_data['className'] == "candles":
                result = extract_data['start'][11:16]
        if self.is_time_format(result):
            return result
        return 'Error'

    # get shabbat time exit
    def get_time_out(self):
        """Get shabbat time exit."""
        result = ''
        for extract_data in self.shabbat_db:
            if extract_data['className'] == "havdalah":
                result = extract_data['start'][11:16]
        if self.is_time_format(result):
            return result
        return 'Error'

    # get full time entrace shabbat for check if is shabbat now
    def get_full_time_in(self):
        """Get full time entrace shabbat for check if is shabbat now."""
        for extract_data in self.shabbat_db:
            if extract_data['className'] == "candles":
                self.shabbatin = extract_data['start']
        if self.shabbatin is not None:
            self.shabbatin = self.shabbatin

    # get full time exit shabbat for check if is shabbat now
    def get_full_time_out(self):
        """Get full time exit shabbat for check if is shabbat now."""
        for extract_data in self.shabbat_db:
            if extract_data['className'] == "havdalah":
                self.shabbatout = extract_data['start']
        if self.shabbatout is not None:
            self.shabbatout = self.shabbatout

    # get parashat hashavo'h
    def get_parasha(self):
        """Get parashat hashavo'h."""
        result = 'שבת מיוחדת'
        get_shabbat_name = None
        for extract_data in self.shabbat_db:
            if extract_data['className'] == "parashat":
                result = extract_data['hebrew']
            for data in extract_data.keys():
                if data == 'subcat' and extract_data[data] == 'shabbat':
                    get_shabbat_name = extract_data
        if get_shabbat_name is not None:
            result = result+' - '+get_shabbat_name['hebrew']
        return result

    # check if is shabbat now / return true or false
    def is_shabbat(self):
        """Check if is shabbat now / return true or false."""
        if self.shabbatin is not None and self.shabbatout is not None:
            is_in = datetime.datetime.strptime(
                self.shabbatin, '%Y-%m-%dT%H:%M:%S')
            is_out = datetime.datetime.strptime(
                self.shabbatout, '%Y-%m-%dT%H:%M:%S')
            is_in = is_in - datetime.timedelta(
                minutes=int(self._time_before))
            is_out = is_out + datetime.timedelta(
                minutes=int(self._time_after))
            if (is_in.replace(tzinfo=None) <
                    datetime.datetime.today() < is_out.replace(tzinfo=None)):
                return 'True'
            return 'False'
        return 'False'

    # convert to hebrew date
    def get_hebrew_date(self):
        """Convert to hebrew date."""
        return self.hebrew_date_db['hebrew']

    # check if the time is correct
    @classmethod
    def is_time_format(cls, input_time):
        """Check if the time is correct."""
        try:
            time.strptime(input_time, '%H:%M')
            return True
        except ValueError:
            return False
