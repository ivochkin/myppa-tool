#!/usr/bin/env python3

import os
import sys
import shutil
import click
import yaml
from myppa.utils import *
from myppa.spec import Spec

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
    packages_dir = os.path.join(cwd, "packages")
    variants = []
    for package_name in os.listdir(packages_dir):
        package_dir = os.path.join(packages_dir, package_name)
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
                spec = Spec()
                spec.parse(spec_file)
                for pkg in spec.packages():
                    for version in pkg.versions():
                        for arch in pkg.architectures():
                            variant = (
                                pkg.name(),
                                version,
                                distribution_name,
                                codename,
                                arch)
                            variants.append(variant)

    print("Name", "Version", "Distribution", "Codename", "Architecture")
    for var in variants:
        print(var)


@cli.command()
@click.argument("name")
@click.argument("distribution")
@click.argument("architecture")
def build(name, distribution, architecture):
    with open("spec.yaml", 'r') as stream:
        try:
            for i in yaml.load_all(stream):
                print(i)
        except yaml.YAMLError as exc:
            print(exc)

def main():
    return cli()

if __name__ == "__main__":
    sys.exit(main())
