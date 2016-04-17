#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=0)
options, unknown_args = parser.parse_known_args()
if unknown_args:
    logging.warn('Get unknown arguments: {}'.format(' '.join(unknown_args)))
