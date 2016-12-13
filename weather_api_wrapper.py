import os
import numpy as np

import json
import requests

import urllib
import urllib.parse

from bs4 import BeautifulSoup


class WeatherApiWrapper(object):
    def __init__(self):
        self.yandex_weather_api_key = os.environ.get('YANDEX_WEATHER_API_KEY')
        print(self.yandex_weather_api_key)

    @staticmethod
    def get_lat_lon_by_city_name(city_name):
        """
        Founds city's lat and lon by name. Also returns corrected city name
        :param city_name: city name
        :return: lat, lon, corrected city name
        """
        yandex_geocode_url = 'http://geocode-maps.yandex.ru/1.x/?'
        r = requests.get(yandex_geocode_url +
                         urllib.parse.urlencode({
                             'geocode': city_name,
                             'results': 1,
                             'format': 'json'
                         }))
        j = json.loads(r.text)

        lon_lat_string = j['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        lon, lat = map(float, lon_lat_string.split())

        corrected_city_name = j['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['name']

        return lat, lon, corrected_city_name

    def get_weather_forecast(self, lat, lon, dt):
        """
        Returns nearest weather forecast for (lat, lon) coordinate for dt
        :param lat: latitude
        :param lon: latitude
        :param dt: datetime to forecast for
        :return: weather description string, temperature, humidity, wind speed
        """
        yandex_weather_url = 'https://api.weather.yandex.ru/v1/forecast?'

        http_params_str = urllib.parse.urlencode({
            'lat': lat,
            'lon': lon,
            'l10n': 'true'
        })
        http_request = yandex_weather_url + http_params_str

        r = requests.get(http_request,
                         headers={
                             'X-Yandex-API-Key': self.yandex_weather_api_key
                         })

        j = json.loads(r.text)

        forecasts = []
        for forecast_day in j['forecasts']:
            for forecast in forecast_day['hours']:
                forecasts.append(forecast)

        def find_nearest_forecast(forecasts, dt):
            timestamps = [x['hour_ts'] for x in forecasts]
            idx = (np.abs(np.array(timestamps) - dt.timestamp())).argmin()
            return forecasts[idx]

        forecast = find_nearest_forecast(forecasts, dt)

        return j['l10n'][forecast['condition']], forecast['temp'], forecast['humidity'], forecast['wind_speed']

    @staticmethod
    def get_image_url_by_text_request(text_request):
        """
        Returs random image url from Yandex.Images by a given text request
        :param text_request: text request to search image
        :return: image url
        """
        yandex_images_url = 'https://yandex.ru/images/search?'

        r = requests.get(yandex_images_url +
                         urllib.parse.urlencode({
                             'text': text_request,
                             'isize': 'medium'
                         }))
        soup = BeautifulSoup(r.text, 'html.parser')
        img_elems = soup.find_all('img', {'class': 'serp-item__thumb'})
        img_elem_chosen = img_elems[np.random.randint(0, len(img_elems))]

        image_url = 'http:' + img_elem_chosen['src']
        return image_url

    @staticmethod
    def get_poem_by_text_request(text_request):
        """
        Returns poem by text request
        :param text_request: text request to search poem
        :return: poem text
        """
        default_text_request = 'погода'
        poetory_url = 'http://poetory.ru/content/list?'

        r = requests.get(poetory_url +
                         urllib.parse.urlencode({
                             'query': text_request
                         }))

        soup = BeautifulSoup(r.text, 'html.parser')
        poem_elems = soup.find_all('div', {'class': 'item-text'})
        if len(poem_elems) == 0:
            return WeatherApiWrapper.get_poem_by_text_request(default_text_request)

        poem_elem_chosen = poem_elems[np.random.randint(0, len(poem_elems))]

        def clean_poem_elem_text(poem_elem):
            text = ''
            for e in poem_elem.recursiveChildGenerator():
                if isinstance(e, str):
                    text += e
                elif e.name == 'br':
                    text += '\n'
            return text.strip()

        return clean_poem_elem_text(poem_elem_chosen)
