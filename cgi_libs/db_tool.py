# coding=utf-8

import mysql.connector
from mysql.connector import errorcode

from cgi_log import CgiLog


class DbTool(object):
    def __init__(self):
        self.m_db_connector = None

    def init(self):
        """
        连接到Mysql数据库
        :return: 成功返回True,失败返回False,失败记录cgi日志
        """
        if self.m_db_connector is not None:
            return True

        try:
            self.m_db_connector = mysql.connector.connect(
                user="cgi", password="cgi", database="homework_online")
            return True
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                CgiLog.debug("dbtool:username or password error")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                CgiLog.debug("dbtool:Database does not exist")
            else:
                CgiLog.debug("dbtool:%s" % str(err))
            return False

    def destroy(self):
        if self.m_db_connector is not None:
            self.m_db_connector.close()
            self.m_db_connector = None

    def start_transaction(self):
        assert self.m_db_connector is not None
        self.m_db_connector.start_transaction()

    def commit(self):
        assert self.m_db_connector is not None
        self.m_db_connector.commit()

    def rollback(self):
        assert self.m_db_connector is not None
        self.m_db_connector.rollback()

    def raw_query(self, sql):
        """
        执行原始sql语句
        :return: 执行成功时返回list，执行失败时返回None
        """
        assert isinstance(sql, (str, unicode))
        assert self.m_db_connector is not None

        cursor = None
        try:
            cursor = self.m_db_connector.cursor()
            cursor.execute(sql)
        except mysql.connector.Error as err:
            CgiLog.debug("dbtool:err while raw_query:%s, err:%s" %
                         (sql, str(err)))
            if cursor is not None:
                cursor.close()
            return None

        data = []
        for row in cursor:
            data.append(row)
        cursor.close()
        CgiLog.debug("exec sql ok:%s" % sql)

        return data

    def insert(self, table_name, data_dict):
        """
        插入一行数据到db
        e.g. dbtool.insert("student", {"stu_id": 3114006520,"class_id": 123456})
        :return: 成功返回True，失败返回False
        """
        assert isinstance(data_dict, dict) and len(data_dict) > 0
        assert isinstance(table_name, (str, unicode))
        assert self.m_db_connector is not None

        column_names = data_dict.keys()
        column_values = data_dict.values()
        sql_column_name = ""
        sql_column_value = ""

        for i in range(len(data_dict)):
            sql_column_name += str(column_names[i])
            sql_column_value += "%s"
            if i != len(data_dict) - 1:
                sql_column_name += ", "
                sql_column_value += ", "

        sql = ("INSERT INTO %s (%s) VALUES (%s)" %
               (table_name, sql_column_name, sql_column_value))

        cursor = None
        try:
            cursor = self.m_db_connector.cursor()
            cursor.execute(sql, column_values)
            self.m_db_connector.commit()
        except mysql.connector.Error as err:
            CgiLog.debug("dbtool:err while insert:%s, err:%s" %
                         (sql, str(err)))
            if cursor is not None:
                cursor.close()
            return False

        cursor.close()
        return True

    def query(self, table_name, column_names, where_str):
        assert (isinstance(table_name, (str, unicode)) and
                isinstance(column_names, (str, unicode)) and
                isinstance(where_str, (str, unicode)))
        assert self.m_db_connector is not None

        sql = "SELECT %s FROM %s WHERE %s" % (column_names,
                                              table_name, where_str)

        cursor = None
        try:
            cursor = self.m_db_connector.cursor()
            cursor.execute(sql)
        except mysql.connector.Error as err:
            CgiLog.debug("dbtool:err while query:%s, err:%s" %
                         (sql, str(err)))
            if cursor is not None:
                cursor.close()
            return None

        data = []
        for row in cursor:
            data.append(row)
        cursor.close()

        return data

    def update(self, table_name, data_dict, where_str):
        assert isinstance(data_dict, dict) and len(data_dict) > 0
        assert isinstance(table_name, (str, unicode)) and isinstance(where_str, (str, unicode))
        assert self.m_db_connector is not None

        value_set_str = ""
        column_names = data_dict.keys()
        column_values = data_dict.values()
        for i in range(len(data_dict)):
            value_set_str += "%s=%s" % (str(column_names[i]), str(column_values[i]))
            if i != len(data_dict) - 1:
                value_set_str += ", "

        sql = "UPDATE %s SET %s WHERE %s" % (table_name,
                                             value_set_str, where_str)

        cursor = None
        try:
            cursor = self.m_db_connector.cursor()
            cursor.execute(sql)
            self.m_db_connector.commit()
        except mysql.connector.Error as err:
            CgiLog.debug("dbtool:err while update:%s, err:%s" %
                         (sql, str(err)))
            if cursor is not None:
                cursor.close()
            return False

        cursor.close()
        return True


# self test
if __name__ == "__main__":

    # 测试sql
    def get_sql_str(table_name, data_dict):
        column_cnt = len(data_dict)
        column_names = data_dict.keys()
        column_values = data_dict.values()
        sql_column_name = ""
        sql_column_value = ""

        for i in range(column_cnt):
            sql_column_name += str(column_names[i])
            sql_column_value += "%s"
            if i != column_cnt - 1:
                sql_column_name += ", "
                sql_column_value += ", "

        sql = ("INSERT INTO %s (%s) VALUES (%s)" %
               (table_name, sql_column_name, sql_column_value))
        return sql, column_values
    # print get_sql_str("user", {"user_name": "user1", "password": "pwd"})

    # 测试insert等操作
    def test_dbtool():
        dbtool = DbTool()
        assert dbtool.init()
        assert dbtool.insert("student",
                             {"stu_id": 3114006520,
                              "class_id": 123456,
                              "stu_name": "j",
                              "stu_gender": "man",
                              "stu_department": 123456})

        print dbtool.query("student", "stu_id, class_id, stu_name", "1=1")

        assert dbtool.update("student",
                             {"class_id": 123456,
                              "stu_name": "\"hehehehehehehehehheeheheh\"",
                              "stu_gender": "\"man\"",
                              "stu_department": 123456},
                             "stu_id=3114006520"
                             )
        print dbtool.query("student", "stu_id, class_id, stu_name", "1=1")

    test_dbtool()
