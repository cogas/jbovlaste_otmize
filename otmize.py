# -*- coding: utf-8 -*-
from collections import OrderedDict as Odict
import json
from vlaxamgau import goodnotes, sortcontents, integrate_gloss, delete_emptynotes, delete_dollar

def content(title, text):
    return {"title": title, "text": text}

def make_content (valsi, opt, title):
    if not isinstance(valsi[opt], list):
        optlist = [valsi[opt]]
    else:
        optlist = valsi[opt]
    options = []
    if opt == "rafsi":
        options = optlist
        return content(title, "   ".join(options))
    else:
        for _od in optlist:
            word = _od["@word"]
            if "@sense" in _od.keys():
                word += "; {}".format(_od["@sense"])
            if opt == "keyword":
                word = "[{}]: {}".format(_od["@place"], word)
            options.append(word)
    return content(title, ", ".join(options))

def make_contents(valsi):
    contents = []
    if "notes" in valsi.keys():
        contents.append(content("notes", valsi["notes"]))
    for option in [("glossword", "gloss"), ("keyword", "keyword"), ("rafsi", "rafsi")]:
        if option[0] in valsi.keys():
            contents.append(make_content(valsi, *option))
    contents.append(content("username", valsi["user"]["username"]))
    return contents

def make_otmword(valsi):
    entry = {"id": int(valsi["definitionid"]), "form": valsi["@word"]}
    translation = {"forms" : [valsi["definition"]],
                    "title": valsi["@type"] + (": " + valsi["selmaho"] if "selmaho" in valsi.keys() else "")}
    translations = [translation]
    tags = []
    if "@unofficial" in valsi.keys():
        tags.append("unofficial")
    contents = make_contents(valsi)
    variations = []
    relations = []
    return Odict([("entry", entry), ("translations", translations), ("tags", tags),
                    ("contents", contents), ("variations", variations), ("relations", relations)])

def load_jbodict(lang):
    if lang not in ["jpn", "eng", "jbo"]:
        raise ValueError("the input lang({}) doesn't exist.".format(lang))
    filename = 'json/jbo-{}.json'.format(lang)
    try:
        with open(filename, encoding='utf-8') as f:
            jbodict = json.loads(f.read())
        print("loaded {}".format(filename))
    except:
        print("can't find '{}'. get from xmltojson..".format(filename))
        if lang == "jpn":
            from jbovlaste_xmltojson import jbojpndict
            jbodict = jbojpndict
        elif lang == "eng":
            from jbovlaste_xmltojson import jboengdict
            jbodict = jboengdict
        elif lang == "jbo":
            from jbovlaste_xmltojson import jboengdict
            jbodict = jbojbodict
    return jbodict

def make_otmjson(jbodict, filename, lang):
    _vlaste = []
    for valsi in jbodict:
        _vla = make_otmword(valsi)
        if lang == "jpn":
            _vla = delete_dollar(delete_emptynotes(sortcontents(integrate_gloss(goodnotes(_vla)))))
        _vlaste.append(_vla)

    _langdata = {"from":"jbo", "to": lang}
    _j = Odict([("words", _vlaste), ("zpdic", {"alphabetOrder":"!zyxwvutsrqponmlkjihgfedcba"}),
                ("lang", _langdata)])

    otmjson = json.dumps(_j, indent=2, ensure_ascii=False)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(otmjson)
        print("written to {}.".format(filename))


if __name__ == '__main__':
    import sys
    args = sys.argv
    filename_temp = 'otm-json/jbo-{}_otm.json'
    arg_list = {'ro':'-ro', 'ponjo':'-ponjo', 'glico':'-glico', 'lojbo':'-lojbo'}
    if len(args) == 1 :
        raise RuntimeError("No command line variables. try: -ponjo/glico/lojbo/ro")
    elif args[1] not in arg_list.values():
        raise RuntimeError("Invalid command line variables. try: -ponjo/glico/lojbo/ro")
    elif args[1] == arg_list['ro']:
        for lang in ['jpn', 'eng', 'jbo']:
            make_otmjson(load_jbodict(lang), filename_temp.format(lang), lang)
        quit()
    elif args[1] == arg_list['ponjo']:
        lang = 'jpn'
    elif args[1] == arg_list['glico']:
        lang = 'eng'
    elif args[1] == arg_list['lojbo']:
        lang = 'jbo'
    make_otmjson(load_jbodict(lang), filename_temp.format(lang), lang)
