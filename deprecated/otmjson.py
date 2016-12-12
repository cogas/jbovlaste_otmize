# -*- coding: utf-8 -*-

'''
* >> words, zpdic, lang
words : [word]
  word >> entry, translations, tags, contents, variations, relations
    entry >> id, form
      id : NUMBER
      form : STRING  // {単語}
    translations : [translation]
    translation >> forms, title
      forms : [STRING] // {訳語}
      title : STRING // 自動詞, 他動詞, 名詞
    tags : [STRING] // 基本, 頻出
    contents : [content]
    content >> text, title
      text : STRING
      title : STRING  // 語法,
    variations : [variation]
    variation >> form, title
      form : STRING
      title : STRING // 現在形, 過去形
    relations : [relation]
    relation >> entry, title
      title : STRING // 類義語, 対義語
zpdic >> alphabetOrder
  alphabetOrder : STRING // !zyxwvutsrqponmlkjihgfedcba
lang >> from, to
  from : STRING // ISO
  to : STRING // ISO
'''

'''
OTM-jsonを操作するとき、[{title:, XXX:}]の型によく出くわす。
そこで、{title:, XXX:} を BiDict とし、これのリストを BiDicts とする。
content, variation, relation は XXX の違いであり、
これらをリストにしたものはすべて BiDicts として処理できる。
'''

class BiDict(dict):
    ALIAS_DICT = {
        "Content":"text", "Variation":"form",
        "Relation":"entry","Translation":"forms"
        }

    def __init__ (self, title, x, alias="BiDict", xname="x"):
        self.alias = alias
        if alias in self.ALIAS_DICT:
            xname = self.ALIAS_DICT[alias]
        self.xname = xname
        self["title"] = title
        self[xname] = x

    def __repr__ (self):
        _x = self.x
        _x = "'{}...'".format(_x) if len(_x) >=6 else str(_x)
        return '<{}|{} : {}>'.format(self.alias, self["title"], _x)

    @property
    def x(self):
        return self[self.xname]

    @x.setter
    def x(self, x):
        self[self.xname] = x

    @staticmethod
    def mkfrom(dic, alias="BiDict"):
        _xname = [x for x in dic.keys() if x != "title"][0]
        if alias in BiDict.ALIAS_DICT:
            xname = BiDict.ALIAS_DICT[alias]
            if xname != xname:
                raise ValueError("inconsistent. {} vs {}".format(xname, _xname))
        else:
            xname = _xname
        return BiDict(dic["title"], dic[xname], alias, xname)

class BiDicts(list):
    def __init__(self, bidicts):
        for bidict in bidicts:
            if not isinstance(bidict, BiDict):
                raise ValueError("Some of the elements are not BiDict instances.")
            self.append(bidict)

    @staticmethod
    def mkfrom(dicts, alias="BiDict"):
        _ls = []
        for dic in dicts:
            _ls.append(BiDict.mkfrom(dic, alias))
        return BiDicts(_ls)

    def query(self, title):
        return [(i,x) for i,x in enumerate(self) if x["title"] == title]

    def queryx(self, title):
        return [e[1] for e in self.query(title)]

    def hquery(self, title):
        return self.query(title)[0]

    def hqueryx(self, title):
        return self.queryx(title)[0]

    def has(self, title):
        return bool(self.query(title))

    def sort_by(self, titles):
        sort_bytitle(self, titles)


class Entry(dict):
    def __init__(self, form, id):
        self["form"] = form
        self["id"] = id

    def __repr__(self):
        return '<Entry{}: {}>'.format(self["id"], self["form"])

    @property
    def x(self):
        return self["form"]

    @staticmethod
    def mkfrom(dic):
        return Entry(dic["form"], dic["id"])

def content(title, text):
    return BiDict(title, text, alias="Content")

def variation(title, form):
    return BiDict(title, form, alias="Variation")

def translation(title, forms):
    return BiDict(title, forms, alias="Translation")

def relation(title, entry):
    return BiDict(title, entry, alias="Relation")

class Word(dict):
    def __init__(self, entry, translations=[], tags=[], contents=[], variations=[], relations=[]):
        self["entry"] = entry
        self["translations"] = translations
        self["tags"] = tags
        self["contents"] = contents
        self["variations"] = variations
        self["relations"] = relations

    def mkfrom (dic):
        en = Entry.mkfrom(dic["entry"])
        tr = BiDicts.mkfrom(dic["translations"], alias="Translation")
        ta = dic["tags"].copy()
        co = BiDicts.mkfrom(dic["contents"], alias="Content")
        va = BiDicts.mkfrom(dic["variations"], alias="Variation")
        re = BiDicts.mkfrom(dic["relations"], alias="Relation")
        return Word(en, tr, ta, co, va, re)

    def query(self, q, title):
        return self[q].query(title)

    def has(self, q, title):
        return bool(self.query(q, title))

    def has_tag(self, tag):
        return bool(tag in self["tags"])

    def __repr__(self):
        return '<Word: {}>'.format(self["entry"]["form"])

    @property
    def x(self):
        return dict(self)

    @property
    def i(self):
        return self["entry"]

class Words(list):
    def __init__(self, words=[]):
        for word in words:
            if isinstance(word, Word):
                self.append(word)
            else:
                raise ValueError()

    def __repr__(self):
        if self == []:
            return '[]'
        if len(self) >= 7:
            formatted = list(self)[:7]
            extra = "..."
        else:
            formatted = list(self)
            extra = ""
        formatted = list(map(str, formatted))
        return '[{}{} total:{} words]'.format(", ".join(formatted), extra, len(self))

    @staticmethod
    def mkfrom(words):
        _ls = Words()
        for wordic in words:
            _ls.append(Word.mkfrom(wordic))
        return _ls

    def contains(self, form):
        return Words([word for word in self if form in word.i.x ])

    @property
    def x(self):
        _ls = Words()
        for word in self:
            _ls = word.x
        return _ls

def query(obj, title):
    '''
        [{title:, XXX:}] 型のリストに対して、title を key として
        該当する要素のリストインデックスとXXXの内容のタプルを返す。
    '''
    return [(i,x) for i,x in enumerate(obj) if x["title"] == title]

def queryi(obj, title):
    return [e[0] for e in query(obj, title)]

def queryx(obj, title):
    '''
        [{title:, XXX:}] 型のリストに対して、それぞれの要素の title を key としてフィルターする。
    '''
    return [e[1] for e in query(obj, title)]

def hquery(obj, title):
    '''
        title がユニークな場合はこちらを推奨。
        リストではなく該当する要素のインデックスとその内容のタプルを返す。
    '''
    return query(obj,title)[0]

def hqueryi(obj, title):
    '''
        title がユニークな場合はこちらを推奨。
        リストではなくインデックス自体が返る。
    '''
    return queryi(obj,title)[0]

def hqueryx(obj, title):
    '''
        title がユニークな場合はこちらを推奨。
        リストではなく内容自体が返る。
    '''
    return queryx(obj, title)[0]

def has(obj, title):
    return bool(query(obj, title))

def sort_bytitle(obj, titles):
    '''
        obj を titles の順に並べる。インプレースであることに注意。
        titles に記載のない title はその順番を保持したまま、後方に寄る。
    '''
    titles.reverse()
    for title in titles:
        for i,x in query(obj, title):
            del obj[i]
            obj[0:0] = [x]

def sorted_bytitle(obj, titles):
    '''
        sort_bytitle の非破壊版。
    '''
    obj = obj.copy()
    sort_bytitle(obj, titles)
    return obj
