#!/usr/bin/env python3

import os
import sys
import shutil
import hashlib
from subprocess import Popen
from copy import copy
import click
import yaml
from jinja2 import Template
from myppa.utils import *

@click.group()
def cli():
    pass

@cli.command()
def clean():
    cwd = ensure_cwd()
    cache_dir = os.path.join(cwd, "cache")
    if not click.confirm("Erase cache/ directory?"):
        return
    for filename in os.listdir(cache_dir):
        if filename == ".placeholder":
            continue
        fullpath = os.path.join(cache_dir, filename)
        if os.path.isdir(fullpath):
            shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)

@cli.command()
def list():
    cwd = ensure_cwd()
    specs_dir = os.path.join(cwd, "specs")
    variants = []
    for package_name in os.listdir(specs_dir):
        package_dir = os.path.join(specs_dir, package_name)
        if not os.path.isdir(package_dir):
            continue
        for distribution_name in os.listdir(package_dir):
            distribution_dir = os.path.join(package_dir, distribution_name)
            if not os.path.isdir(distribution_dir):
                continue
            for codename in os.listdir(distribution_dir):
                spec_dir = os.path.join(distribution_dir, codename)
                if not os.path.isdir(spec_dir):
                    continue
                spec_file = os.path.join(spec_dir, 'spec.yaml')
                if not os.path.exists(spec_file):
                    continue

    print("Name", "Version", "Distribution", "Codename", "Architecture")
    for var in variants:
        print(var)


@cli.command()
@click.argument("name")
@click.argument("distribution")
@click.argument("architecture")
def build(name, distribution, architecture):
    distcodename = distribution.split(":")
    dist = distcodename[0]
    if len(distcodename) > 1:
        codename = distcodename[1]
    else:
        codename = default_codename(dist)
    codename = normalize_codename(codename)
    name, version = name.split("@")
    specpath = os.path.join("specs", name, dist, codename, "spec.yaml")
    with open(specpath, 'r') as stream:
        try:
            for i in yaml.load_all(stream):
                if i["version"] == version and i["name"] == name:
                    h = hashlib.sha1()
                    for component in [name, version, dist, codename, architecture]:
                        h.update(component.encode('utf-8'))
                    conf_name = h.hexdigest()
                    script_name = conf_name + ".sh"
                    with open(os.path.join("cache", script_name), 'w') as out:
                        template = Template(open(get_data("templates", "build_deb.sh"), 'r').read())
                        spec_env= i
                        env = copy(spec_env)
                        for k, v in spec_env.items():
                            env[k.replace("-", "_")] = v
                        env['distribution'] = dist
                        env['codename'] = codename
                        env['architecture'] = architecture
                        out.write(template.render(env))
                    work_dir = os.path.join("cache", conf_name)
                    try:
                        os.mkdir(work_dir)
                    except:
                        pass
                    script_name = os.path.join("..", script_name)
                    p = Popen(['sh', script_name], cwd=work_dir)
                    p.wait()
                    outdir = os.path.join("packages", ".".join([dist, codename]))
                    try:
                        os.mkdir(outdir)
                    except:
                        pass
                    for filename in os.listdir(work_dir):
                        if filename.endswith(".deb"):
                            shutil.copy(os.path.join(work_dir, filename), os.path.join(outdir, filename))
        except yaml.YAMLError as exc:
            print(exc)

def main():
    return cli()

if __name__ == "__main__":
    sys.exit(main())
