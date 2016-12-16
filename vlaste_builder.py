# coding=utf-8

import re
import json
from collections import namedtuple, OrderedDict

from exceptions import (DictionaryBuildError, WordBuildError,
                        MetadataError, WordComponentsError)


class DictionaryBuilder:
    def __init__(self):
        self.words = []

    def append(self, word: str) -> None:
        if isinstance(word, WordBuilder):
            self.words.append(word)
        else:
            raise DictionaryBuildError("word must be Word.")

    @property
    def metadata(self):
        return self.__metadata

    @metadata.setter
    def metadata(self, metadata):
        if not isinstance(metadata, Metadata):
            raise DictionaryBuildError
        self.__metadata = metadata

    def build(self):
        built_dict = OrderedDict()
        built_dict.update({"words": [word.build() for word in self.words]})
        built_dict.update(self.metadata.as_dict())
        return built_dict

    def save(self, filename):
        predata = self.build()
        otmized_json = json.dumps(predata, indent=2, ensure_ascii=False)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(otmized_json)
            print("Written to {}.".format(filename))

    @classmethod
    def load(cls, otmized_json, builder=None):
        if builder is None:
            builder = WordBuilder
        result = cls()
        result.words.extend([builder.load(word)
                             for word in otmized_json["words"]])
        result.__metadata = {key: otmized_json[key]
                             for key in otmized_json.keys()
                             if key != "words"}
        return result


class Metadata:
    def __init__(self, zpdic=True):
        self.__dict = {}
        self.__dict["meta"] = {}
        self.__zpdic = zpdic
        if zpdic:
            self.__dict["zpdic"] = {}

    @property
    def langdata(self):
        return self.__dict["meta"]["lang"]

    def set_langdata(self, from_lang, to_lang):
        self.__dict["meta"]["lang"] = {"from": from_lang, "to": to_lang}

    def add_generated_date(self, date):
        self.__dict["meta"]["generated_date"] = str(date)

    def set_zpdic_data(self, zpdic_data):
        if not self.__zpdic:
            raise MetadataError("this metadata set don't support zpdic.")
        else:
            self.__dict["zpdic"].update(zpdic_data)

    def as_dict(self):
        return self.__dict


class WordBuilder:
    """Class building a Word object."""
    def __init__(self):
        self.translations = WordComponents(Translation)
        self.contents = WordComponents(Content)
        self.relations = WordComponents(Relation)
        self.variations = WordComponents(Variation)
        self.tags = []

    def add_translation(self, title, forms):
        self.translations.append(Translation(title, forms))

    def add_content(self, title, text):
        self.contents.append(Content(title, text))

    def add_relation(self, title, id_, form):
        self.relations.append(Relation(title, Entry(id_, form)))

    def add_variation(self, title, form):
        self.variations.append(Variation(title, form))

    def add_tag(self, tag):
        self.tags.append(tag)

    def set_entry(self, id_, form):
        self.entry = Entry(id_, form)

    def add(self, component):
        if isinstance(component, Translation):
            self.translations.append(component)
        elif isinstance(component, Content):
            self.contents.append(component)
        elif isinstance(component, Relation):
            self.relations.append(component)
        elif isinstance(component, Variation):
            self.variations.append(component)
        elif isinstance(component, Entry):
            self.entry = component
        else:
            WordBuildError("component couldn't match.")

    def build(self):
        _entry = self.entry._asdict()
        _translations = self.translations.build()
        _contents = self.contents.build()
        _variations = self.variations.build()
        _relations = self.relations.build()
        return OrderedDict([
            ("entry", _entry),
            ("translations", _translations),
            ("tags", self.tags),
            ("contents", _contents),
            ("variations", _variations),
            ("relations", _relations)
        ])

    @classmethod
    def load(cls, dic):
        result = cls()
        result.entry = Entry(dic["entry"]["id"], dic["entry"]["form"])
        result.translations.extend([Translation(**trsl)
                                    for trsl in dic["translations"]])
        result.tags = dic["tags"]
        result.contents.extend([Content(**cnt) for cnt in dic["contents"]])
        result.variations.extend([Variation(**var)
                                  for var in dic["variations"]])
        result.relations.extend([Relation(relation["title"],
                                          Entry(**relation["entry"]))
                                 for relation in dic["relations"]])
        return result

    def __repr__(self):
        return "<WordBuilder: {}>".format(self.entry)


class JbovlasteWordBuilder(WordBuilder):
    def delete_dollar(self):
        """definition の $x_n$ を x_n に変える。"""
        sentence = self.translations[0].forms[0]
        self.translations[0].forms[0] = sentence.replace("$", "")
        return self

    def glosswords(self):
        if 'glossword' not in self.contents.keys():
            return []
        glosses_text = self.contents.find('glossword')[1].text
        glosses = glosses_text.split("\n")
        return [gloss.strip("- ") for gloss in glosses]

    def add_glossword(self, glossword):
        if 'glossword' in self.contents.keys():
            glosses_text = self.contents.find('glossword')[1].text
            glosses_text = '\n' + '- ' + glossword
            self.contents.renew('glossword', glosses_text)
        else:
            self.contents.append(Content('glossword', '- ' + glossword))

    def keywords(self):
        if 'keyword' not in self.contents.keys():
            return []
        glosses_text = self.contents.find('keyword')[1].text
        glosses = glosses_text.split("\n")
        return {i: re.sub(r"^\[\d\]: ", "", gloss)
                for i, gloss in enumerate(glosses, 1)}


class WordBuilderForJapanese(JbovlasteWordBuilder):
    """Notes内のごたごたを上手く切り分け別に登録するメソッドを独自にもつ。
    Basically, all you need is call for ``whole_execute`` method! :)"""

    def add_split_notes_to_content(self):
        """split_notesが返した辞書をもとに word に content を追加する。"""
        if "notes" in self.contents.keys():
            new_components = self.split_notes()
            # keywords = ["大意", "読み方", "語呂合わせ", "関連語"]
            for keyword, text in new_components.items():
                if keyword == "notes":
                    self.contents.renew("notes", text)
                else:
                    self.add(Content(keyword, text))
        return self

    def split_notes(self):
        """notesをkeywordsごとに分け、それぞれの項目の辞書を返す。"""
        keywords = ["大意", "読み方", "語呂合わせ", "関連語"]
        regex_template = r'・\s*(?={}\s*[:：])'
        regex = r'{}|{}|{}|{}'.format(*(regex_template.format(keyword)
                                        for keyword in keywords))
        regex_template2 = r'{}\s*[:：]\s*'
        if "notes" not in self.contents.keys():
            return {}
        dic = {}
        dic["notes"] = ""
        for phrase in re.split(regex, self.contents.find("notes")[1].text):
            for keyword in keywords:
                if keyword in phrase:
                    s = re.sub(regex_template2.format(keyword), "", phrase)
                    s = re.sub(r'\s*$', "", s)
                    dic[keyword] = s
                    break
            else:
                dic["notes"] += re.sub(r'\s*$', "", phrase)
        return dic

    def example_extract(self):
        """Extract '「…／…」' expressions from notes,
        adding them to contents as '用例' component"""
        regex = r'「[^／]+／[^／]+」'
        if "notes" in self.contents.keys():
            notes_text = self.contents.find("notes")[1].text
            examples = re.findall(regex, notes_text)
            if examples:
                self.contents.renew("notes", re.sub(regex, "", notes_text))
                self.add(Content("用例", "\n".join(examples)))
        return self

    def integrate_gloss(self):
        """Integrate '大意' component with 'glossword' component."""
        if "大意" in self.contents.keys():
            pre_gloss = self.contents.find("大意")[1].text
            if "glossword" in self.contents.keys():
                glosses = self.contents.find("glossword")[1].text
                if pre_gloss not in self.glosswords():
                    self.add_glossword(pre_gloss)
            else:
                self.add(Content("glossword", pre_gloss))
            del self.contents[self.contents.find("大意")[0]]
        return self

    def sort_contents(self):
        # 大意 は gloss に統合している。
        sorting = ["notes", "読み方", "glossword", "keyword", "用例",
                   "語呂合わせ", "関連語", "rafsi", "username"]
        self.contents.sort_bytitle(sorting)
        return self

    def delete_emptynotes(self):
        """Delete a notes component with no text."""
        cs = self.contents
        if ("notes" in cs.keys() and
                re.search(r'^\s*$', cs.find("notes")[1].text)):
            del self.contents[self.contents.find("notes")[0]]
        return self

    def whole_execute(self):
        """All is done well."""
        self.add_split_notes_to_content().example_extract()
        self.integrate_gloss().sort_contents().delete_emptynotes()
        return self

Entry = namedtuple("Entry", "id form")
Translation = namedtuple("Translation", "title forms")
Content = namedtuple("Content", "title text")
Variation = namedtuple("Variation", "title form")


class Relation:
    """mostly same with namedtuple,
    except that ``_asdict`` method works well for Entry object."""
    def __init__(self, title, entry):
        self._title = title
        self._entry = entry

    @property
    def title(self):
        return self._title

    @property
    def entry(self):
        return self._entry

    def _asdict(self):
        return OrderedDict([('title', self.title),
                            ('entry', self.entry._asdict())])


class WordComponents(list):
    def __init__(self, component_type):
        self.__type = component_type

    def append(self, component):
        if not isinstance(component, self.__type):
            raise WordComponentsError("component must be {}."
                                      .format(self.__type))
        else:
            super().append(component)

    def keys(self):
        return [component.title for component in self]

    def find(self, title):
        generator = ((i, component) for i, component in enumerate(self)
                     if component.title == title)
        try:
            result = next(generator)
        except StopIteration:
            raise WordComponentsError("No component has the 'title'.")
        return result

    def renew(self, title, new_value):
        self[self.find(title)[0]] = self.__type(title, new_value)

    def sort_bytitle(self, titles):
        """titlesの順に並べる。インプレースであることに注意。
        titlesに記載のないtitleをもつ要素はその順番を保持したまま後方に寄る。"""
        titles.reverse()
        for title in titles:
            if title in self.keys():
                i, component = self.find(title)
                del self[i]
                self[0:0] = [component]

    def build(self):
        return [component._asdict() for component in self]


class ZpDICInfo:
    DEFAULT_ALPHABET_ORDER = ".'aAbBcCdDeEfFgGiIjJkKlLmMnNoOpPrRsStTuUvVxXyYzZ"

    def __init__(self, lang):
        self.__lang = lang
        self.alphabetOrder()

    def plainInformationTitles(self, titles):
        self._plainInformationTitles = titles

    def alphabetOrder(self, order=DEFAULT_ALPHABET_ORDER):
        self._alphabetOrder = order

    def defaultWord(self, word):
        if isinstance(word, WordBuilder):
            word = word.build()
        self._defaultWord = word

    def informationTitleOrder(self, order):
        self._informationTitleOrder = order

    def set_by_lang(self):
        self.plainInformationTitles(['username', 'rafsi'])
        if self.__lang == 'ja':
            self._plainInformationTitles.extend(['読み方', '語呂合わせ'])

    def build(self):
        result_dict = {}
        for attr in ['_alphabetOrder',
                     '_defaultWord',
                     '_plainInformationTitles',
                     '_informationTitleOrder']:
            if hasattr(self, attr):
                result_dict[attr[1:]] = getattr(self, attr)
        return result_dict
