# coding=utf-8
from vlaste_builder import DictionaryBuilder, WordComponents, Entry

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

    def filter(self, query, *, attr='contents',
               target='glossword', column='text', partial=True):
        result = []
        for word in self.builder.words:
            components = getattr(word, attr)
            if isinstance(components, WordComponents):
                compared_text = getattr(components.find(target)[1], column)
                if partial and query in compared_text:
                    result.append(word)
                elif not partial and query == compared_text:
                    result.append(word)
            elif isinstance(components, Entry):
                if partial and query in getattr(components, target):
                    result.append(word)
                elif not partial and query == getattr(components, target):
                    result.append(word)
            else:
                raise TypeError
        return result

class WordManager:

    @staticmethod
    def entry_eq(word, form):
        return word.entry.form == form

    @staticmethod
    def has_such_content(word, title):
        return title in word.contents.keys()

    @staticmethod
    def contains_such_content(word, query, title):
        if title in word.contents.keys():
            return query in word.contents.find(title)[1].text
        else:
            return False
