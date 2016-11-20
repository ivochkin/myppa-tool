#!/usr/bin/env python3

import re

class Key(object):
    _regexp = re.compile(r'([+-]?)(?:([^:]+):)?([^:]+)(?::(.*))?')

    def __init__(self, onmerge, tag, name, envspec):
        self._on_merge_add = True if onmerge == "+" else False
        self._tag = tag
        self._name = name
        self._envspec = envspec

    @classmethod
    def parse(cls, val):
        m = cls._regexp.match(val)
        return cls(m.group(1) or "+", m.group(2) or None, m.group(3), m.group(4) or None)

    def on_merge_add(self):
        return self._on_merge_add

    def on_merge_remove(self):
        return not self._on_merge_add

    def tag(self):
        return self._tag

    def name(self):
        return self._name

    def envspec(self):
        return self._envspec
