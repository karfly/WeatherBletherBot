import re
import json
from datetime import datetime, timedelta

import logging

import pymorphy2

from weather_api_wrapper import WeatherApiWrapper


class WeatherAnswerBuilder(object):
    def __init__(self):
        self.weather_api_wrapper = WeatherApiWrapper()

        with open('data/dicts.json') as fin:
            self.dicts = json.load(fin)

        self.morph = pymorphy2.MorphAnalyzer()

    def build_answer(self, text):
        """
        Builds answer from giver text.
        :param text: message text
        :return: generator, which generates 3 items: forecast string, image url, poem
        """
        city_name = self.parse_city_name(text)
        dt = self.parse_dt(text)

        lat, lon, corrected_city_name = self.weather_api_wrapper.get_lat_lon_by_city_name(city_name)
        logging.info('lat: {}, lon: {}'.format(lat, lon))

        description, temp, humidity, wind_speed = self.weather_api_wrapper.get_weather_forecast(lat, lon, dt)

        forecast_str = 'В {} будет {} ({}).\n'.format(
            self.morph.parse(corrected_city_name)[0].inflect({'loct'}).word.title(),
            description,
            dt.strftime('%d.%m.%Y, %H:%M'))
        forecast_str += 'Температура {} °C, относительная влажность: {}%, скорость ветра: {} м/с.\n'.format(
            temp,
            humidity,
            wind_speed)

        logging.info('Forecast string: {}'.format(forecast_str))
        yield forecast_str

        image_url = self.weather_api_wrapper.get_image_url_by_text_request(
            '{} {}'.format(corrected_city_name, description))
        yield image_url

        poem = self.weather_api_wrapper.get_poem_by_text_request(description)
        yield poem

    def parse_city_name(self, text):
        """
        Founds city in text and returns it's name in the nominative case.
        :param text: input string
        :return: city name in the nominative case

        2 types of texts are supported.
        See examples:
            1) [...] в Москве [...]
            2) Москва [...]
        """
        city = None

        # Finding type 1
        for found_city in re.findall(r'[В,в] (\w+)', text):
            if found_city.lower() not in self.dicts['days_of_week_all_forms']:
                city = self.morph.parse(found_city)[0].normal_form

        # If type 1 is not found, it's type 2
        if city is None:
            city = text.split()[0]

        return city.title()

    def parse_dt(self, text):
        """
        Founds absolute date in text and return it in datetime format
        :param text:
        :return: date
        4 types of date are supported.
        See examples:
            1) Realtive: Погода в Москве завтра
            2) Absolute: Погода в Москве ночью
            3) Day of week: Погода в Москве в четверг
            4) After N days: Погода в Москве через 3 дня
        """
        text_words = text.split()
        now = datetime.now()

        # Relative terms
        for relative_term, delta_hours in self.dicts['relative_terms'].items():
            if relative_term in text_words:
                return now + timedelta(hours=delta_hours)

        # Absolute terms
        for absolute_term, delta_hours in self.dicts['absolute_terms'].items():
            if absolute_term in text_words:
                return now.replace(hour=delta_hours,
                                   minute=0, second=0, microsecond=0)

        text_words_normal_form = [self.morph.normal_forms(x)[0] for x in text_words]

        # Days of week
        for index, day_of_week in enumerate(self.dicts['days_of_week']):
            if day_of_week in text_words_normal_form:
                delta_days = (index - now.weekday()) % 7
                return now + timedelta(days=delta_days)

        # After N days
        delta_days_found = re.findall(r'через (\d+)', text)
        if delta_days_found:
            return now + timedelta(days=int(delta_days_found[0]))

        return now
