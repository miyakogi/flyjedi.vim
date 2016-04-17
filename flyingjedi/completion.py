#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import json
import asyncio

from jedi.api import Script

import_re = re.compile(r'^\s*from\s+.+\s+import\s+')


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
        root = info.get('root')
        if root and root not in sys.path:
            sys.path.append(root)

    def clear_cache(self):
        self._cache.clear()

    def _is_cached(self, import_match):
        if import_match:
            line_text = import_match.group(0)
            prev_import = import_re.match(self._cache.get('line_text'))
            if prev_import is None:
                return False
            else:
                prev_line = prev_import.group(0)
        else:
            line_text = self.line_text
            prev_line = self._cache.get('line_text')
        return bool(self.path == self._cache.get('path') and
                    self.line == self._cache.get('line') and
                    len(self.text) == len(self._cache.get('text')) and
                    line_text == prev_line)

    def _get_script(self, line=None, col=None):
        if line is None:
            line = self.line
        s = Script('\n'.join(self.text), line=line, column=col)
        return s

    def _get_completions(self):
        import_match = import_re.match(self.line_text)
        if not self._is_cached(import_match):
            if import_match:
                start_col = len(import_match.group(0))
            else:
                start_col = self.start_col
            s = self._get_script(line=self.line, col=start_col)
            self._cache.update(path=self.path, line=self.line, text=self.text,
                               line_text=self.line_text,
                               completions=tuple(s.completions()))
        return self._cache.get('completions')

    @asyncio.coroutine
    def complete(self):
        self.detail = bool(self.info.get('detail'))
        self.fuzzy = bool(self.info.get('fuzzy'))
        self.icase = bool(self.info.get('icase'))
        self.cur_line = self.text[self.line - 1][:self.col-1]

        match = re.search(r'\w+$', self.cur_line)
        self.word = match.group(0) if match else ''
        self.start_col = self.col - 1 - len(self.word)
        self.line_text = self.cur_line[:self.start_col]

        if self.word and self.fuzzy:
            result = yield from self.fuzzy_match()
        else:
            result = yield from self.normal_match()
        return result

    @asyncio.coroutine
    def get_completion_results(self):
        result = yield from self.complete()
        resp = [self.start_col+1]
        if result:
            resp.append(result)
        else:
            resp.append([])
        resp.append(self.path)
        return resp

    def get_goto_definitons(self):
        s = self._get_script(col=self.col)
        for d in s.goto_definitions():
            # print(vars(d))
            # print(d.name)
            # print(d.module_path)
            pass

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
    response = yield from c.get_completion_results()
    if not transport._closing:
        transport.write(json.dumps([handle, response]).encode('utf-8'))


def goto_assignments(msg, transport):
    c = Complete(msg, transport)
    handle = msg[0]
    response = c.get_goto_definitons()
    if not transport._closing:
        transport.write(json.dumps([handle, response]).encode('utf-8'))
