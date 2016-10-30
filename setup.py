from setuptools import setup

setup(
    name="myppa",
    setup_requires=["vcversioner"],
    author="Stanislav Ivochkin",
    author_email="isn@extrn.org",
    description=("Manage your own PPA"),
    license="MIT",
    url="https://github.com/ivochkin/myppa-tool",
    packages=["myppa"],
    package_data={"myppa": "snippets/*"},
    entry_points={
        "console_scripts": [
            "myppa = myppa.cli:main"
        ]
    }
)
