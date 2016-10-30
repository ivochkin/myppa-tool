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
