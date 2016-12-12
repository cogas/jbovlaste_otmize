# -*- coding: utf-8 -*-
import xmltodict, json, zipfile

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
    def __init__(self, langs):
        self.langs = langs
        self.__zip_path = 'zip/{}-otmjson.zip'.format("-".join(langs))

    def zippy(self):
        filename_temp = 'otm-json/jbo-{}_otm.json'
        with zipfile.ZipFile(self.__zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for lang in self.langs:
                zf.write(filename_temp.format(lang))
            print("zipped: {}.".format(self.__zip_path))

import os.path

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
    def __init__(self, lang):
        self.__lang = lang

    def load(self):
        filename = 'otm-json/jbo-{}_otm.json'.format(self.__lang)
        if os.path.exists(filename):
            with open(filename, encoding='utf-8') as f:
                json_dict = json.loads(f.read())
                print("Loaded {}".format(filename))
        else:
            raise ValueError("{} doesn't exist.".format(filename))
        self.__json = json_dict

    @property
    def json(self):
        if not hasattr(self, "_OTMizedJsonDealer__json"):
            self.load()
        return self.__json
