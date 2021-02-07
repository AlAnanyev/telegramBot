import telebot
import requests
from bs4 import BeautifulSoup

URL = 'https://1xstavka.ru/live/Table-Tennis/2064427-Masters/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36',
           'accept': '*/*'}
HOST = 'https://1xstavka.ru/'


def get_html(url, params = None):
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='c-events__item c-events__item_col')
    # print(items)
    matches = []
    for item in items:
        # счёт по сетам
        set = item.find_all('span', class_='c-events-scoreboard__cell c-events-scoreboard__cell--all')
        if len(set) == 0:
            set_text1 = '0'
            set_text2 = '0'
        else:
            set_text1 = set[0].get_text()
            set_text2 = set[1].get_text()
        # линии со счётом в сетах
        schetlines = item.find_all('div', class_='c-events-scoreboard__line')
        # коэффициенты
        bets = item.find('div', class_='c-bets')
        matches.append(
        {
            'Title': item.find('span', class_="n").get_text(),
            'Link': HOST + item.find('a', class_='c-events__name').get('href'),
            'set': set_text1 + '--' + set_text2,
            'schetline1': schetlines[0].get_text().replace('\n', ' '),
            'schetline2': schetlines[1].get_text().replace('\n', ' '),
            'bets': bets.get_text().replace('\n', ' ')

        }
        )
    return matches


def parse():
    html = get_html(URL)
    if html.status_code == 200:
        matches = get_content(html.text)
    else:
        return 'Error'
    return matches


bot = telebot.TeleBot('1699645072:AAGE3eWMl-spPf7vCJNphWQFQMUlz6k6D4A')


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, ты написал мне /start')

@bot.message_handler(commands=['Value'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, введи Low__цена, High__цена')


# @bot.message_handler(content_types=['text'])
# def send_text_values(message):
#     global lowvalue
#     global highvalue
#     if message.text.find('Low__') == 0:
#         lowvalue = int(message.text.replace('Low__', ''))
#     elif message.text.find('High__') == 0:
#         highvalue = int(message.text.replace('High__', ''))


@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, 'Привет, мой создатель')
    elif message.text.lower() == 'пока':
        bot.send_message(message.chat.id, 'Прощай, создатель')
    elif message.text.lower() == 'матчи':
        matches = parse()
        for match in matches:
            bot.send_message(message.chat.id, 'Мастерс' + match.get('Title'))
            bot.send_message(message.chat.id, match.get('Link'))
            bot.send_message(message.chat.id, 'счёт по сетам ' + match.get('set'))
            bot.send_message(message.chat.id, 'счёт в сетах 1-го' + match.get('schetline1'))
            bot.send_message(message.chat.id, 'счёт в сетах 2-го' + match.get('schetline2'))
            bot.send_message(message.chat.id, 'какие-то коэффициенты' + match.get('bets'))




bot.polling()