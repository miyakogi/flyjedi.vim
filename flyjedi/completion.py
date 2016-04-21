#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import json
import asyncio
from pathlib import Path

from jedi.api import Script

import_re = re.compile(r'^\s*from\s+.+\s+import\s+')
word_re = re.compile(r'\w+$')
str_word_re = re.compile(r'[.\w]+$')
quote_re = re.compile(r'(\'|").*?\1')
triplequote_re = re.compile(r'(\'\'\'|""").*?\1', re.S)
path_re = re.compile(r'[^\s\'"]+$')


class StringComplete(object):
    def __init__(self, msg):
        info = msg[1]
        self.msg = msg
        self.info = info
        self.col = info.get('col')
        self.line = info.get('line')
        self.text = info.get('text')
        self.path = Path(info.get('path'))
        self.dir = self.path.parent
        self.root = Path(info.get('root'))

    def _to_complete_item(self, path:Path, base:Path=None):
        if not path.exists():
            return {}
        path = path.resolve()
        dir = path.parent
        d = dict(
            word=path.name,
            abbr=path.name,
            icase=1,
        )
        if base:
            path_menu = os.path.relpath(str(dir), str(base))
            if not (path_menu == '.' or path_menu.startswith('..')):
                path_menu = '.' + os.path.sep + path_menu
        elif len(dir.parts) < 4:
            path_menu = dir
        else:
            path_menu = '...' + os.path.sep.join(dir.parts[-3:])
        if path.is_dir():
            d['abbr'] += os.path.sep
            d['info'] = '[Directory] {}'.format(path)
            d['menu'] = 'dir  [F] {}'.format(path_menu)
        if path.is_file():
            d['info'] = '[File] in {}'.format(path)
            d['menu'] = 'file [F] {}'.format(path_menu)
        return d

    def _to_complete_items(self, dir:Path, base:Path=None):
        word = self.word.lower()
        if word:
            res = [self._to_complete_item(item, base)
                   for item in dir.iterdir()
                   if item.name.lower().startswith(word)]
        else:
            res = [self._to_complete_item(item, base)
                   for item in dir.iterdir()]
        res.sort(key=lambda i: i['word'])
        return res

    def _path_complete(self):
        m = path_re.search(self.cur_line[:self.start_col])
        if not m or '://' in m.group(0):
            # would be url
            return {'success': False, 'mode': 'url', 'items': []}
        path = Path(m.group(0))
        res = []
        if path.is_absolute() and path.is_dir():
            res.extend(self._to_complete_items(path))
        else:
            if (self.dir / path).is_dir():
                res.extend(
                    self._to_complete_items(self.dir/path, self.dir))
            if (self.root / path).is_dir():
                res.extend(self._to_complete_items(self.root/path, self.dir))
        if res:
            return {'success': True, 'mode': 'path', 'items': res}
        else:
            return {'success': False, 'mode': 'path', 'items': res}

    def _complete(self):
        self.cur_line = self.text[:self.col-1]
        m = str_word_re.search(self.cur_line)
        self.word = m.group(0) if m else ''
        self.start_col = self.col - 1 - len(self.word)
        if self.cur_line[self.start_col-1] in ('~', '/', '\\'):
            return self._path_complete()
        else:
            return {'success': False, 'mode': 'string', 'items': []}

    @asyncio.coroutine
    def get_completion_results(self):
        resp = self._complete()
        resp['path'] = str(self.path)
        resp['start_col'] = self.start_col + 1
        return resp


class PythonComplete(object):
    _cache = {}

    def __init__(self, msg):
        info = msg[1]
        self.info = info
        self.col = info.get('col')
        self.line = info.get('line')
        self.text = info.get('text')
        self.path = info.get('path')
        root = info.get('root')
        if root and root not in sys.path:
            sys.path.append(root)

    def clear_cache(self):
        self._cache.clear()

    def _is_cached(self):
        import_match = import_re.match(self.line_text)
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
        if import_match:
            start_col = len(import_match.group(0))
        else:
            start_col = self.start_col
        s = self._get_script(line=self.line, col=start_col)
        completions = tuple(s.completions())
        self._cache.update(path=self.path, line=self.line, text=self.text,
                           line_text=self.line_text,
                           completions=completions)
        return completions

    @asyncio.coroutine
    def complete(self):
        self.detail = bool(self.info.get('detail'))
        self.fuzzy = bool(self.info.get('fuzzy'))
        self.icase = bool(self.info.get('icase'))
        self.cur_line = self.text[self.line - 1][:self.col-1]

        match = word_re.search(self.cur_line)
        self.word = match.group(0) if match else ''
        self.start_col = self.col - 1 - len(self.word)
        self.line_text = self.cur_line[:self.start_col]

        cached = self._is_cached()
        completions = (self._cache.get('completions')
                       if cached else self._get_completions())
        if self.word and self.fuzzy:
            result = yield from self.fuzzy_complete(completions)
        else:
            result = yield from self.normal_complete(completions)
        result['start_col'] = self.start_col + 1
        return result

    @asyncio.coroutine
    def get_completion_results(self):
        resp = yield from self.complete()
        resp['path'] = self.path
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
    def fuzzy_complete(self, completions):
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
        return {'success': True, 'items': result, 'mode': 'jedi'}

    @asyncio.coroutine
    def normal_complete(self, completions):
        result = [self._to_complete_item(c) for c in completions]
        yield from asyncio.sleep(0)
        return {'success': True, 'items': result, 'mode': 'jedi'}


@asyncio.coroutine
def complete(msg, transport):
    mode = msg[1].get('mode')
    if mode == 'python':
        completer = PythonComplete(msg)
    elif mode == 'string':
        completer = StringComplete(msg)
    else:
        raise ValueError('Unknown mode: {}'.format(mode))
    handle = msg[0]
    response = yield from completer.get_completion_results()
    if not transport._closing:
        transport.write(json.dumps([handle, response]).encode('utf-8'))
