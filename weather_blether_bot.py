import os

import telepot
from telepot.delegate import per_chat_id, create_open, pave_event_space

import urllib.request

from weather_answer_builder import WeatherAnswerBuilder

# Logging
import logging

logging.basicConfig(filename='log', filemode='a',
                    format='%(asctime)s %(message)s', datefmt='%H:%M:%S',
                    level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())


class WeatherBletherBot(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(WeatherBletherBot, self).__init__(*args, **kwargs)
        self.weather_answer_builder = WeatherAnswerBuilder()

        with open('data/start_message.txt') as fin:
            self.start_message = fin.read()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type == 'text':
            text = msg['text']
            logging.info('Chat id: {} | Message: {}'.format(chat_id, text))

            if text.startswith('/start'):
                self.sender.sendMessage(self.start_message)
            else:
                builder = self.weather_answer_builder.build_answer(text)
                self.sender.sendMessage(next(builder))

                furl = urllib.request.urlopen(next(builder))
                self.sender.sendChatAction('upload_photo')
                self.sender.sendPhoto(('weather.png', furl))
                furl.close()

                self.sender.sendMessage('Стишок по теме:\n')
                self.sender.sendChatAction('upload_document')
                self.sender.sendMessage(next(builder))


if __name__ == '__main__':
    telegram_token = os.environ.get('TELEGRAM_TOKEN')

    bot = telepot.DelegatorBot(telegram_token, [
        pave_event_space()(
            per_chat_id(), create_open, WeatherBletherBot, timeout=86400),
    ])

    bot.message_loop(run_forever='Listening ...')
