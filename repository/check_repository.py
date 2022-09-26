from model.cheque import Check
from repository.db_helper import DBHelper


class CheckRepositoryDB:
    def __init__(self):
        self.conn = DBHelper().get_connector()
        self.cur = DBHelper().get_cursor()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(CheckRepositoryDB, cls).__new__(cls)
        return cls.instance

    def set_check(self, check: Check) -> None:
        insert_check_query = """ INSERT INTO cheque (user_id, bill_id, money)
                                VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET
                                bill_id = EXCLUDED.bill_id, money = EXCLUDED.money """

        args = (check.user_id, check.bill_id, check.money)
        self.cur.execute(insert_check_query, args)
        self.conn.commit()

    def get_check(self, user_id: int) -> Check:
        select_query = """ SELECT user_id, bill_id, money FROM cheque WHERE user_id = %s """

        args = (user_id,)
        self.cur.execute(select_query, args)
        fetch = self.cur.fetchone()

        check = Check(fetch[0], fetch[1], fetch[2])

        return check
