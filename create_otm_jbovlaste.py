# -*- coding: utf-8 -*-

import sys, json, datetime, concurrent.futures, re, argparse
from time import time
from multiprocessing import cpu_count
from collections import OrderedDict, defaultdict

from file_dealer import JbovlasteXmlDealer, JbovlasteZipDealer, RawdictDealer 
from vlaste_builder import (DictionaryBuilder, JbovlasteWordBuilder, Metadata,
                            WordBuilderForJapanese, ZpDICInfo)

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

def dictionary_customize(dictionary, nodollar, addrelations):

    if dictionary.metadata.langdata["to"] == "ja":
        dictionary.words = [WordBuilderForJapanese.load(word.build())
                            for word in dictionary.words]

    for word in dictionary.words:
        if dictionary.metadata.langdata["to"] == "ja":
            word.whole_execute()
        if nodollar:
            word.delete_dollar()

    if addrelations:
        dictionary.words = relationized_words(dictionary)

    return dictionary

def relationized_words(dictionary):
    print('add relations...')
    start = time()
    entry_list = [word.entry for word in dictionary.words]
    letters = ".abcdefgijklmnoprstuvxyz"
    letters += letters[1:].upper()
    entries_for_dict_creation = entry_list
    entry_dict = defaultdict(list)
    for letter in letters:
        for i, entry in enumerate(entries_for_dict_creation):
            if entry.form[0] == letter:
                entry_dict[letter].append(entry)
    new_word_list = []
    max_task = len(dictionary.words)
    if max_task >= 6000:
        message = "\r{}/{} * {} words done, using {} processes."
        cpu = cpu_count()
        futures = set()
        list_size = 2000 # max_task // (cpu*1)
        done_task = 0
        split_words = [dictionary.words[x:x+list_size] for x in range(0, max_task, list_size)]
        task_block = len(split_words)
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu) as executor:
            sys.stdout.write(message.format(0, task_block, max_task, cpu))
            sys.stdout.flush()
            for words in split_words:
                future = executor.submit(worker_for_plural, words, entry_dict)
                futures.add(future)
            for future in concurrent.futures.as_completed(futures):
                new_word_list.extend(future.result())
                done_task += 1
                sys.stdout.write(message.format(done_task, task_block, max_task, cpu))
                sys.stdout.flush()
        new_word_list = sorted(new_word_list, key=(lambda word: word.entry.form))
    else:
        for word in dictionary.words:
            future = worker(word, entry_dict)
            new_word_list.append(future)
            done_task = len(new_word_list)
            sys.stdout.write("\r{}/{} words done, using 1 process.".format(done_task, max_task))
            sys.stdout.flush()
    end = time()
    print(" ({:.1f} sec.)".format(end-start))
    return new_word_list

def worker(word, entry_dict):
    '''r"{[a-zA-Z']}" に該当する単語のうち、エントリーのあるものだけを relations に加える。
    "ja" の場合「関連語」も対象にする。'''
    regex = r"\{[.a-zA-Z']+\}"
    potential_list = []
    if "notes" in word.contents.keys():
        potential_list.extend(re.findall(regex, word.contents.find("notes")[1].text))
    if "関連語" in word.contents.keys():
        potential_list.extend(re.findall(regex, word.contents.find("関連語")[1].text))
    potential_list = [re.sub(r'^[^.a-zA-Z]+', '', re.sub(r'[^.a-zA-Z]+$', '', w)) for w in potential_list]
    for potential_word in potential_list:
        for entry in entry_dict[potential_word[0]]:
            if entry.form == potential_word:
                word.add_relation("", *entry)
                break
    return word

def worker_for_plural(words, entry_dict):
    result = []
    for word in words:
        result.append(worker(word, entry_dict))
    return result

# -------------------------

def handle_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument("language", choices=LANG_LIST, nargs='+')
    parser.add_argument("--zip", action='store_true')
    parser.add_argument("--nodollar", action='store_true')
    parser.add_argument("--addrelations", action='store_true')
    args = parser.parse_args()
    return args.language, args.nodollar, args.addrelations, args.zip

def create_dictionary(lang, nodollar, addrelations):
    rawdict_dealer = RawdictDealer(lang)
    rawdict = rawdict_dealer.load()
    zpdic = ZpDICInfo(lang)
    zpdic.set_by_lang()
    dictionary = make_otmized_dictionary(rawdict, lang, zpdic_data=zpdic.build())
    return dictionary_customize(dictionary, nodollar, addrelations)

if __name__ == '__main__':
    langs, nodollar, addrelations, zippy = handle_commandline()
    filename_temp = 'otm-json/jbo-{}_otm.json'
    for lang in langs:
        filename = filename_temp.format(lang)
        dictionary = create_dictionary(lang, nodollar, addrelations)
        dictionary.save(filename)
        print()
    if zippy:
        zipdealer = JbovlasteZipDealer(langs)
        zipdealer.zippy()
    print("Success!")
