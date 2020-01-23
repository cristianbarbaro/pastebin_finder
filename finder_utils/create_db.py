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

    sql_create_finded_table = """ CREATE TABLE IF NOT EXISTS Results (
                                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                    query_id INTEGER NOT NULL,
                                    site_id INTEGER,
                                    title TEXT NOT NULL,
                                    link TEXT NOT NULL,
                                    body_text TEXT NOT NULL,
                                    body_hash TEXT NOT NULL,
                                    create_date TEXT NOT NULL,
                                    FOREIGN KEY(query_id) REFERENCES Queries(id) ,
                                    FOREIGN KEY(site_id) REFERENCES Sites(id)
                                ); """

    sql_create_queries_table = """ CREATE TABLE IF NOT EXISTS Queries (
                                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                    query TEXT NOT NULL
                                );"""

    sql_create_sites_table = """ CREATE TABLE IF NOT EXISTS Sites (
                                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                site TEXT NOT NULL
                            );"""

    conn = create_connection(database)

    if conn is not None:
        create_table(conn, sql_create_finded_table)
        create_table(conn, sql_create_queries_table)
        create_table(conn, sql_create_sites_table)
    else:
        print("Error!")


if __name__ == '__main__':
    main()
    