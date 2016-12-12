# coding=utf-8
from vlaste_builder import DictionaryBuilder
from vlaste_manager import DictionaryManager
from file_dealer import OTMizedJsonDealer
from collections import defaultdict
import csv, re
from pprint import pprint

jbo_dealer = OTMizedJsonDealer("jbo")
jbo_dictionary = DictionaryBuilder.load(jbo_dealer.json)
jbo_manager = DictionaryManager(jbo_dictionary)
