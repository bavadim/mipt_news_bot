#!/usr/bin/env python3

import os
from lxml import etree
import lxml.html as html
from urllib.request import urlopen
from dateutil import parser
import datetime
import json
import telegram

def fresh_news(sorted_news):
    last_update = datetime.datetime.now()
    last_news_digest = 'UNKNOWN'
    if os.path.exists('news.lock'):
        with open('news.lock', 'r') as f:
            lock = json.load(f)
            if lock:
                last_update = parser.parse(lock['last_update'])
                last_news_digest = lock['last_news_digest']

    res = []
    unknown = []
    for n in sorted_news:
        if n['date'] > last_update:
            res.append(n)
        elif n['date'] == last_update:
            unknown.append(n)
        else:
            break

    unknown.reverse()
    is_fresh = False
    news_on_day_of_update = []
    for n in unknown:
        if is_fresh:
            news_on_day_of_update.append(n)

        if n['url'] == last_news_digest:
            is_fresh = True
 
    news_on_day_of_update.reverse()

    return res + news_on_day_of_update 

def posts():
    page = html.parse(urlopen("https://mipt.ru/news/"))
    news = page.xpath("//div[contains(@class, 'news-list')]/div[contains(@class, 'news-item')]")
    res = []
    for n in news:
        title = n.xpath(".//a[contains(@class, 'title')]/text()")
        title = title[0] if title else None

        url = n.xpath(".//a[contains(@class, 'title')]/@href")
        if url:
            url = 'https://mipt.ru' + url[0]
        else:
            continue

        date = n.xpath(".//span[contains(@class, 'date')]/text()")
        date = parser.parse(date[0]) if date else None

        text = n.xpath(".//div[contains(@class, 'summary')]/div/text()")
        if not text:
            text = n.xpath(".//div[contains(@class, 'summary')]/text()")
        text = text[0].replace('\n', '').strip() if text else None

        res.append({ 'title': title, 'date': date, 'text': text, 'url': url })
    #return fresh_news(res)
    return res

def save_checkpoint(sorted_news):
    the_newest = sorted_news[0]
    last_update = the_newest['date']
    last_news_digest = the_newest['url']
    with open('news.lock', 'w+') as f:
        f.write(json.dumps({ 'last_update': time.strftime('{%Y-%m-%d}'), 'last_news_digest': last_news_digest }))

def main(telegram_token, channel_name):
    bot = telegram.Bot(telegram_token)
    news = posts()
    for post in news:
        bot.sendMessage(chat_id='@' + channel_name, text=post['url'])
    save_checkpoint(news)

if __name__ =="__main__":
    token = os.environ['TELEGRAM_TOKEN']
    main(token, 'MiptNews test')


