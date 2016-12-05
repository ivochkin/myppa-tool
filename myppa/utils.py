#!/usr/bin/env python3

import os
import sys
import shutil
import sqlite3
import click
import uuid
import hashlib
import yaml
import json
import xmltodict
from subprocess import Popen
from copy import copy
from jinja2 import Environment, PackageLoader, Template
from myppa.package import Package
from myppa.filters import *

def supported_architectures():
    return ['amd64', 'i386']

def supported_distributions(with_aliases=True):
    supported_ubuntus = [
        "xenial",
        "trusty",
        "precise",
    ]
    if with_aliases:
        supported_ubuntus += [
            "16.04",
            "14.04",
            "12.04",
        ]
    return ["ubuntu:" + i for i in supported_ubuntus]

def supported_formats():
    return ["yaml", "json", "xml"]

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

def get_package(package):
    name, version = parse_package(package)
    conn = sqlite3.connect(get_packages_db())
    try:
        package = Package.load(conn, name, version)
    except RuntimeError as err:
        click.echo(err)
        sys.exit(1)
    conn.close()
    return package

def get_script(http_proxy, package, distribution, architecture):
    distribution, codename = parse_distribution(distribution)
    description = get_package(package).resolve(distribution, codename, architecture)
    description['http-proxy'] = http_proxy
    description['distribution'] = distribution
    description['codename'] = codename
    description['architecture'] = architecture
    variables = copy(description)
    for k, v in description.items():
        variables[k.replace("-", "_")] = v
    env = Environment(loader=PackageLoader("myppa", os.path.join("data", "templates")))
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.filters["format_deb_depends"] = format_deb_depends
    return env.get_template("build_deb.sh").render(variables)

def format_object(obj, format_type):
    if format_type == "yaml":
        return yaml.dump(obj, default_flow_style=False)
    elif format_type == "json":
        return json.dumps(obj, indent=2)
    elif format_type == "xml":
        obj = {"package": obj}
        return xmltodict.unparse(obj, pretty=True, indent="  ")
    raise RuntimeError("Unknown format '{}'".format(format_type))

def run_builder(http_proxy, package, distribution, architecture):
    dist, codename = parse_distribution(distribution)
    script = get_script(http_proxy, package, distribution, architecture)
    scriptid = hashlib.sha1(script.encode('utf-8')).hexdigest()
    script_fullpath = os.path.join(get_cache_dir(), "{}.sh".format(scriptid))
    open(script_fullpath, 'w').write(script)
    tasks_dir = ensure_tasks_dir()
    taskid = str(uuid.uuid4())
    work_dir = os.path.join(tasks_dir, taskid)
    os.mkdir(work_dir)
    Popen(['sh', script_fullpath], cwd=work_dir).wait()
    outdir = "packages"
    for filename in os.listdir(work_dir):
        if filename.endswith(".deb"):
            shutil.copy(os.path.join(work_dir, filename), os.path.join(outdir, filename))
