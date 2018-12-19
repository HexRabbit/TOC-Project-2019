import requests
import config
from bs4 import BeautifulSoup


GRAPH_URL = "https://graph.facebook.com/v2.6"
ACCESS_TOKEN = config.ACCESS_TOKEN
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}


def send_text_message(id, text):
    url = "{0}/me/messages?access_token={1}".format(GRAPH_URL, ACCESS_TOKEN)
    payload = {
        "recipient": {"id": id},
        "message": {"text": text}
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print("Unable to send message: " + response.text)
    return response

def create_buttons(buttons):
    l = []
    for button in buttons:
        l.append({ "type": "postback", "title": button, "payload": button })
    return l

def send_button_message(id, text, buttons):

    url = "{0}/me/messages?access_token={1}".format(GRAPH_URL, ACCESS_TOKEN)
    payload = {
        "recipient":{
            "id": id
        },
        "message":{
            "attachment":{
                "type": "template",
                "payload":{
                    "template_type": "button",
                    "text": text,
                    "buttons": create_buttons(buttons)
                }
            }
        }
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print("Unable to send message: " + response.text)

    return response

def send_url_message(id, target_url):
    r = requests.get(target_url, headers = headers)
    html = r.text
    soup = BeautifulSoup(html, 'lxml')
    img = soup.find('meta', attrs={'property': 'og:image'})['content']
    title = soup.find('meta', attrs={'property': 'og:title'})['content']
    description = soup.find('meta', attrs={'property': 'og:description'})['content']


    url = "{0}/me/messages?access_token={1}".format(GRAPH_URL, ACCESS_TOKEN)
    payload = {
        "recipient":{
            "id": id
        },
        "message":{
            "attachment":{
                "type":"template",
                "payload":{
                    "template_type":"generic",
                    "elements":[
                        {
                            "title": title,
                            "image_url": img,
                            "subtitle": description,
                            "default_action": {
                                "type": "web_url",
                                "url": target_url,
                                "webview_height_ratio": "full",
                            },
                            "buttons":[
                                {
                                    "type": "postback",
                                    "title": "back",
                                    "payload": "back"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print("Unable to send message: " + response.text)

    return response



"""
def send_image_url(id, img_url):
    pass

def send_button_message(id, text, buttons):
    pass
"""
