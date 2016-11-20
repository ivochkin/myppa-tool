#!/usr/bin/env python3

import subprocess
import json
import re
from copy import copy
from myppa.key import Key

class Package(object):
    def __init__(self, description):
        self._description = description

    def __getattr__(self, attr):
        return self._description.get(attr)

    def is_version_computed(self):
        return getattr(self, "version-script") is not None

    def validate(self):
        pass

    def description(self):
        return self._description

    def resolve(self, distribution, codename, architecture):
        resolved = {}
        tagged_keys = []
        for k, v in self.description().items():
            k = Key.parse(k)
            if k.tag() is None:
                resolved[k.name()] = v
            else:
                tagged_keys.append((k, v))
        # sort by tag
        tagged_keys = sorted(tagged_keys, key=lambda x: x[0].tag())
        for k, v in tagged_keys:
            if k.name() in resolved:
                if k.on_merge_add():
                    resolved[k.name()].update(v)
                elif k.on_merge_remove():
                    del resolved[k.name()]
            else:
                resolved[k.name()] = v
        return resolved

    def persist(self, conn):
        c = conn.cursor()
        c.execute("INSERT INTO package VALUES (?,?,?,?)",
            (getattr(self, "name"),
             self.is_version_computed(),
             getattr(self, "version"),
             json.dumps(self.description())))

    @classmethod
    def load(cls, conn, name, version):
        c = conn.cursor()
        description = None
        query = "SELECT description FROM package where name = ?"
        qargs = (name,)
        if version is not None:
            query += " AND version = ?"
            qargs = (name, version)
        row_found = False
        for row in c.execute(query, qargs):
            if row_found:
                raise RuntimeError(("Multiple packages with name '{}' are found. "
                                    "Please specify exact version of the package."
                                    ).format(name))
            row_found = True
            description = row[0]
        if not row_found:
            raise RuntimeError("No package with name '{}' and version '{}' is found."
                                .format(name, version or "any"))
            return 0
        return cls(json.loads(description))
