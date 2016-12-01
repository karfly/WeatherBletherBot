# import sys
import telepot
from telepot.delegate import per_chat_id, create_open, pave_event_space
import urllib.request

# Logging
import logging
logging.basicConfig(filename='log', filemode='a',
                    format='%(asctime)s %(message)s', datefmt='%H:%M:%S',
                    level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())


class WeatherBletherBot(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(WeatherBletherBot, self).__init__(*args, **kwargs)

    def on_chat_message(self, msg):
        username = msg['chat']['username']
        chat_id = msg['chat']['id']
        text = msg['text']

        logging.info('From: \'{}\' (id: {}) | Message: {}'.format(username, chat_id, text))

        furl = urllib.request.urlopen('https://desktop.telegram.org/img/td_logo.png')
        # print(furl.read())
        self.sender.sendChatAction('upload_photo')
        self.sender.sendPhoto(('td_logo.png', furl))


if __name__ == '__main__':
    with open('.token') as fin:
        token = fin.read()

    bot = telepot.DelegatorBot(token, [
        pave_event_space()(
            per_chat_id(), create_open, WeatherBletherBot, timeout=10),
    ])

    bot.message_loop(run_forever='Listening ...')
