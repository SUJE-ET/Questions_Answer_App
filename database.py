from flask import g
import sqlite3

def connect_db():
    sql = sqlite3.connect("C:/Users/sujit/OneDrive/Desktop/Question & Answer App/questions.db")
    sql.row_factory = sqlite3.Row
    return sql

def get_db():
    if not hasattr(g, "sqlite3_db"):
        g.sqlite_db= connect_db()
    return g.sqlite_db
