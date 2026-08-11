import sqlite3
import datetime


DB="memory.db"


def init_memory():

    conn=sqlite3.connect(DB)

    c=conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS memories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        memory TEXT,
        category TEXT,
        created TEXT
    )
    """)

    conn.commit()
    conn.close()



def save_memory(user_id, text, category="general"):

    conn=sqlite3.connect(DB)

    c=conn.cursor()

    c.execute("""
    INSERT INTO memories
    (user_id,memory,category,created)
    VALUES(?,?,?,?)
    """,
    (
        user_id,
        text,
        category,
        str(datetime.datetime.now())
    ))

    conn.commit()
    conn.close()



def get_memory(user_id):

    conn=sqlite3.connect(DB)

    c=conn.cursor()

    c.execute("""
    SELECT memory
    FROM memories
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 20
    """,
    (user_id,))


    rows=c.fetchall()

    conn.close()


    return [
        r[0]
        for r in rows
    ]