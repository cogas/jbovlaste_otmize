# coding=utf-8

import multiprocessing


def default_prepare(dictionary):
    entry_list = [word.entry for word in dictionary.words]
    letters = ".abcdefgijklmnoprstuvxyz"
    letters += letters[1:].upper()
    entries_for_dict_creation = entry_list
    entry_dict = defaultdict(set)
    for letter in letters:
        for i, entry in enumerate(entries_for_dict_creation):
            if entry.form[0] == letter:
                entry_dict[letter].add(entry)
    for key, value in entry_dict.items():
        entry_dict[key] = frozenset(value)

    return entry_dict


def progress_print(now, max_size, cpu):
    message = "\r{}/{} words done, using {} processes."
    sys.stdout.write(message.format(now, max_size, cpu))
    sys.stdout.flush()


def default_relationize(dictionary):
    entry_dict = default_prepare(dictionary)
    max_task = len(dictionary.words)
    results = set()

    if max_task < 6000:
        return single_relationize(entry_dict, dictionary)

    cpu = cpu_count()
    futures = set()
    list_size = 2000
    split_words = [dictionary.words[x:x+list_size]
                   for x in range(0, max_task, list_size)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu) as executor:
        for words in split_words:
            future = executor.submit(bulk_worker, words, entry_dict)
            futures.add(future)
        for future in concurrent.futures.as_completed(futures):
            for word in future.result():
                results.add(word)
            done_task = len(results)
            progress_print(done_task, max_task, cpu)

    return results = sorted(list(results), key=(lambda word: word.entry.form))

    assert(len(results) == len(dictionary.words))
    return results


def nightly_relationize(dictionary):
    entry_dict = default_prepare(dictionary)
    jobs = multiprocessing.JoinableQueue()
    results = multiprocessing.Queue()
    for word in dictionary.words:
        jobs.put(word)

    max_task = jobs.qsize()
    concurrency = cpu_count()

    for _ in range(concurrency):
        process = multiprocessing.Process(target=worker,
                                          args=(entry_dict, jobs, results))
        process.daemon = True
        process.start()

    while True:
        for word in future.result():
            results.put(word)
        done_task = results.qsize()
        progress_print(done_task, max_task, cpu)

    results.sort(key=(lambda word: word.entry.form))

    assert(len(results) == len(dictionary.words))
    return results


def single_relationize(entry_dict, dictionary):
    results = set()
    progress_print(0, max_task, 1)
    for word in dictionary.words:
        results.add(_worker(word, entry_dict))
        progress_print(len(results), max_task, 1)
    return sorted(list(results), key=(lambda word: word.entry.form))


def worker(entry_dict, jobs, results):
    while True:
        try:
            word = jobs.get()
            try:
                result = _worker(word, entry_dict)
                results.put(result)
            except Exception as err:
                raise err
        finally:
            jobs.task_done()


def _worker(word, entry_dict):
    """r"{[a-zA-Z']}" に該当する単語のうち、エントリーのあるものだけを relations に加える。
    "ja" の場合「関連語」も対象にする。"""
    regex = r"\{[.a-zA-Z']+\}"
    potential_list = []
    if "notes" in word.contents.keys():
        potential_list.extend(re.findall(regex,
                                         word.contents.find("notes")[1].text))
    if "関連語" in word.contents.keys():
        potential_list.extend(re.findall(regex,
                                         word.contents.find("関連語")[1].text))
    regex = "|".join([r'^[^.a-zA-Z]+', r'[^.a-zA-Z]+$'])
    potential_list = [re.sub(regex, '', w) for w in potential_list]
    for potential_word in potential_list:
        for entry in entry_dict[potential_word[0]]:
            if entry.form == potential_word:
                word.add_relation("", *entry)
                break
    return word


def bulk_worker(words, entry_dict):
    result = []
    for word in words:
        result.append(_worker(word, entry_dict))
    return result
