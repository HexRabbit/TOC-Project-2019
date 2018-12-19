from bottle import route, run, request, abort, static_file
import requests

from fsm import TocMachine
import config
import copy
import random
import traceback
from utils import send_text_message, send_url_message, send_button_message

userdata = {}

VERIFY_TOKEN = config.VERIFY_TOKEN

@route("/webhook", method="GET")
def setup_webhook():
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return challenge

    else:
        abort(403)


@route("/webhook", method="POST")
def webhook_handler():
    body = request.json

    try:
        if body['object'] == "page":
            msg = ''
            event = body['entry'][0]['messaging'][0]
            id = int(event['sender']['id'])
            if event.get('message'):
                msg = event['message']['text']
            elif event.get('postback'):
                msg = event['postback']['payload']
            state_handler(id, msg.strip())
            return 'OK'
        else:
            return 'OK'
    except:
        return 'OK'


@route('/show-fsm/<id:int>', methods=['GET'])
def show_fsm(id):
    if userdata.get(id):
        userdata[id]['machine'].get_graph().draw('./img/'+str(id)+'fsm.png', prog='dot', format='png')
        return static_file(str(id)+'fsm.png', root='./img/', mimetype='image/png')
    else:
        abort(404)

def state_handler(id, text):
    if not userdata.get(id) or text == 'get_started':
        userdata[id] = {
            'state': 'new',
            'record': 0,
            'guess': 0,
            'machine': TocMachine(
                states=[
                    'new',
                    'menu',
                    'game',
                    'end',
                    'info',
                    'anime'
                ],
                transitions=[
                    {
                        'trigger': 'menu',
                        'source': 'new',
                        'dest': 'menu',
                    },
                    {
                        'trigger': 'info',
                        'source': 'new',
                        'dest': 'info',
                    },
                    {
                        'trigger': 'back',
                        'source': 'info',
                        'dest': 'new',
                    },
                    {
                        'trigger': 'anime',
                        'source': 'new',
                        'dest': 'anime'
                    },
                    {
                        'trigger': 'back',
                        'source': 'anime',
                        'dest': 'new'
                    },
                    {
                        'trigger': 'game',
                        'source': 'menu',
                        'dest': 'game'
                    },
                    {
                        'trigger': 'end',
                        'source': 'game',
                        'dest': 'end'
                    },
                    {
                        'trigger': 'restart',
                        'source': 'end',
                        'dest': 'game'
                    },
                    {
                        'trigger': 'new',
                        'source': 'end',
                        'dest': 'new'
                    },
                ],
                initial='new',
                auto_transitions=False,
                show_conditions=True,
            )
        }
        send_new_start(id)
        return

    print('User: {} STATE: {}'.format(id, userdata[id]['machine'].state))
    state = userdata[id]['state']

    if state == 'new':
        if text == 'menu':
            send_button_message(id, 'Guessing numbers', ['start'])
            userdata[id]['state'] = 'menu'
            userdata[id]['machine'].menu()
        elif text == 'info':
            send_button_message(id, 'This little application is create for TOC-project', ['back'])
            userdata[id]['state'] = 'info'
            userdata[id]['machine'].info()
        elif text == 'anime':
            anime_handler(id)
        else:
            send_text_message(id, 'Wrong input')

    elif state == 'menu':
        if text[:5] == 'start':
            game_start(id)
            userdata[id]['state'] = 'game'
            userdata[id]['machine'].game()
        else:
            send_text_message(id, 'Wrong input')

    elif state == 'game':
        game_handler(id, text)

    elif state == 'end':
        if text == 'yes':
            game_start(id)
            userdata[id]['state'] = 'game'
            userdata[id]['machine'].restart()
        elif text == 'no':
            send_new_start(id)
            userdata[id]['state'] = 'new'
            userdata[id]['machine'].new()
        else:
            send_text_message(id, 'Wrong input')

    elif state == 'info':
        if text == 'back':
            send_new_start(id)
            userdata[id]['state'] = 'new'
            userdata[id]['machine'].back()
        else:
            send_text_message(id, 'Wrong input')
    elif state == 'anime':
        if text == 'back':
            send_new_start(id)
            userdata[id]['state'] = 'new'
            userdata[id]['machine'].back()
        else:
            send_text_message(id, 'Wrong input')

def send_new_start(id):
    send_button_message(id, 'Use "menu" to view games, "info" to get info of this app, or "anime" to let RNGesus recommand you an anime!', ['menu', 'info', 'anime'])


def game_start(id):
    userdata[id]['guess'] = random.randint(0, 1000)
    userdata[id]['count'] = 8
    send_text_message(id, 'You have 8 times to guess a number (1-1000)')
    send_text_message(id, 'GO!')

def game_handler(id, text):
    try:
        userdata[id]['count'] -= 1
        if int(text) == userdata[id]['guess']:
            send_text_message(id, 'WOW! You guessed right!')
            userdata[id]['state'] = 'end'
            userdata[id]['machine'].end()
        elif userdata[id]['count'] == 0:
            send_text_message(id, 'GAMEOVER')
            send_text_message(id, 'Answer: {}'.format(userdata[id]['guess']))
            send_button_message(id, 'Retry?', ['yes', 'no'])
            userdata[id]['state'] = 'end'
            userdata[id]['machine'].end()
        else:
            if int(text) > userdata[id]['guess']:
                send_text_message(id, 'Too big. Keep trying!')
            else:
                send_text_message(id, 'Too small. Keep trying!')
            send_text_message(id, 'Remain {} times'.format(userdata[id]['count']))

    except:
        pass

def anime_handler(id):
    userdata[id]['state'] = 'anime'
    userdata[id]['machine'].anime()
    url = 'https://anidb.net/perl-bin/animedb.pl?show=anime&do.random=1'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.6',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Mobile Safari/537.36',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive'
    }
    try:
        req = requests.get(url, headers=headers, allow_redirects=False)
        resolved = 'https://anidb.net/perl-bin/' + req.headers['Location']
        print(resolved)
        send_text_message(id, 'Here\'s today recommendation:')
        send_url_message(id, resolved)
    except:
        traceback.print_exc()
        send_button_message(id, 'Some bad thing happened', ['back'])


if __name__ == "__main__":
    run(host="localhost", port=5000, debug=True, reloader=True)

