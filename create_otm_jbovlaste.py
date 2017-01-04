# -*- coding: utf-8 -*-

import argparse
import concurrent.futures
import datetime
import json
import re
import sys
from time import time
from multiprocessing import cpu_count
from collections import OrderedDict, defaultdict

from file_dealer import JbovlasteXmlDealer, JbovlasteZipDealer, RawdictDealer
from vlaste_builder import (DictionaryBuilder, JbovlasteWordBuilder, Metadata,
                            WordBuilderForJapanese, ZpDICInfo)
import relationize

LANG_LIST = ["en", "ja", "jbo", "en-simple"]


def make_content(valsi, title_name):
    if title_name in ('keyword', 'glossword'):
        text_delimiter = "\n"
        component_type = dict
    elif title_name == 'rafsi':
        text_delimiter = "   "
        component_type = str
    else:
        text_delimiter = ", "
        component_type = dict

    if title_name in valsi.keys():
        component_list = []
        if isinstance(valsi[title_name], component_type):
            component_list.append(valsi[title_name])
        else:
            component_list.extend(valsi[title_name])
        text_list = []
        if title_name == 'rafsi':
            text_list = component_list
        else:
            for component in component_list:
                word = component["@word"]
                if "@sense" in component.keys():
                    word += "; {}".format(component["@sense"])
                if title_name == "keyword":
                    word = "[{}]: {}".format(component["@place"], word)
                if title_name == "glossword":
                    word = "- {}".format(word)
                text_list.append(word)
        return title_name, text_delimiter.join(text_list)
    else:
        raise ValueError


def make_otmized_word(valsi):
    builder = JbovlasteWordBuilder()
    builder.set_entry(int(valsi["definitionid"]), valsi["@word"])

    if "selmaho" in valsi.keys():
        selmaho = ": "+valsi["selmaho"]
    else:
        selmaho = ""
    builder.add_translation(valsi["@type"]+selmaho, [valsi["definition"]])

    if "@unofficial" in valsi.keys():
        builder.add_tag("unofficial")

    if "notes" in valsi.keys():
        builder.add_content("notes", valsi["notes"])

    for title in ("keyword", "glossword", "rafsi"):
        if title in valsi.keys():
            builder.add_content(*make_content(valsi, title))

    builder.add_content("username", valsi["user"]["username"])
    return builder


def make_otmized_dictionary(rawdict, lang, zpdic_data={}):
    dictionary_builder = DictionaryBuilder()
    for valsi in rawdict:
        word = make_otmized_word(valsi)
        dictionary_builder.append(word)

    metadata = Metadata()
    metadata.set_langdata("jbo", lang)
    metadata.add_generated_date(datetime.date.today())
    metadata.set_zpdic_data(zpdic_data)
    dictionary_builder.metadata = metadata

    return dictionary_builder


def dictionary_customize(dictionary, args):

    if dictionary.metadata.langdata["to"] == "ja":
        dictionary.words = [WordBuilderForJapanese.load(word.build())
                            for word in dictionary.words]

    for word in dictionary.words:
        if dictionary.metadata.langdata["to"] == "ja":
            word.whole_execute()
        if args.nodollar:
            word.delete_dollar()
        # if you wanna keep glossword in contents, comment-out the block below.
        if args.keepgloss and word.glosswords():
            word.add_translation("gloss", word.glosswords())
            del word.contents[word.contents.find('glossword')[0]]

    if args.addrelations:
        dictionary.words = relationized_words(dictionary)

    return dictionary


def relationized_words(dictionary, strategy=None):
    print('relationizing...')
    if stragety is None:
        strategy = relationize.default_relationize
    start = time()
    new_word_list = strategy(dictionary)
    end = time()
    print(" ({:.1f} sec.)".format(end-start))
    return new_word_list


def handle_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument("language", choices=LANG_LIST, nargs='+')
    parser.add_argument("--zip", action='store_true')
    parser.add_argument("--nodollar", action='store_true')
    parser.add_argument("--addrelations", action='store_true')
    parser.add_argument("--output", "-o", nargs='?', default='otm-json/')
    parser.add_argument("--keepgloss", action='store_false')
    parser.add_argument("--test", action='store_true')
    args = parser.parse_args()
    return args


def create_dictionary(lang, args):
    rawdict_dealer = RawdictDealer(lang)
    rawdict = rawdict_dealer.load()
    zpdic = ZpDICInfo(lang)
    zpdic.set_by_lang()
    dictionary = make_otmized_dictionary(rawdict, lang,
                                         zpdic_data=zpdic.build())
    return dictionary_customize(dictionary, args)

if __name__ == '__main__':
    args = handle_commandline()
    langs = args.language
    output = args.output
    filename_temp = '{}jbo-{}_otm.json'.format(output, '{}')
    for lang in langs:
        filename = filename_temp.format(lang)
        dictionary = create_dictionary(lang, args)
    if args.test:
        print('This is test. Dictionary data is not saved.')
    else:
        dictionary.save(filename)
    print()
    if args.zip:
        zipdealer = JbovlasteZipDealer(langs)
        zipdealer.zippy()
    print("Success!")
