# coding=utf-8
from vlaste_builder import DictionaryBuilder
from vlaste_manager import JbovlasteManager
from file_dealer import OTMizedJsonDealer
from pprint import pprint
from random import choice
from collections import defaultdict
import re
import json

dealer = OTMizedJsonDealer("en")
dictionary = DictionaryBuilder.load(dealer.json)
manager = JbovlasteManager(dictionary)
gismu_manager = JbovlasteManager(dictionary)
gismu_manager.builder.words = list(manager.filter_by_morphology("gismu"))

for _ in range(10):
    gismu = choice(gismu_manager.words).entry.form
    levens = [word.entry.form for word
              in manager.filter_by_levenshtein(gismu, 1, gismu_only=True)]
    print("{}: {}".format(gismu, levens))

def aaa():
    leven_dict = defaultdict(list)
    for gismu in gismu_liste:
        gismu = gismu.entry.form
        levens = [word.entry.form for word
                  in manager.filter_by_levenshtein(gismu, 1, gismu_only=True)]
        leven_dict[len(levens)].append((gismu, levens))
