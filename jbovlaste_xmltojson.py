# -*- coding: utf-8 -*-
import xmltodict, json

def make_dict_from_xml (lang):
    xmlname = 'xml/jbo-{}-xml.xml'.format(lang)
    with open(xmlname, encoding="utf-8") as f:
        xml = f.read()
    xmldict = xmltodict.parse(xml)
    jbodict = xmldict["dictionary"]["direction"][0]["valsi"]
    nldict = xmldict["dictionary"]["direction"][1]["nlword"]
    return jbodict, nldict

def save_json (dic, lang):
    _json = json.dumps(dic, indent=2, ensure_ascii=False)
    filename = 'json/jbo-{}.json'.format(lang)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(_json)
        print("Saved json.")
