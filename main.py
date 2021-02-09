import telebot
import requests
import time
from bs4 import BeautifulSoup

URL = ['https://1xstavka.ru/live/Table-Tennis/2178512-Winners-League/',
 'https://1xstavka.ru/live/Table-Tennis/1792858-Win-Cup/',
 'https://1xstavka.ru/live/Table-Tennis/1197285-TT-Cup/',
 'https://1xstavka.ru/live/Table-Tennis/1733171-Setka-Cup/',
 'https://1xstavka.ru/live/Table-Tennis/1691055-Pro-League/']

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36',
           'accept': '*/*'}
HOST = 'https://1xstavka.ru/'
POROGWINSET = 5  # пороговый счет в партии
POROGKOEF = 1.4  # пороговый коэффициент
ENDCOMMAND = 0  # команда завершения работы парсера
SIGNAL = -1 # команда на вывод всех сигналов

def get_html(url, params=None):  # реквест, получение ответа
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='c-events__item c-events__item_col')
    # print(items)
    matches = []
    for item in items:
        # линии со счётом в сетах
        # первая линия
        schetlines = item.find_all('div', class_='c-events-scoreboard__line')
        schetline1 = schetlines[0].get_text().split('\n')
        schetline1.pop()  # убираем последний пустой элемент
        schetline1.remove(schetline1[0]) # убираем пустые элементы сначала
        schetline1.remove(schetline1[0])
        schetline1.remove(schetline1[0])
        if len(schetline1) == 1:
            set1 = '0'
        else:
            set1 = schetline1.pop(0)  # первый элемент - победы в сетах, удаляем и присваиваем в set
        # вторая линия
        schetline2 = schetlines[1].get_text().split('\n')
        schetline2.pop()
        schetline2.remove(schetline2[0])
        schetline2.remove(schetline2[0])
        schetline2.remove(schetline2[0])
        if len(schetline2) == 1:
            set2 = '0'
        else:
            set2 = schetline2.pop(0)  # первый элемент - победы в сетах, удаляем и присваиваем в set
        # коэффициенты
        bets = item.find('div', class_='c-bets').get_text().split('\n')
        bet1 = bets[2]
        bet2 = bets[8]
        matches.append(
        {
            'Title': item.find('span', class_="n").get_text(),
            'Link': HOST + item.find('a', class_='c-events__name').get('href'),
            'set1': set1,
            'set2': set2,
            'schetline1': schetline1,
            'schetline2': schetline2,
            'bet1': bet1,
            'bet2': bet2
        }
        )
    return matches


def proverka_na_pobedu(match):

    if match.get('bet1') == '-' or match.get('bet2') == '-': # условие для коэфиц. без значений
        return -1

    if float(match.get('bet1')) >= POROGKOEF:  # сравение с порогом первого коэф
        if int(match.get('set1')) == 1 and int(match.get('set2')) == 0:   # проверка на одну победу в партии
            if int(match.get('schetline2')[0]) <= POROGWINSET:
                res1 = 'sledim'  # на слежение
            else:
                res1 = 'pas'
        elif int(match.get('set1')) == 2 and int(match.get('set2')) == 0:  # проверка на две победы в партии
            if int(match.get('schetline2')[0]) <= POROGWINSET and int(match.get('schetline2')[1]) <= POROGWINSET:
                res1 = 'stavka'  # на ставку
            else:
                res1 = 'pas'
        else:
            res1 = 'pas'
    else:
        res1 = 'pas'

    if float(match.get('bet2')) >= POROGKOEF:   # сравение с порогом второго коэф
        if int(match.get('set2')) == 1 and int(match.get('set1')) == 0:  # проверка на одну победу в партии
            if int(match.get('schetline1')[0]) <= POROGWINSET:
                res2 = 'sledim'  # на слежение
            else:
                res2 = 'pas'
        elif int(match.get('set2')) == 2 and int(match.get('set1')) == 0:  # проверка на две победы в партии
            if int(match.get('schetline1')[0]) <= POROGWINSET and int(match.get('schetline1')[1]) <= POROGWINSET:
                res2 = 'stavka'  # на ставку
            else:
                res2 = 'pas'
        else:
            res2 = 'pas'
    else:
        res2 = 'pas'

    # возврат результатов
    if res1 == 'stavka':
        return 1
    elif res2 == 'stavka':
        return 2
    elif res1 == 'sledim':
        return 11
    elif res2 == 'sledim':
        return 22
    else:
        return -1


def parse():
    matches = []  # список матчей
    for url in URL:
        html = get_html(url)
        if html.status_code == 200:
            mat = get_content(html.text)
            matches += mat
    return matches


def loop_zapros():
    global ENDCOMMAND
    while ENDCOMMAND != 1:
        print('запрос')
        matches = parse()
        for match in matches:
            result_proverki = proverka_na_pobedu(match)
            if SIGNAL == 1:
                if result_proverki == 1 or result_proverki == 2:
                    bot.send_message(362390015,
                                 match.get('Title') + '\n' +
                                 match.get('Link') + '\n' +
                                 'Cчёт по сетам: ' + match.get('set1') + '--' + match.get('set2') + '\n' +
                                 'Счёт в сетах 1-го: ' + ''.join(
                                     str(e + '\t') for e in match.get('schetline1')) + '\n' +
                                 'Счёт в сетах 2-го: ' + ''.join(
                                     str(e + '\t') for e in match.get('schetline2')) + '\n' +
                                 'П1 = ' + match.get('bet1') + '\n' +
                                 'П2 = ' + match.get('bet2')
                                 )
            elif SIGNAL == -1:
                if result_proverki != -1:
                    bot.send_message(362390015,
                                 match.get('Title') + '\n' +
                                 match.get('Link') + '\n' +
                                 'Cчёт по сетам: ' + match.get('set1') + '--' + match.get('set2') + '\n' +
                                 'Счёт в сетах 1-го: ' + ''.join(
                                     str(e + '\t') for e in match.get('schetline1')) + '\n' +
                                 'Счёт в сетах 2-го: ' + ''.join(
                                     str(e + '\t') for e in match.get('schetline2')) + '\n' +
                                 'П1 = ' + match.get('bet1') + '\n' +
                                 'П2 = ' + match.get('bet2')
                                 )
        # bot.send_message(362390015, 'проверка')
        print('конец запроса')
        time.sleep(10)
    ENDCOMMAND = 0


bot = telebot.TeleBot('1699645072:AAGE3eWMl-spPf7vCJNphWQFQMUlz6k6D4A')



@bot.message_handler(commands=['start_parcer'])
def start_message(message):
    bot.send_message(message.chat.id, 'Старт работы парсера')
    loop_zapros()


@bot.message_handler(commands=['stop_parcer'])
def start_message(message):
    global ENDCOMMAND
    ENDCOMMAND = 1
    bot.send_message(message.chat.id, 'Парсер остановлен')


@bot.message_handler(commands=['vse'])
def start_message(message):
    global SIGNAL
    SIGNAL = -1
    bot.send_message(message.chat.id, 'выводятся все матчи')


@bot.message_handler(commands=['stavka'])
def start_message(message):
    global SIGNAL
    SIGNAL = 1
    bot.send_message(message.chat.id, 'выводятся только матчи на ставку')


@bot.message_handler(commands=['коэффициент'])
def start_message(message):
    bot.send_message(message.chat.id, 'Сейчас порог по коэффициенту = ' + str(POROGKOEF) + '. Чтобы поменять введи koef_<значение>')


@bot.message_handler(commands=['партия'])
def start_message(message):
    bot.send_message(message.chat.id, 'Сейчас порог по счёту в партии = ' + str(POROGWINSET) + '. Чтобы поменять введи winset_<значение>')


@bot.message_handler(content_types=['text'])
def send_text(message):
    global POROGKOEF
    global POROGWINSET
    print(message.text, message.chat.id)
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, 'Привет, Поросенок')

    elif message.text.find('koef_') == 0: # смена коэффициента
        message_size = len(message.text)
        if message_size > 5:
            sl = slice(5, message_size, 1)
            new_koef = message.text[sl]
            if new_koef.replace('.', '').isdigit():
                POROGKOEF = float(new_koef)
                bot.send_message(message.chat.id, 'Порог коэффициента >=' + str(POROGKOEF))
                print(POROGKOEF)

    elif message.text.find('winset_') == 0: # смена порога по выигрышам в партии
        message_size = len(message.text)
        if message_size > 7:
            sl = slice(7, message_size, 1)
            new_koef = message.text[sl]
            if new_koef.isdigit():
                POROGWINSET = int(new_koef)
                bot.send_message(message.chat.id, 'Порог выигрышей в партии <=' + str(POROGWINSET))
                print(POROGWINSET)

    elif message.text.lower() == 'test': # тестовая ветка
        matches = parse()
        for match in matches:
            bot.send_message(message.chat.id,
                             match.get('Title') + '\n' +
                             match.get('Link') + '\n' +
                             'Cчёт по сетам: ' + match.get('set1') + '--' + match.get('set2') + '\n' +
                             'Счёт в сетах 1-го: ' + ''.join(str(e + '\t') for e in match.get('schetline1')) + '\n' +
                             'Счёт в сетах 2-го: ' + ''.join(str(e + '\t') for e in match.get('schetline2')) + '\n' +
                             'П1 = ' + match.get('bet1') + '\n' +
                             'П2 = ' + match.get('bet2')
                             )

bot.polling()

