# coding=utf-8
from vlaste_builder import DictionaryBuilder
from vlaste_manager import DictionaryManager
from file_dealer import OTMizedJsonDealer
from collections import defaultdict
import csv, re

EXCEPT_WORDS = ("lesrxapsurdie", )
MANUAL_WORDS = {"lelxe": ["lel"]}

def rafsi_collector(dictionaries):
    rafsi_table = defaultdict(set)
    for dictionary in dictionaries:
        for word in dictionary.words:
            key = word.entry.form
            if 'unofficial' in word.tags:
                key = '*' + key
                estimated_rafsis = rafsi_detector(word)
                if estimated_rafsis:
                    rafsi_table[key].update(estimated_rafsis)
            if 'rafsi' in word.contents.keys():
                rafsi_set = word.contents.find('rafsi')[1].text.split()
                rafsi_table[key].update(rafsi_set)
    return rafsi_table

def rafsi_detector(word):
    '''detect potential rafsi from notes in word. DIRTY!!! .oisai
    Firstly, detect a phrase like "Proposed short rafsi" of notes.
    And... detect '-XXX-' forms... yeah... just guess. ge'e
    '''
    if word.entry.form in EXCEPT_WORDS:
        return []
    if word.entry.form in MANUAL_WORDS:
        result = MANUAL_WORDS[word.entry.form]
        print("MANUALLY detect in {}: '{}'".format(word.entry.form, result))
        return result
    if 'notes' in word.contents.keys():
        key_phrase = r'([pP]roposed |[sS]hort |[pP]roposed [sS]hort )rafsi'
        notes_text = word.contents.find('notes')[1].text
        match_ = re.search(key_phrase, notes_text)
        if match_ is None:
            return []
        end = match_.end()
        # --- fenki cfari ---
        consonant = r"[bcdfgjklmnprstvxz]"
        vowel = r"[aeiou]"
        rafsi_forms = (r"{}{}{}".format(consonant, consonant, vowel),
                       r"{}{}{}".format(consonant, vowel, consonant),
                       r"{}{}\'{}".format(consonant, vowel, vowel),
                       r"{}ai".format(consonant),
                       r"{}au".format(consonant),
                       r"{}ei".format(consonant),
                       r"{}oi".format(consonant)
                       )
        rafsi_hiphens = [r"-{}-", r"–{}–"]
        rafsi_patterns = []
        for hiphen in rafsi_hiphens:
            for form in rafsi_forms:
                rafsi_patterns.append(hiphen.format(form))
        rafsi_regex = "|".join(rafsi_patterns)
        # --- fenki fanmo ---
        potential_list = re.findall(rafsi_regex, notes_text[end:end+50])
        result = [re.sub(r"[^a-z']", "", potential)
                  for potential in potential_list]
        print("detect in {}: '{}'".format(word.entry.form, result))
        return result
    else:
        return []

def sort_key(row):
    word = row[0]
    if word[0] == '*':
        return word[1:]
    else:
        return word

def make_rafsi_table(format="csv"):
    if format == "tsv":
        delimiter = '\t'
    elif format == "csv":
        delimiter = ","
    else:
        raise ValueError("not supported.")
    en_dealer = OTMizedJsonDealer("en")
    en_dictionary = DictionaryBuilder.load(en_dealer.json)
    en_manager = DictionaryManager(en_dictionary)
    rafsi_table = [[key, *rafsis]
                   for key, rafsis in rafsi_collector((en_dictionary,)).items()]
    rafsi_table = sorted(rafsi_table, key=sort_key)
    filename = 'rafsi_table/rafsi_table.' + format
    with open(filename, "w", newline='', encoding='utf-8') as file:
        header = ["valsi", "rafsi_1", "rafsi_2", "rafsi_3"]
        writer = csv.writer(file, delimiter=delimiter)
        writer.writerow(header)
        for row in rafsi_table:
            if len(row) < 4:
                row.extend(['']*(4-len(row)))
            writer.writerow(row)
        print("Written: {}.".format(filename))
