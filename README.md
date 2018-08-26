# Shabbat Times with HomeAssistant Sensor Custom Component
Get Shabbat Times in HomeAssistant

Updates 26.08.2018
1. fix json data parsing (hebcal add some things and change the index )
2. add new feature : is_shabbat , now you have a sensor that can tell the HA that is shabbat or not .
3. timezone are now dynamic for chnages in 31/10/2018


## Guide How to use it

### Requirements

* First need to create folder "sensor" in your HomeAssistant config/custom_components folder
* Copy python file "shabbat_hagg.py" to the HA config ./custom_components/sensor folder.
* Now you need to add those lines in sensor config :

```python
- platform: shabbat_hagg
  latitude: 0000
  longitude: 0000
  geoid: 0000
  havdalah_calc: 42 
  scan_interval: 60
  resources:
    - in
    - out
    - parasha
    - hebrew_date
    - sunset
    - is_shabbat -- state get True if is shabbat and False is shabbat end.
    - is_holiday -- not work for now...
  ```
  ### Entity Requirements
  
  geoid (require) = need for your city location
  
  latitude (require) = need for the sun sunset - you can find like in ha configurtion.yaml
  
  longitude (require) = need for the sun sunset - you can find like in ha configurtion.yaml
  
  ### Entity Optional
  
  havdalah_calc =   By defaule he get 42 Min , you can set 50 or 72 for other methods
  
  time_before_check: By defaule he get 10 Min , you can set minutes so the sensor can check if is shabbat
  
  time_after_check: By defaule he get 10 Min , you can set minutes so the sensor can check if shabbat is ends..
  
  scan_interval =   By defaule he get 60 seconds , you can set what you wants...
  
  ### Sensor Views Options :
  
* Add those lines to your group.yaml :
```python
shabat:
  name: "זמני כניסת שבת/חג"
  view: no
  #icon: mdi:ceiling-light
  entities:
   - sensor.shabbat_hebrew_date
   - sensor.shabbat_parasha
   - sensor.shabbat_in
   - sensor.shabbat_out
   - sensor.shabbat_sunset
   - sensor.shabbat_is_shabbat
   
 ```
 
 * Or in ui-lovelace.yaml :
 
 ```python
 - type: entities
        title: "זמני כניסת שבת/חג"
        show_header_toggle: false
        entities:
          - sensor.shabbat_hebrew_date
          - sensor.shabbat_parasha
          - sensor.shabbat_in
          - sensor.shabbat_out
          - sensor.shabbat_sunset
          - sensor.shabbat_is_shabbat
 ```
 * All sensors icon already set , but you can always customize them..
 
 # Good Luck !
