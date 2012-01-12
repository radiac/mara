import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "cletus",
    version = "2.0.0",
    author = "Richard Terry",
    author_email = "python@richardterry.co.uk",
    description = ("A simple chatroom server"),
    license = "BSD",
    keywords = "socket proxy telnet http gateway",
    url = "http://richardterry.co.uk/projects/cletus/",
    long_description=read('README'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Internet :: Proxy Servers",
        "License :: OSI Approved :: BSD License",
    ],
    
    zip_safe=True,
    packages=['cletus'],
    scripts=['bin/cletus']
)
