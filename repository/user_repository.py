from model.user import User
from repository.db_helper import DBHelper


class UserRepositoryDB:
    def __init__(self):
        self.conn = DBHelper().get_connector()
        self.cur = DBHelper().get_cursor()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(UserRepositoryDB, cls).__new__(cls)
        return cls.instance

    def set_user(self, user: User) -> None:
        insert_user_query = """ INSERT INTO users (user_id, user_name, money, block) 
                                VALUES (%s, %s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET 
                                user_name = EXCLUDED.user_name, money = EXCLUDED.money, block = EXCLUDED.block """

        args = (user.user_id, user.user_name, user.money, user.block)
        self.cur.execute(insert_user_query, args)
        self.conn.commit()

    def get_user(self, user_id: int) -> User:
        select_query = """ SELECT user_id, user_name, money, block FROM users WHERE user_id = %s """

        args = (user_id,)
        self.cur.execute(select_query, args)
        fetch = self.cur.fetchone()

        user = User(fetch[0], fetch[1])
        user.money = fetch[2]
        user.block = fetch[3]

        return user

    def get_users(self) -> list[tuple[int, int]]:

        select_query = """ SELECT user_id, money FROM users """

        self.cur.execute(select_query)
        fetch = self.cur.fetchall()

        return fetch
