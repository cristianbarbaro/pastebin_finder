import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    conn = None
    try: 
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def insert_paste(conn, paste):
    sql = """ INSERT INTO pastes(title, paste_query_id, link, body_text, body_hash, create_date)
              VALUES(?,?,?,?,?,?) """
    cursor = conn.cursor()
    cursor.execute(sql, paste)
    conn.commit()
    #cursor.close()
    return cursor.lastrowid


def insert_query(conn, paste_query):
    sql = """ INSERT INTO Queries(paste_query)
              VALUES(?) """
    cursor = conn.cursor()
    cursor.execute(sql, (paste_query,))
    conn.commit()
    #cursor.close()
    return cursor.lastrowid


def check_exists_paste(conn, body_hash):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Pastes WHERE body_hash=?", (body_hash,))
    return cursor.fetchall()


def check_exists_query(conn, paste_query):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Queries WHERE paste_query=?", (paste_query,))
    return cursor.fetchall()