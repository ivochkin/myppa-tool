#!/usr/bin/env python3

import subprocess
import json

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
