#!/usr/bin/env python3

import os
import sys
import sqlite3
import click
from copy import copy
from jinja2 import Template
from myppa.package import Package

def supported_architectures():
    return ['i386', 'amd64']

def supported_distributions():
    supported_ubuntus = [
        "precise", "12.04",
        "trusty", "14.04",
        "xenial", "16.04",
    ]
    return ["ubuntu:" + i for i in supported_ubuntus]

def _normalize_codename(name):
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

def _default_codename(dist):
    return {
        "ubuntu": "xenial",
    }.get(dist)

def parse_package(package):
    nameversion = package.split("@")
    name = nameversion[0]
    version = nameversion[1] if len(nameversion) > 1 else None
    return name, version

def parse_distribution(distribution):
    distcodename = distribution.split(":")
    dist = distcodename[0]
    codename = distcodename[1] if len(distcodename) > 1 else _default_codename(dist)
    codename = _normalize_codename(codename)
    return dist, codename

def ensure_cwd():
    cwd = os.getcwd()
    required_dirs = ["packages", "cache", "specs"]
    required_files = ["myppa"]
    for directory in required_dirs:
        fulldir = os.path.join(cwd, directory)
        if not os.path.exists(fulldir) or not os.path.isdir(fulldir):
            raise RuntimeError("Directory \"{}\" is missing. Please cd to myppa root".format(directory))
    for filename in required_files:
        if not os.path.exists(os.path.join(cwd, filename)):
            raise RuntimeError("File \"{}\" is missing. Please cd to myppa root".format(filename))
    return cwd

def get_data_dir():
    root = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(root, "data")

def get_data(*paths):
    return os.path.join(get_data_dir(), *paths)

def get_cache_dir():
    return os.path.join(ensure_cwd(), "cache")

def ensure_tasks_dir():
    tasks_dir = os.path.join(get_cache_dir(), "tasks")
    if not os.path.exists(tasks_dir):
        os.mkdir(tasks_dir)
    if not os.path.isdir(tasks_dir):
        raise RuntimeError("Cache directory is broken, run ./myppa clean and try again.")
    return tasks_dir

def get_packages_db():
    return os.path.join(ensure_cwd(), "cache", "packages.db")

def get_specs_dir():
    return os.path.join(ensure_cwd(), "specs")

def get_package_description(package):
    name, version = parse_package(package)
    conn = sqlite3.connect(get_packages_db())
    try:
        package = Package.load(conn, name, version)
    except RuntimeError as err:
        click.echo(err)
        sys.exit(1)
    conn.close()
    return package.description()

def get_script(package, distribution, architecture):
    description = get_package_description(package)
    env = copy(description)
    for k, v in description.items():
        env[k.replace("-", "_")] = v
    distribution, codename = parse_distribution(distribution)
    env['distribution'] = distribution
    env['codename'] = codename
    env['architecture'] = architecture
    template = Template(open(get_data("templates", "build_deb.sh"), 'r').read())
    return template.render(env)
