# -*- coding: utf-8 -*-

import re
from collections import OrderedDict as Odict
import otmjson as otm
from otmjson import hqueryx, hqueryi, has, sort_bytitle

def splitnotes_(notes):
    reg_template = r'・\s*(?={}\s*[:：])'
    _l = []
    opts = ["大意", "読み方", "語呂合わせ", "関連語"]
    for x in opts:
        _l.append(reg_template.format(x))
    reg = r'{}|{}|{}|{}'.format(*_l)
    reg_template2 = r'{}\s*[:：]\s*'
    result = []
    dic = {}
    for phrase in re.split(reg, notes):
        for opt in opts:
            if opt in phrase:
                s = re.sub(reg_template2.format(opt), "", phrase)
                s = re.sub(r'\s*$', "", s)
                dic[opt] = s
                break
        else:
            result.append(re.sub(r'\s*$', "", phrase))
    result.append(dic)
    return result

def splitnotes(word):
    cs = word["contents"]
    if has(cs, "notes"):
        notes = hqueryx(cs, "notes")["text"]
        return splitnotes_(notes)
    else:
        return []

def goodnotes(word):
    cs = word["contents"]
    if has(cs, "notes"):
        after = splitnotes(word)
        hqueryx(cs, "notes")["text"] = ""
        for elem in after:
            if isinstance(elem, dict):
                keys = ["大意", "読み方", "語呂合わせ", "関連語"]
                for k in keys:
                    if k in elem:
                        cs.append({"title":k, "text":elem[k]})
            else:
                hqueryx(cs, "notes")["text"] += elem + " "
        example_extract(word)
    return word

def example_extract(word):
    '''
    notesから「…／…」形式を抜き出して、用例としてcontentsに加える。
    '''
    reg = r'「[^／]+／[^／]+」'
    cs = word["contents"]
    notes = hqueryx(cs, "notes")
    example_ls = re.findall(reg, notes["text"])
    if example_ls:
        notes["text"] = re.sub(reg, "", notes["text"])
        cs.append(otm.content("用例", "\n".join(example_ls)))
    return word

def sortcontents(word):
    # 大意 は gloss に統合している。
    sorting = ["notes", "読み方", "gloss", "keyword", "用例", "語呂合わせ", "関連語", "rafsi", "username"]
    sort_bytitle(word["contents"], sorting)
    return word

def integrate_gloss(word):
    cs = word["contents"]
    if has(cs, "大意"):
        glossy = hqueryx(cs, "大意")
        if has(cs, "gloss"):
            gloss = hqueryx(cs, "gloss")
            if glossy["text"] not in gloss["text"].split(", "):
                gloss["text"] += ", " + glossy["text"]
        else:
            cs.append(otm.content("gloss", glossy["text"]))
        del cs[hqueryi(cs, "大意")]
    return word

def delete_emptynotes(word):
    '''
    空白記号のみの notes を消去。
    '''
    cs = word["contents"]
    if has(cs, "notes") and re.search(r'^\s*$', hqueryx(cs, "notes")["text"]):
        del cs[hqueryi(cs, "notes")]
    return word

def delete_dollar(word):
    '''
        definition の $x_n$ を x_n に変える。
    '''
    s = word["translations"][0]["forms"][0]
    word["translations"][0]["forms"][0] = s.replace("$", "")
    return word

from time import time
import sys
import concurrent.futures
import itertools
def add_relations_for_multi(task_words, entry_dict):
    '''
    r"{[a-zA-Z']}" に該当する単語のうち、エントリーのあるものだけを relations に加える。
    "ja" の場合「・関連語」も対象にする。
    '''
    regex = r"\{[a-zA-Z']+\}"
    #entry_dict = entry_dict.copy()
    for word in task_words:
        cs = word["contents"]
        _ls = []
        if has(cs, "notes"):
            _ls = re.findall(regex, hqueryx(cs, "notes")["text"])
        if has(cs, "関連語"):
            _ls += re.findall(regex, hqueryx(cs, "関連語")["text"])
        _ls = [re.sub(r'^[^a-zA-Z]+', '', re.sub(r'[^a-zA-Z]+$', '', e)) for e in _ls]
        relations = []
        for rel in _ls:
            for entry in entry_dict[rel[0]]:
                if entry["form"] == rel:
                    relations.append(otm.relation("", entry))
                    break
        word["relations"] = relations
    return task_words

def add_relations(words):
    '''
    r"{[a-zA-Z']}" に該当する単語のうち、エントリーのあるものだけを relations に加える。
    "ja" の場合「・関連語」も対象にする。
    '''
    regex = r"\{[a-zA-Z']+\}"
    entry_list = [word["entry"] for word in words]
    letters = ".abcdefgijklmnoprstuvwxyz"
    letters += letters[1:].upper()
    word_dict = {letter: [word for word in words if word["form"][0] == letter] for letter in letters}
    add_relations_for_multi(words, word_dict)
