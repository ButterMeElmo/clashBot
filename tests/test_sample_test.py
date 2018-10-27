#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os

import pytest


@pytest.mark.parametrize("val1, val2, val3", [
    (1, 2, 3),
    (10, 20, 30),
    #    (10, 20, 40),
])
def test_transactions(val1, val2, val3):
    assert val1 + val2 == val3


@pytest.fixture(scope='function')
def db(tmpdir):
    file = os.path.join(tmpdir.strpath, "test.db")
    conn = sqlite3.connect(file)
    conn.execute("CREATE TABLE blog (id, title, text)")
    yield conn
    conn.close()


def test_entry_creation(db):
    query = ("INSERT INTO blog "
             "(id, title, text)"
             "VALUES (?, ?, ?)")
    values = (1,
              "PyTest",
              "This is a blog entry")

    db.execute(query, values)
