import telebot
import requests
import time
from telebot import types
from bs4 import BeautifulSoup
from multiprocessing import Pool

LEAGUENAMES = ['Winners-League', 'Win-Cup', 'TT-Cup', 'Setka-Cup', 'Pro-League']
URL = ['https://1xstavka.ru/live/Table-Tennis/2178512-Winners-League/',
       'https://1xstavka.ru/live/Table-Tennis/1792858-Win-Cup/',
       'https://1xstavka.ru/live/Table-Tennis/1197285-TT-Cup/',
       'https://1xstavka.ru/live/Table-Tennis/1733171-Setka-Cup/',
       'https://1xstavka.ru/live/Table-Tennis/1691055-Pro-League/']

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/88.0.4324.146 Safari/537.36',
           'accept': '*/*'}
HOST = 'https://1xstavka.ru/'
POROGWINSET = 7  # пороговый счет в партии
POROGKOEF = 1.4  # пороговый коэффициент
ENDCOMMAND = 0  # команда завершения работы парсера
SIGNAL = 1  # команда на вывод только на победу
PRIZNAKRABOTY = 0  # признак работы
IDMEMBERS = [-1001323622532, 362390015]  # ID telegramm
start_time_parser = 0
STEKMATCHEY = []


def get_html(url, params=None):  # реквест, получение ответа
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_content(url):
    html = get_html(url)  # получение html кода
    soup = BeautifulSoup(html.text, 'html.parser')
    items = soup.find_all('div', class_='c-events__item c-events__item_col')
    # print(items)
    matches = []
    for item in items:
        # проверка матча на правильную лигу
        match_url = item.find('a', class_='c-events__name').get('href')
        for league_name in LEAGUENAMES:
            if match_url.find(league_name) > 0:
                # линии со счётом в сетах
                # первая линия
                schetlines = item.find_all('div', class_='c-events-scoreboard__line')
                schetline1 = schetlines[0].get_text().split('\n')
                schetline1.pop()  # убираем последний пустой элемент
                schetline1.remove(schetline1[0])  # убираем пустые элементы сначала
                schetline1.remove(schetline1[0])
                schetline1.remove(schetline1[0])
                if len(schetline1) == 0:  # заплатка на отсутствие счета в первой партии
                    continue
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
                        'Link': HOST + match_url,
                        'set1': set1,
                        'set2': set2,
                        'schetline1': schetline1,
                        'schetline2': schetline2,
                        'bet1': bet1,
                        'bet2': bet2
                    }
                )
    return matches


def proverka_na_pobedu(match):  # основная проверка матча
    if match.get('bet1') == '-' or match.get('bet2') == '-':  # условие для коэфиц. без значений
        return -1
    if len(match.get('schetline2')) == 3:
        if float(match.get('bet1')) >= POROGKOEF:  # сравение с порогом первого коэф
            if int(match.get('set1')) == 2 and int(match.get('set2')) == 0:  # проверка на две победы в партии
                if int(match.get('schetline2')[0]) <= POROGWINSET and int(
                        match.get('schetline2')[1]) <= POROGWINSET and int(match.get('schetline2')[2]) <= 1:
                    res1 = 'stavka'  # на ставку
                else:
                    res1 = 'pas'
            else:
                res1 = 'pas'
        else:
            res1 = 'pas'
    else:
        res1 = 'pas'

    if len(match.get('schetline1')) == 3:
        if float(match.get('bet2')) >= POROGKOEF:  # сравение с порогом первого коэф
            if int(match.get('set1')) == 0 and int(match.get('set2')) == 2:  # проверка на две победы в партии
                if int(match.get('schetline1')[0]) <= POROGWINSET and int(
                        match.get('schetline1')[1]) <= POROGWINSET and int(match.get('schetline1')[2]) <= 1:
                    res2 = 'stavka'  # на ставку
                else:
                    res2 = 'pas'
            else:
                res2 = 'pas'
        else:
            res2 = 'pas'
    else:
        res2 = 'pas'

    if res1 == 'stavka':
        return 1
    elif res2 == 'stavka':
        return 2
    else:
        return -1


def proverka_na_3partiu():
    pass


def parse():
    with Pool(10) as p:
        leagues = p.map(get_content, URL)
    return leagues


def stek_matchey(match):  # здесь будеть накапливаться список матчей
    global STEKMATCHEY
    if len(STEKMATCHEY) == 0:  # список пустой
        STEKMATCHEY.append(match.get('Link'))  # добавляем в список
        forma_message(match)  # выводим в канал
    else:
        for match_in_stek in STEKMATCHEY:  # цикл по списку
            if match_in_stek == match.get('Link'):
                return
            else:
                STEKMATCHEY.append(match.get('Link'))
                forma_message(match)


# для статистики можного выводить ежедневно информацию с помощью schedule


def loop_zapros():
    global ENDCOMMAND
    global PRIZNAKRABOTY
    if PRIZNAKRABOTY == 1:
        return -1  # выходим если парсер уже работает
    while ENDCOMMAND != 1:
        PRIZNAKRABOTY = 1
        start_time = time.time()  # старт замера времени
        print('запрос')
        with Pool(10) as p:
            leagues = p.map(get_content, URL)
            for league in leagues:
                for match in league:
                    result_proverki_pobeda = proverka_na_pobedu(match)
                    if SIGNAL == 1:
                        if result_proverki_pobeda == 1 or result_proverki_pobeda == 2:
                            stek_matchey(match)
                    elif SIGNAL == -1:
                        if result_proverki_pobeda != -1:
                            forma_message(match)
        # bot.send_message(362390015, 'проверка')
        print('     конец запроса', "--- %s seconds ---" % (time.time() - start_time))
        time.sleep(0)  # время задержки между запросами
    ENDCOMMAND = 0  # обнуление команды на окончание работы парсера
    PRIZNAKRABOTY = 0  # обнуление признака работы парсера
    return 1  # успешное завершение работы


def forma_message(match):  # форма отправки сообщений адресатам
    bot.send_message(IDMEMBERS[0],
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


bot = telebot.TeleBot('1699645072:AAGE3eWMl-spPf7vCJNphWQFQMUlz6k6D4A')


# Далее описание работы телеграмм бота

@bot.message_handler(commands=['start_parser'])
def start_message(message):
    bot.send_message(message.chat.id, 'Запускаю парсер')
    global start_time_parser
    start_time_parser = time.time()
    otvet = loop_zapros()
    if otvet == -1:
        bot.send_message(message.chat.id, 'Парсер уже запущен')
    elif otvet == 1:
        print('     конец работы парсера', "--- %s seconds ---" % (time.time() - start_time_parser))
        bot.send_message(message.chat.id,
                         'Парсер завершил работу --- %s seconds ---' % (time.time() - start_time_parser))


@bot.message_handler(commands=['stop_parser'])
def start_message(message):
    global ENDCOMMAND
    ENDCOMMAND = 1  # установка команды на окончание работы парсера
    #  bot.send_message(message.chat.id, 'Парсер остановлен')


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
    bot.send_message(message.chat.id,
                     'Сейчас порог по коэффициенту = ' + str(POROGKOEF) + '. Чтобы поменять введи koef_<значение>')


@bot.message_handler(commands=['партия'])
def start_message(message):
    bot.send_message(message.chat.id, 'Сейчас порог по счёту в партии = ' + str(
        POROGWINSET) + '. Чтобы поменять введи winset_<значение>')


@bot.message_handler(commands=['HP'])  # вывод вспомогательных кнопок по команде /Help
def start_message(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)  # обьявление окна экранных кнопок
    button_start_parser = types.InlineKeyboardButton(text='Старт работы парсера', callback_data='start_parser')
    button_koef = types.InlineKeyboardButton(text='Текущий пороговый коэффициент', callback_data='koef')
    button_winset = types.InlineKeyboardButton(text='Текущий порог по победам соперника в партии',
                                               callback_data='winset')
    button_stop_parser = types.InlineKeyboardButton(text='Остановка работы парсера', callback_data='stop_parser')
    button_vse_match = types.InlineKeyboardButton(text='Вывод матчей которые на рассмотрении', callback_data='vse')
    button_na_stavku = types.InlineKeyboardButton(text='Вывод матчей на ставку', callback_data='stavka')
    button_na_time = types.InlineKeyboardButton(text='Вывод времени работы парсера', callback_data='time_spent')
    button_na_stek = types.InlineKeyboardButton(text='Вывод текущего стека найденных матчей', callback_data='stek')
    keyboard.add(button_start_parser, button_koef, button_winset, button_stop_parser, button_vse_match,
                 button_na_stavku, button_na_time, button_na_stek)  # добавление кнопок в окно
    bot.send_message(message.chat.id, 'Команды', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global SIGNAL
    if call.data == "koef":
        bot.send_message(call.message.chat.id,
                         'Сейчас порог по коэффициенту = ' + str(POROGKOEF) + '. Чтобы поменять введи koef_<значение>')
    elif call.data == "winset":
        bot.send_message(call.message.chat.id, 'Сейчас порог по счёту в партии = ' + str(
            POROGWINSET) + '. Чтобы поменять введи winset_<значение>')
    elif call.data == 'start_parser':
        global start_time_parser
        start_time_parser = time.time()
        bot.send_message(call.message.chat.id, 'Запускаю парсер')
        otvet = loop_zapros()
        if otvet == -1:
            bot.send_message(call.message.chat.id, 'Парсер уже запущен')
        elif otvet == 1:
            bot.send_message(call.message.chat.id, 'Парсер завершил работу')
    elif call.data == 'stop_parser':
        global ENDCOMMAND
        ENDCOMMAND = 1
    elif call.data == 'vse':
        SIGNAL = -1
        bot.send_message(call.message.chat.id, 'выводятся все матчи')
    elif call.data == 'stavka':
        SIGNAL = 1
        bot.send_message(call.message.chat.id, 'выводятся только матчи на ставку')
    elif call.data == 'time_spent':
        time_spent_mins = ((time.time() - start_time_parser) / 60)
        if time_spent_mins < 60:
            bot.send_message(call.message.chat.id, "Время работы парсера: --- %s mins ---" % time_spent_mins)
        else:
            time_spent_hours = time_spent_mins / 60;
            bot.send_message(call.message.chat.id, "Время работы парсера: --- %s hrs ---" % time_spent_hours)
    elif call.data == 'stek':
        bot.send_message(call.message.chat.id, 'Список найденных матчей:\n')
        if len(STEKMATCHEY) != 0:
            bot.send_message(call.message.chat.id, STEKMATCHEY)


@bot.message_handler(content_types=['text'])
def send_text(message):
    global POROGKOEF
    global POROGWINSET
    global start_time_parser
    print(message.text, message.chat.id)
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, 'Привет, Поросенок')

    elif message.text.find('koef_') == 0:  # смена коэффициента
        message_size = len(message.text)
        if message_size > 5:
            sl = slice(5, message_size, 1)
            new_koef = message.text[sl]
            if new_koef.replace('.', '').isdigit():
                POROGKOEF = float(new_koef)
                bot.send_message(message.chat.id, 'Порог коэффициента >=' + str(POROGKOEF))
                print(POROGKOEF)

    elif message.text.find('winset_') == 0:  # смена порога по выигрышам в партии
        message_size = len(message.text)
        if message_size > 7:
            sl = slice(7, message_size, 1)
            new_koef = message.text[sl]
            if new_koef.isdigit():
                POROGWINSET = int(new_koef)
                bot.send_message(message.chat.id, 'Порог выигрышей в партии <=' + str(POROGWINSET))
                print(POROGWINSET)

    elif message.text.lower() == 'time':  # тестовая ветка
        time_spent_mins = ((time.time() - start_time_parser) / 60)
        if time_spent_mins < 60:
            bot.send_message(message.chat.id, "Время работы парсера: --- %s mins ---" % time_spent_mins)
        else:
            time_spent_hours = time_spent_mins / 60;
            bot.send_message(message.chat.id, "Время работы парсера: --- %s hrs ---" % time_spent_hours)

    elif message.text.lower() == 'test':  # тестовая ветка
        leagues = parse()
        for league in leagues:
            for match in league:
                bot.send_message(message.chat.id,
                                 match.get('Title') + '\n' +
                                 match.get('Link') + '\n' +
                                 'Cчёт по сетам: ' + match.get('set1') + '--' + match.get('set2') + '\n' +
                                 'Счёт в сетах 1-го: ' + ''.join(
                                     str(e + '\t') for e in match.get('schetline1')) + '\n' +
                                 'Счёт в сетах 2-го: ' + ''.join(
                                     str(e + '\t') for e in match.get('schetline2')) + '\n' +
                                 'П1 = ' + match.get('bet1') + '\n' +
                                 'П2 = ' + match.get('bet2') + '\n' +
                                 'Проверка = ' + str(proverka_na_pobedu(match))
                                 )


# @bot.channel_post_handler()
# def channel(message):
#     print(message.chat.id)

if __name__ == '__main__':
    bot.polling()
