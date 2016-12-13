# coding=utf-8
from vlaste_builder import DictionaryBuilder, WordComponents, Entry
from leven import levenshtein
import re

class DictionaryManager:
    def __init__(self, builder):
        if not isinstance(builder, DictionaryBuilder):
            raise TypeError("builder must be DictionaryBuilder.")
        self.builder = builder

    def get_zpdic(self):
        return self.builder.metadata["zpdic"]

    def get_meta(self):
        return self.builder.metadata["meta"]

    @property
    def words(self):
        return self.builder.words

    def filter_by_spell(self, spell, regex=False):
        if regex:
            pattern = re.compile(spell)
            for word in self.words:
                    match = pattern.search(word.entry.form)
                    if match is not None:
                        yield word
        else:
            for word in self.words:
                if spell in word.entry.form:
                    yield word

    def filter_by_levenshtein(self, word_spell, distance):
        words = self.words
        for word in words:
            if levenshtein(word_spell, word.entry.form) <= distance:
                yield word

    def filter_by_morphology(self, morpho):
        for word in self.words:
            if morpho in word.translations[0].title:
                yield word


class JbovlasteManager(DictionaryManager):
    ...
