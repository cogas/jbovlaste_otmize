# coding=utf-8
from vlaste_builder import DictionaryBuilder, JbovlasteWordBuilder
from vlaste_manager import JbovlasteManager
from file_dealer import JbovlasteOTMizedJsonDealer
from pprint import pprint
from random import choice
from collections import defaultdict
import re, json

dealer = JbovlasteOTMizedJsonDealer("en")
dictionary = DictionaryBuilder.load(dealer.json, builder=JbovlasteWordBuilder)
manager = JbovlasteManager(dictionary)

for _ in range(20):
    gismu = choice(list(manager.filter_by_morphology("gismu"))).entry.form
    levens = [word.entry.form for word
              in manager.filter_by_levenshtein(gismu, 1)]
    print("{}: {}".format(gismu, levens))

print(list(manager.filter_by_spell(".onji"))[0].keywords())

def make_leven_dict():
    leven_dict = defaultdict(list)
    for gismu in gismu_liste:
        gismu = gismu.entry.form
        levens = [word.entry.form for word
                  in manager.filter_by_levenshtein(gismu, 1)]
        leven_dict[len(levens)].append((gismu, levens))
