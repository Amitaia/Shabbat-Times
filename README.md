# Shabbat Times with HomeAssistant Sensor Custom Component
Get Shabbat Times in HomeAssistant

Updates 26.08.2018
1. fix json data parsing (hebcal add some things and change the index )
2. add new feature : is_shabbat , now you have a sensor that can tell the HA that is shabbat or not .
3. timezone are now dynamic for chnages in 31/10/2018

Updates 13.09.2018
1. create new sensor , now the data come more dynamic and not by index
2. remove sunset sensor and is_hagg
3. fix update data , now the data is update on 24H..not the sensors..only the data!

Updates 16.09.2018
1. fix db time updates ( return for every 5 min)
2. add validate time and date for result , if failed the state get 'Error' status

Updates 30.09.2018
1. change DB sorce ( hope that still be stable )
2. now we check only in friday and saturday for shabbat times 

Updates 07.10.2018
1. recode the sensor , now is async so no need a for scan interval anymore
2. all db now downloading to local json file and once a day the db check for change
3. no need anymore for geoid and latitude and longitude . the sensor got it from HA config ,
   so you need to besure that you put them in configuration.yaml . also need the TimeZone 
   see link : https://www.home-assistant.io/blog/2015/05/09/utc-time-zone-awareness/
   Example :
   ```python
      homeassistant:
        latitude: 32.0667
        longitude: 34.7667
        time_zone: Asia/Jerusalem
   ```
   
Updates 21.10.2018
1. Add Hebrew days name ..

Updates 03.12.2018
1. fix shabbat entrace , get wronk value cause chanuka times
   
   
   
## Guide How to use it

### Requirements

* First need to create folder "sensor" in your HomeAssistant config/custom_components folder
* Copy python file "shabbat.py" to the HA config ./custom_components/sensor folder.
* Now you need to add those lines in configuration.yaml :

```python
sensor:
  - platform: shabbat
    havdalah_calc: 42 
    time_before_check: 10
    time_after_check: 10
    resources:
      - in
      - out
      - parasha
      - hebrew_date
      - is_shabbat  # state get True if is shabbat and False is shabbat end.
  ```
  
  ### Entity Optional
  
  havdalah_calc =   By defaule he get 42 Min , you can set 50 or 72 for other methods
  
  time_before_check: By defaule he get 10 Min , you can set minutes so the sensor can check if is shabbat
  
  time_after_check: By defaule he get 10 Min , you can set minutes so the sensor can check if shabbat is ends..
  
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
          - sensor.shabbat_is_shabbat
 ```
 * All sensors icon already set , but you can always customize them..
 
 # Good Luck !
