import psycopg2
from psycopg2.extensions import connection, cursor
from decouple import config


class DBHelper:
    conn = psycopg2.connect(
        database=config('DATABASE'),
        user=config('USER'),
        password=config('PASSWORD'),
        host=config('HOST'),
        port=config('PORT')
    )
    cur = conn.cursor()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DBHelper, cls).__new__(cls)
            cls.instance.setup()
        return cls.instance

    def get_connector(self) -> connection:
        return self.conn

    def get_cursor(self) -> cursor:
        return self.cur

    def setup(self):
        user_table_query = """ CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, 
                                                                  user_name VARCHAR(255),
                                                                  money INTEGER,
                                                                  block INTEGER) """

        check_table_query = """ CREATE TABLE IF NOT EXISTS cheque (user_id INTEGER PRIMARY KEY, 
                                                                  bill_id VARCHAR,
                                                                  money INTEGER) """

        self.cur.execute(user_table_query)
        self.cur.execute(check_table_query)
        self.conn.commit()
