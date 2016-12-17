from setuptools import setup

setup(
    name="myppa",
    setup_requires=["vcversioner"],
    vcversioner={
        'version_module_paths': ['myppa/_version.py'],
    },
    author="Stanislav Ivochkin",
    author_email="isn@extrn.org",
    description=("Manage your own PPA"),
    license="MIT",
    url="https://github.com/ivochkin/myppa-tool",
    packages=["myppa"],
    include_package_data=True,
    package_data={"myppa": ["data/templates/*"]},
    entry_points={
        "console_scripts": [
            "myppa = myppa.cli:main"
        ]
    },
    install_requires=[
        "click>=6.0",
        "Jinja2>=2.7",
        "PyYAML>=3.12",
        "xmltodict>=0.10",
        "requests>=2.12",
    ],
)
