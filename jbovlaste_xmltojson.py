# -*- coding: utf-8 -*-
from collections import OrderedDict as Odict
import xmltodict, json
import goodnotes

def make_xmldict(xmlname):
    with open(xmlname, encoding="utf-8") as f:
        xml = f.read()

    xmldict = xmltodict.parse(xml)
    jbodict = xmldict["dictionary"]["direction"][0]["valsi"]
    nldict = xmldict["dictionary"]["direction"][1]["nlword"]
    return jbodict, nldict

print("---xmltojson--- ...")

jbopondict, ponjbodict = make_xmldict('xml/jbo-jpn-xml.xml')
jboglidict, glijbodict = make_xmldict('xml/jbo-eng-xml.xml')
jbojbodict, _ = make_xmldict('xml/jbo-jbo-xml.xml')

# alias for ISO
jbojpndict = jbopondict
jboengdict = jboglidict

print("generated dictionary.")

jboponjson = json.dumps(jbopondict, indent=2, ensure_ascii=False)
jboglijson = json.dumps(jboglidict, indent=2, ensure_ascii=False)
jbojbojson = json.dumps(jbojbodict, indent=2, ensure_ascii=False)

print("generated json data.")

for _json, filename in [(jboponjson,"json/jbo-jpn.json"), (jboglijson, "json/jbo-eng.json"), (jbojbojson, "json/jbo-jbo.json")]:
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(_json)

print("written json.")

print("end.")
