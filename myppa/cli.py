#!/usr/bin/env python3

import os
import sys
import shutil
import hashlib
import uuid
from subprocess import Popen
import click
import yaml
from myppa import __version__
from myppa.utils import *
from myppa.package import Package
import sqlite3

@click.group()
@click.version_option(__version__)
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
    conn = sqlite3.connect(get_packages_db())
    c = conn.cursor()
    print("Packages with fixed versions")
    for row in c.execute("SELECT name, version from package WHERE NOT version_is_computed ORDER BY name"):
        print(row[0], row[1])
    print("Packages with version computed upon build")
    for row in c.execute("SELECT name, version from package WHERE version_is_computed ORDER BY name"):
        print(row[0], row[1])
    conn.close()

@cli.command()
def update():
    specs = []
    for root, dirs, files in os.walk(get_specs_dir()):
        for filename in files:
            if filename.endswith('.yaml'):
                specs.append(os.path.join(root, filename))
    click.echo("Total {} spec files found".format(len(specs)))
    if os.path.exists(get_packages_db()):
        os.remove(get_packages_db())
    conn = sqlite3.connect(get_packages_db())
    c = conn.cursor()
    c.execute("CREATE TABLE package (name TEXT, version_is_computed INTEGER, version TEXT, description TEXT)")
    for spec in specs:
        click.echo("Processing '{}'".format(spec))
        with open(spec, 'r') as f:
            for document in yaml.load_all(f):
                for name, package in document.items():
                    if not name.startswith("package-"):
                        continue
                    pkg = Package(package)
                    pkg.validate()
                    pkg.persist(conn)
    conn.commit()
    conn.close()

@cli.command()
@click.argument("package")
@click.option("--format",
        type=click.Choice(supported_formats()),
        default=supported_formats()[0])
def show(package, format):
    description = get_package(package).description()
    click.echo(format_object(description, format))

@cli.command()
@click.argument("package")
@click.option("--distribution", "-d",
        type=click.Choice(supported_distributions()),
        default=supported_distributions()[0])
@click.option("--architecture", "-a",
        type=click.Choice(supported_architectures()),
        default=supported_architectures()[0])
@click.option("--format",
        type=click.Choice(supported_formats()),
        default=supported_formats()[0])
def resolve(package, distribution, architecture, format):
    dist, codename = parse_distribution(distribution)
    resolved = get_package(package).resolve(dist, codename, architecture)
    click.echo(format_object(resolved, format))

@cli.command()
@click.argument("package")
@click.option("--distribution", "-d",
        type=click.Choice(supported_distributions()),
        default=supported_distributions()[0])
@click.option("--architecture", "-a",
        type=click.Choice(supported_architectures()),
        default=supported_architectures()[0])
def script(package, distribution, architecture):
    click.echo(get_script(package, distribution, architecture))

@cli.command()
@click.argument("package")
@click.option("--distribution", "-d",
        type=click.Choice(supported_distributions()),
        default=supported_distributions()[0])
@click.option("--architecture", "-a",
        type=click.Choice(supported_architectures()),
        default=supported_architectures()[0])
def build(package, distribution, architecture):
    dist, codename = parse_distribution(distribution)
    script = get_script(package, distribution, architecture)
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

def main():
    return cli()

if __name__ == "__main__":
    sys.exit(main())
