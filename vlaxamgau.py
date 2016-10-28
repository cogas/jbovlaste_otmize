# -*- coding: utf-8 -*-

import re
from collections import OrderedDict as Odict
import otmjson
from otmjson import hqueryx, hqueryi, has, sort_bytitle
from otmjson import content as make_content

def content(word, title):
    return otmjson.queryx(word["contents"], title)

# 「.+[/／].+」 を用例として抜き出せ。
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
    if (word, "notes"):
        notes = content(word, "notes")[0]["text"]
        return splitnotes_(notes)

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
    notes["text"] = re.sub(reg, "", notes["text"])
    cs.append(make_content("用例", "\n".join(example_ls)))
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
            cs.append(make_content("gloss", glossy["text"]))
        del cs[hqueryi(cs, "大意")]
    return word

def delete_emptynotes(word):
    cs = word["contents"]
    if has(cs, "notes") and re.search(r'^\s*$', hqueryx(cs, "notes")["text"]):
        del cs[hqueryi(cs, "notes")]
    return word

def delete_dollar(word):
    '''
        definition の $x_n$ を xn に変える。
    '''
    s = word["translations"][0]["forms"][0]
    word["translations"][0]["forms"][0] = s.replace("$", "")
    return word
