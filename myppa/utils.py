#!/usr/bin/env python3

import os

def ensure_cwd():
    cwd = os.getcwd()
    if not os.path.exists(os.path.join(cwd, "packages")):
        raise RuntimeError("Directory \"packages\" is missing. Please cd to myppa root")
    if not os.path.exists(os.path.join(cwd, "cache")):
        raise RuntimeError("Directory \"cache\" is missing. Please cd to myppa root")
    if not os.path.exists(os.path.join(cwd, "myppa")):
        raise RuntimeError("Script \"myppa\" is missing. Please cd to myppa root")
    return cwd

def normalize_codename(name):
    return {
        "804": "hardy",
        "1004": "lucid",
        "1104": "natty",
        "1110": "oneiric",
        "1204": "precise",
        "1210": "quantal",
        "1304": "raring",
        "1310": "saucy",
        "1404": "trusty",
        "1410": "utopic",
        "1504": "vivid",
        "1510": "wily",
        "1604": "xenial",
        "1610": "yakkety",
        "1704": "zesty",
    }.get(name.replace(".", ""), name)

def default_codename(dist):
    return {
        "ubuntu": "xenial",
    }.get(dist)

def get_data_dir():
    root = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(root, "data")

def get_data(*paths):
    return os.path.join(get_data_dir(), *paths)
