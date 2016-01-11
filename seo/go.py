from django.shortcuts import render
import xml.etree.ElementTree as ET
from urllib.parse import quote
import requests
import re
from seo.seo.secret import secret

answers = {}
old_keys = set()
rus_aux = {'под', 'так', 'на', 'от', 'по', 'над', 'для', 'не'}


class ClearData:
    def __init__(self, old_keys=old_keys):
        self.old_keys = old_keys
        self.new_bolds = dict()

    def check(self, word):
        len_word = len(word)
        if len_word > 4:
            for old in self.old_keys:
                if old[:len_word-2] == word[:-2]:
                    return False
            return True
        elif len_word > 3:
            for old in self.old_keys:
                if old[:len_word-1] == word[:-1]:
                    return False
            return True
        else:
            if word in self.old_keys:
                return False
            return True

    def add(self, word):
        if len(word) > 1 and (not self.old_keys or self.check(word)):
            len_word = len(word)
            if len_word > 4:
                for old in self.new_bolds:
                    if old[:len_word-2] == word[:-2]:
                        self.new_bolds[old] += 1
                        break
                else:
                    self.new_bolds[word] = 1
            elif len_word > 3:
                for old in self.new_bolds:
                    if old[:len_word-1] == word[:-1]:
                        self.new_bolds[old] += 1
                        break
                else:
                    self.new_bolds[word] = 1
            else:
                if word in self.new_bolds:
                    self.new_bolds[word] += 1
                else:
                    self.new_bolds[word] = 1

    def get_sorted(self, min_value=None):
        temp = sorted(zip(self.new_bolds.keys(), self.new_bolds.values()), key=lambda x: x[1], reverse=True)
        if min_value:
            return filter(lambda x: x[1] > min_value, temp)
        return temp


def open_urls(text, regions, pages):
    keys = text.split('\n')
    begin_set(keys)
    for key in keys:
        key = quote(key)
        url = 'https://yandex.ru/search/xml?' + secret +\
                 '&query=' + key +\
                 '&lr=' + regions +\
                 '&l10n=ru'\
                 '&sortby=rlv'\
                 '&groupby=attr%3D%22%22.mode%3Dflat.groups-on-page%3D' + pages +\
                 '.docs-in-group%3D1&'
        answers[url] = requests.get(url).content.decode()


def begin_set(keys):
    for key in keys:
        words = key.split()
        for word in words:
            word = word.lower()
            old_keys.add(word)


def parse_snip():
    title = []
    passage =[]
    for url in answers:
        root = ET.fromstring(answers[url])
        for line in root.iter('title'):
            words = []
            for word in line.itertext():
                word = word.strip()
                if word: words.append(word)
            temp_line = ' '.join(words).replace(' ,', '').replace(' .', '')
            title.append((temp_line, len(temp_line)))
        for line in root.iter('passage'):
            words = []
            for word in line.itertext():
                word = word.strip()
                if word: words.append(word)
            temp_line = ' '.join(words).replace(' ,', '').replace(' .', '')
            passage.append((temp_line, len(temp_line)))
    return zip(title, passage)


def aver_data(snips):
    count = 0
    len_titles = 0
    len_descriptions = 0
    list_words = ClearData()
    for snip in snips:
        count += 1
        len_titles += snip[0][1]
        len_descriptions += snip[1][1]
        for word in re.findall('\w+', snip[0][0]):
            word = word.lower()
            if word not in rus_aux:
                list_words.add(word)
        for word in re.findall('\w+', snip[1][0]):
            word = word.lower()
            if word not in rus_aux:
                list_words.add(word)

    return int(len_titles/count), int(len_descriptions/count), list_words.get_sorted(3)


def find_bold(text, regions, pages):
    keys = text.split('\n')
    begin_set(keys)
    open_urls(text, regions, pages)
    temp = ClearData()
    for url in answers:
        root = ET.fromstring(answers[url])
        for bold in root.iter('hlword'):
            word = bold.text.strip().lower()
            temp.add(word)
    return temp.get_sorted()


def seo_analistic(request):
        keys = request.POST.get('keys')
        regions = request.POST.get('region')
        pages = request.POST.get('pages')
        answers.clear()
        old_keys.clear()
        bolds = find_bold(keys, regions, pages)
        parsed = list(parse_snip())
        average = aver_data(parsed)
        content_dict = {'bolds': bolds,
                        'titles': parsed,
                        'average': average
                        }
        return render(request, 'answer.html', content_dict)
