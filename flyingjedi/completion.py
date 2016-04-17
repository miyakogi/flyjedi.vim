#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import json
import asyncio

from jedi.api import Script


class Complete(object):
    _cache = {}

    def __init__(self, msg, transport):
        self.handle = msg[0]
        info = msg[1]
        self.info = info
        self.col = info['col']
        self.line = info['line']
        self.text = info['text']
        self.path = info['path']
        self.detail = bool(info['detail'])
        self.fuzzy = bool(info['fuzzy'])
        self.icase = bool(info['icase'])
        root = info.get('root')
        if root and root not in sys.path:
            sys.path.append(root)

        self.cur_line = self.text[self.line - 1][:self.col-1]

        match = re.search(r'\w+$', self.cur_line)
        self.word = match.group(0) if match else ''
        self.start_col = self.col - 1 - len(self.word)
        self.line_text = self.cur_line[:self.start_col]

    def _get_completions(self):
        if not (self.path == self._cache.get('path') and
                self.line == self._cache.get('line') and
                len(self.text) == len(self._cache.get('text')) and
                self.line_text == self._cache.get('line_text')):
            s = Script('\n'.join(self.text), line=self.line,
                       column=self.start_col)
            self._cache.update(path=self.path, line=self.line, text=self.text,
                               line_text=self.line_text,
                               completions=tuple(s.completions()))
        return self._cache.get('completions')

    @asyncio.coroutine
    def complete(self):
        if self.word and self.fuzzy:
            result = yield from self.fuzzy_match()
        else:
            result = yield from self.normal_match()
        return result

    @asyncio.coroutine
    def get_result(self):
        result = yield from self.complete()
        resp = [self.start_col+1]
        if result:
            resp.append(result)
            resp.append(self.path)
            return resp
        else:
            return resp

    def _to_complete_item(self, c) -> dict:
        d = dict(
            word=c.name,
            abbr=c.name,
            icase=1,
        )
        if self.detail:
            # To obtain these information, sometimes jedi takes TOO LONG TIME.
            d['menu'] = c.description  # for item selection menu
            d['info'] = c.docstring()  # for preview window
        return d

    @asyncio.coroutine
    def fuzzy_match(self):
        completions = self._get_completions()
        result = []
        exact_re = re.compile(r'^' + self.word)
        icase_re = re.compile(r'^' + self.word, re.I)
        fuzzy_re = re.compile(r'^' + r'.*'.join(self.word), re.I)
        exact = []
        icase = []
        fuzzy = []
        for c in completions:
            name = c.name
            if exact_re.match(name):
                exact.append(self._to_complete_item(c))
            elif self.icase and icase_re.match(name):
                icase.append(self._to_complete_item(c))
            elif self.fuzzy and fuzzy_re.match(name):
                fuzzy.append(self._to_complete_item(c))
        yield from asyncio.sleep(0)
        result.extend(exact)
        result.extend(icase)
        result.extend(fuzzy)
        return result

    @asyncio.coroutine
    def normal_match(self):
        completions = self._get_completions()
        result = [self._to_complete_item(c) for c in completions]
        yield from asyncio.sleep(0)
        return result


@asyncio.coroutine
def complete(msg, transport):
    c = Complete(msg, transport)
    handle = msg[0]
    response = yield from c.get_result()
    if not transport._closing:
        transport.write(json.dumps([handle, response]).encode('utf-8'))
