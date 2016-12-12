# coding=utf-8
from vlaste_builder import DictionaryBuilder
from file_dealer import OTMizedJsonDealer
from pprint import pprint

dealer = OTMizedJsonDealer("ja")
dictionary = DictionaryBuilder.load(dealer.json)
