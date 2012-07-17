import os

from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-sonicwall",
    version = "0.0.1",
    author = "Clay McClure",
    author_email = "clay@daemons.net",
    description = "Django app for authorizing SonicWall LHM wifi clients",
    keywords = "sonicwall,lhm,wifi,hotspot",
    packages = ['sonicwall'],
    install_requires = ['requests', 'django'],
    long_description = read('README'),
    classifiers = [
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: BSD License",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
    ],
)
