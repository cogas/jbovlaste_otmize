# -*- coding: utf-8 -*-

import json
import os.path
import xmltodict
import zipfile

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
        with zipfile.ZipFile(self.__zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
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
        checker = _OTMChecker(json_dict)
        checker.check()
        print("Loaded: {}.".format(filename))
        self.__json = json_dict

    @property
    def json(self):
        try:
            return self.__json
        except AttributeError:
            self.load()
        except Exception as err:
            raise err
        return self._json


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
        if not isinstance(json_dict["words"], list):
            raise NotOTMJson("words must be list")

    def _word_check(self, word):
        component_types = ["entry", "translations", "tags",
                           "contents", "variations", "relations"]
        if list(word) != component_types:
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
        if list(word["entry"]) != ["id", "form"]:
            raise NotOTMJson("Entry is broken: {}.".format(word))
        if not isinstance(word["entry"]["id"], int):
            ok = False
        if not isinstance(word["entry"]["form"], str):
            ok = False
        if not ok:
            raise NotOTMJson("Entry is broken: {}.".format(word))

    def _translations_check(self, word):
        err_message = "Translations is broken: {}.".format(word)
        if not isinstance(word["translations"], list):
            raise NotOTMJson(err_message)
        if list(word["translations"]) != ["title", "forms"]:
            raise NotOTMJson(err_message)
        for component in word["translations"]:
            err_message_2 = ("Translation is broken: {} in {}."
                             .format(component, word))
            ok = True
            if not isinstance(component["title"], str):
                ok = False
            if not isinstance(component["forms"], list):
                raise NotOTMJson(err_message_2)
            for form in component["forms"]:
                if not isinstance(form, str):
                    ok = False
            if not ok:
                raise NotOTMJson(err_message_2)

    def _contents_check(self, word):
        err_message = "Contents is broken: {}.".format(word)
        if not isinstance(word["contents"], list):
            raise NotOTMJson(err_message)
        if list(word["contents"]) != ["title", "text"]:
            raise NotOTMJson(err_message)
        for component in word["contents"]:
            err_message_2 = ("Content is broken: {} in {}."
                             .format(component, word))
            ok = True
            if not isinstance(component["title"], str):
                ok = False
            if not isinstance(component["text"], str):
                ok = False
            if not ok:
                raise NotOTMJson(err_message_2)

    def _variations_check(self, word):
        err_message = "Variations is broken: {}.".format(word)
        if not isinstance(word["variations"], list):
            raise NotOTMJson(err_message)
        if list(word["variations"]) != ["title", "form"]:
            raise NotOTMJson(err_message)
        for component in word["variations"]:
            err_message_2 = ("Content is broken: {} in {}."
                             .format(component, word))
            ok = True
            if not isinstance(component["title"], str):
                ok = False
            if not isinstance(component["form"], str):
                ok = False
            if not ok:
                raise NotOTMJson(err_message_2)

    def _relations_check(self, word):
        name = "relations"
        err_message = "Relations is broken: {}.".format(word)
        if not isinstance(word[name], list):
            raise NotOTMJson(err_message)
        if list(word[name]) != ["title", "entry"]:
            raise NotOTMJson(err_message)
        for component in word[name]:
            err_message_2 = ("Relation is broken: {} in {}."
                             .format(component, word))
            ok = True
            if not isinstance(component["title"], str):
                ok = False
            try:
                self._entry_check(component)
            except NotOTMJson:
                ok = False
            if not ok:
                raise NotOTMJson(err_message_2)

    def _tags_check(self, word):
        name = "tags"
        err_message = "Tags is broken: {}.".format(word)
        if not isinstance(word[name], list):
            raise NotOTMJson(err_message)
        for component in word[name]:
            ok = True
            err_message_2 = ("Tag is broken: {} in {}."
                             .format(component, word))
            if not isinstance(component, str):
                ok = False
            if not ok:
                raise NotOTMJson(err_message_2)
