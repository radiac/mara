#!/usr/bin/python
from __future__ import unicode_literals

from talker import service

if __name__ == '__main__':  # pragma: no cover
    service.run(store_path='talker_store')
