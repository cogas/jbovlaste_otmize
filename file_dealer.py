# -*- coding: utf-8 -*-

import json
import os.path
import xmltodict
import zipfile
from exceptions import NotOTMJson

class JbovlasteXmlDealer:
    def __init__(self, lang):
        self.__has_dict = False
        self.__has_json = False
        self.__lang = lang

    def make_dict(self):
        if self.__has_dict:
            return self.__jbodict, self.__nldict
        else:
            xmlname = 'xml/jbo-{}-xml.xml'.format(self.__lang)
            with open(xmlname, encoding="utf-8") as f:
                xml = f.read()
            xmldict = xmltodict.parse(xml)
            self.__jbodict = xmldict["dictionary"]["direction"][0]["valsi"]
            self.__nldict = xmldict["dictionary"]["direction"][1]["nlword"]
            self.__has_dict = True
            return self.__jbodict, self.__nldict

    def make_json(self):
        if self.__has_json:
            return self.__json
        else:
            jbodict, _ = self.make_dict()
            self.__json = json.dumps(jbodict, indent=2, ensure_ascii=False)
            self.__has_json = True
            return self.__json

    def save_json(self):
        filename = 'json/jbo-{}.json'.format(self.__lang)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.make_json())
            print("Saved json.")


class ZipDealer:
    def __init__(self, pathname):
        self.__pathname = pathname

    def zippy(self, filenames):
        with zipfile.ZipFile(self.__pathname, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename in filenames:
                zf.write(filename)
            print("Zipped: {}.".format(self.__pathname))


class JbovlasteZipDealer(ZipDealer):
    def __init__(self, langs):
        self.langs = langs
        pathname = 'zip/{}-otmjson.zip'.format("-".join(langs))
        super().__init__(pathname)

    def zippy(self):
        filename_template = 'otm-json/jbo-{}_otm.json'
        filenames = (filename_template.format(lang) for lang in self.langs)
        super().zippy(filenames)


class RawdictDealer:
    def __init__(self, lang):
        self.__lang = lang

    def load(self):
        filename = 'json/jbo-{}.json'.format(self.__lang)
        if os.path.exists(filename):
            with open(filename, encoding='utf-8') as f:
                rawdict = json.loads(f.read())
                print("Loaded {}".format(filename))
        else:
            print("file '{}' doesn't exist. Generating from xml file.".format(filename))
            xml_dealer = JbovlasteXmlDealer(self.__lang)
            rawdict, _ = xml_dealer.make_dict()
            print("OK, loaded.")
            xml_dealer.save_json()
        return rawdict


class OTMizedJsonDealer:
    def load(self, filename):
        if not filename.endswith(".json"):
            raise ValueError("filename must ends with '.json'.")
        if not os.path.exists(filename):
            raise ValueError("{} doesn't exist.".format(filename))
        with open(filename, encoding='utf-8') as f:
            json_dict = json.loads(f.read())
            print("Loaded.")
        print("Checking..")
        checker = _OTMChecker(json_dict)
        checker.check()
        print("OK: {}.".format(filename))
        self.__json = json_dict

    @property
    def json(self):
        try:
            return self.__json
        except AttributeError:
            self.load()
        except Exception as err:
            raise err
        return self.__json


class JbovlasteOTMizedJsonDealer(OTMizedJsonDealer):
    def __init__(self, lang):
        self.__lang = lang
        self.__filename = 'otm-json/jbo-{}_otm.json'.format(self.__lang)

    def load(self):
        super().load(self.__filename)


class _OTMChecker():
    """Should shorten and revise _XXX_check method. REDUNDUNT!"""
    def __init__(self, json_dict):
        self.json = json_dict

    def check(self):
        self._words_check()
        for word in self.json["words"]:
            self._word_check(word)

    def _words_check(self):
        if 'words' not in self.json.keys():
            raise NotOTMJson("Not have words attribute.")
        if not isinstance(self.json["words"], list):
            raise NotOTMJson("words must be list")

    def _word_check(self, word):
        component_types = {"entry", "translations", "tags",
                           "contents", "variations", "relations"}
        if set(word) != component_types:
            lacks = [comp_type for comp_type in component_types
                     if comp_type not in list(word)]
            raise NotOTMJson("Attributes lack: {}.".format(word))

        self._entry_check(word)
        self._translations_check(word)
        self._tags_check(word)
        self._contents_check(word)
        self._variations_check(word)
        self._relations_check(word)

    def _entry_check(self, word):
        ok = True
        if set(word["entry"]) != {"id", "form"}:
            raise NotOTMJson("Entry is broken: {}.".format(word))
        if not isinstance(word["entry"]["id"], int):
            ok = False
        if not isinstance(word["entry"]["form"], str):
            ok = False
        if not ok:
            raise NotOTMJson("Entry is broken: {}.".format(word))

    def __word_components_check(self, word, name, component_attrs, attr_type):
        err_message = "{} is broken: {}.".format(name, word)
        if not isinstance(word[name], list):
            raise NotOTMJson(err_message)
        for component in word[name]:
            err_message_2 = ("{} is broken: {} in {}."
                             .format(name[:-1], component, word))
            ok = True
            if set(component) != set(component_attrs):
                raise NotOTMJson(err_message)
            if not isinstance(component["title"], str):
                ok = False
            attr = [x for x in component_attrs if x != "title"][0]
            if not isinstance(component[attr], attr_type):
                ok = False
            if not ok:
                raise NotOTMJson(err_message_2)

    def _translations_check(self, word):
        self.__word_components_check(word, "translations",
                                     {"title", "forms"}, list)
        for component in word["translations"]:
            ok = True
            for form in component["forms"]:
                if not isinstance(form, str):
                    ok = False
            if not ok:
                raise NotOTMJson("form is broken: {} in {}."
                                 .format(form, word))

    def _contents_check(self, word):
        self.__word_components_check(word, "contents",
                                     {"title", "text"}, str)

    def _variations_check(self, word):
        self.__word_components_check(word, "variations",
                                     {"title", "form"}, str)

    def _relations_check(self, word):
        self.__word_components_check(word, "relations",
                                     {"title", "entry"}, dict)
        for component in word["relations"]:
            ok = True
            try:
                self._entry_check(component)
            except NotOTMJson:
                ok = False
            if not ok:
                raise NotOTMJson("entry in relation is broken: {} in {}"
                                 .format(component, word))

    def _tags_check(self, word):
        name = "tags"
        err_message = "{} is broken: {}.".format(name, word)
        if not isinstance(word[name], list):
            raise NotOTMJson(err_message)
        for component in word[name]:
            ok = True
            err_message_2 = ("name is broken: {} in {}."
                             .format(component, word))
            if not isinstance(component, str):
                ok = False
            if not ok:
                raise NotOTMJson(err_message_2)
