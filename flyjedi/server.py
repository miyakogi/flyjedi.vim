#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import socket
import asyncio

from option import options
from completion import complete, Complete, goto_assignments

_tasks = []

try:
    ensure_future = asyncio.ensure_future
except AttributeError:
    # old python (<3.4.4) support
    # async becomes keyword in python3.7, so cannot use directly
    exec('ensure_future = asyncio.async')


class IOServer(asyncio.Protocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raw_data = ''
        self.task = None

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        while _tasks:
            _t = _tasks.pop()
            _t.cancel()

        msg = json.loads(data.decode('utf-8'))
        mode = msg[1].get('mode')
        if mode == 'clear_cache':
            Complete.clear_cache()
        elif mode == 'completion':
            self.task = ensure_future(complete(msg, self.transport))
            _tasks.append(self.task)
        elif mode == 'goto_assignments':
            goto_assignments(msg, self.transport)

    def eof_received(self):
        if self.task in _tasks and not self.task.done():
            _tasks.remove(self.task)
            self.task.cancel()
        return None


@asyncio.coroutine
def run():
    loop = asyncio.get_event_loop()
    server = yield from loop.create_server(
        IOServer, host='localhost', port=options.port)
    return server


def start_server():
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(run())
    for sock in server.sockets:
        if sock.family == socket.AF_INET:
            port = sock.getsockname()[1]
            print('{}\n'.format(port))
            sys.stdout.flush()
            break
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.stop()


def main():
    start_server()


if __name__ == '__main__':
    main()
