import telebot
import requests
from bs4 import BeautifulSoup

URL = 'https://www.labirint.ru/gift/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36',
           'accept': '*/*'}
HOST = 'https://www.labirint.ru'

lowvalue = 0
highvalue = 0

def get_html(url, params = None):
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_content(html, high_border, low_border):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='product-padding')
    books = []
    for item in items:
        price = item.find('span', class_="price-gray").get_text()
        price = price.replace(" ", "")
        if high_border > int(price) > low_border:
            books.append(
            {
                'Title': item.find('span', class_="product-title").get_text(),
                'Link': HOST + item.find('a', class_='cover').get('href')
            }
            )
    return books


def parse(high_border, low_border):
    html = get_html(URL)
    if html.status_code == 200:
        books = get_content(html.text, high_border, low_border)
    else:
        return 'Error'
    return books


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
    global lowvalue
    global highvalue
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, 'Привет, мой создатель')
    elif message.text.lower() == 'пока':
        bot.send_message(message.chat.id, 'Прощай, создатель')
    elif message.text.lower() == 'лабиринт':
        books = parse(int(highvalue), int(lowvalue))
        for book in books:
            bot.send_message(message.chat.id, book.get('Title'))

    elif message.text.find('Low__') == 0:
        lowvalue = int(message.text.replace('Low__', ''))
    elif message.text.find('High__') == 0:
        highvalue = int(message.text.replace('High__', ''))


bot.polling()