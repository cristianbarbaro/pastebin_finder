import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    conn = None
    try: 
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def insert_found(conn, found):
    sql = """ INSERT INTO Results(title, query_id, site_id, link, body_text, body_hash, create_date)
              VALUES(?,?,?,?,?,?,?) """
    cursor = conn.cursor()
    cursor.execute(sql, found)
    conn.commit()
    #cursor.close()
    return cursor.lastrowid


def insert_query(conn, query):
    sql = """ INSERT INTO Queries(query)
              VALUES(?) """
    cursor = conn.cursor()
    cursor.execute(sql, (query,))
    conn.commit()
    #cursor.close()
    return cursor.lastrowid


def insert_site(conn, site):
    sql = """ INSERT INTO Sites(site)
              VALUES(?) """
    cursor = conn.cursor()
    cursor.execute(sql, (site,))
    conn.commit()
    #cursor.close()
    return cursor.lastrowid


def check_exists_found(conn, body_hash):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Results WHERE body_hash=?", (body_hash,))
    return cursor.fetchall()


def check_exists_query(conn, query):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Queries WHERE query=?", (query,))
    return cursor.fetchall()


def check_exists_site(conn, site):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Sites WHERE site=?", (site,))
    return cursor.fetchall()