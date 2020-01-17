import sqlite3
import config
from sqlite3 import Error


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
 
    return conn


def create_table(conn, sql_statement):
    try:
        c = conn.cursor()
        c.execute(sql_statement)
        conn.commit()
        c.close()
    except Error as e:
        print(e)


def main():
    database = config.DB

    sql_create_pastes_table = """ CREATE TABLE IF NOT EXISTS Pastes (
                                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                    paste_query_id INTEGER NOT NULL,
                                    title TEXT NOT NULL,
                                    link TEXT NOT NULL,
                                    body_text TEXT NOT NULL,
                                    body_hash TEXT NOT NULL,
                                    create_date TEXT NOT NULL,
                                    FOREIGN KEY(paste_query_id) REFERENCES Queries(id) 
                                ); """

    sql_create_queries_table = """ CREATE TABLE IF NOT EXISTS Queries (
                                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                    paste_query text NOT NULL
                                );"""

    conn = create_connection(database)

    if conn is not None:
        create_table(conn, sql_create_pastes_table)
        create_table(conn, sql_create_queries_table)
    else:
        print("Error!")


if __name__ == '__main__':
    main()
    