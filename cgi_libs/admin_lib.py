# coding=utf-8

from cgi_log import CgiLog
from db_tool import DbTool


def _gen_teacher_list(teacher_dict):
    assert isinstance(teacher_dict, dict)
    teacher_list = []
    for (t_id, t_name, class_list) in teacher_dict.itervalues():
        teacher_list.append({"t_id": t_id, "t_name": t_name,
                             "class_list": class_list})
    return teacher_list


def search_teacher_list(search_str):
    """
    管理员查询教师列表
    :param search_str: 要查询的条件，空字符串表示无条件
    :return: 查询成功返回data字段对应的dict，查询失败返回None
    """
    assert isinstance(search_str, str)

    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("dbtool init failed")
        return None

    sql = ("SELECT teacher.t_id, teacher.t_name, class.class_name FROM "
           "teacher, teacher_class, class WHERE "
           "teacher.t_id=teacher_class.t_id AND "
           "teacher_class.class_id=class.class_id AND " 
           "(teacher.t_id LIKE \"%s%%\" or "
           "teacher.t_name LIKE \"%s%%\");") % (search_str, search_str)

    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.destroy()
        return None

    # {t_id, (t_id, t_name, [class_name])}，用于同时教多个班级的教师去重
    teachers_dict = {}
    for (t_id, t_name, class_name) in ret_data:
        if t_id in teachers_dict:
            unused_a, unused_b, class_list = teachers_dict[t_id]
            class_list.append(class_name)
        else:
            teachers_dict[t_id] = (t_id, t_name, [class_name])

    dbtool.destroy()
    return {"teachers": _gen_teacher_list(teachers_dict)}


def add_teacher(t_id, t_name, class_list):
    """
    添加教师信息
    :return: bool，True表示插入成功， False表示插入失败
    """
    assert isinstance(t_id, str)
    assert isinstance(t_name, str)
    assert isinstance(class_list, list)

    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("dbtool init failed")
        return False
    dbtool.start_transaction()
    sql = "INSERT INTO teacher(t_id, t_name) VALUES('%s', '%s');" % (t_id, t_name)
    if dbtool.raw_query(sql) is None:
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.destroy()
        return False
    for class_id in class_list:
        sql = ("INSERT INTO teacher_class(t_id, class_id) "
               "VALUES('%s', %d);" % (t_id, class_id))
        if dbtool.raw_query(sql) is None:
            CgiLog.warning("exec sql failed:%s" % sql)
            dbtool.rollback()
            dbtool.destroy()
            return False

    if not dbtool.commit():
        CgiLog.warning("commit failed")
        dbtool.rollback()
        dbtool.destroy()
        return False

    dbtool.destroy()
    return True


def modify_teacher(old_t_id, new_t_id, new_t_name, new_class_list):
    assert isinstance(old_t_id, str)
    assert isinstance(new_t_id, str)
    assert isinstance(new_t_name, str)
    assert isinstance(new_class_list, list)

    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("dbtool init failed")
        return False
    dbtool.start_transaction()
    sql = "DELETE FROM teacher_class WHERE t_id='%s';" % old_t_id
    if dbtool.raw_query(sql) is None:
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.destroy()
        return False

    for class_id in new_class_list:
        sql = ("INSERT INTO teacher_class(t_id, class_id) "
               "VALUES('%s', %d);" % (old_t_id, class_id))
        if dbtool.raw_query(sql) is None:
            CgiLog.warning("exec sql failed:%s" % sql)
            dbtool.rollback()
            dbtool.destroy()
            return False

    sql = ("UPDATE teacher SET t_id='%s' WHERE t_id='%s';"
           % (new_t_id, old_t_id))
    if dbtool.raw_query(sql) is None or not dbtool.commit():
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.rollback()
        dbtool.destroy()
        return False

    dbtool.destroy()
    return True


def del_teacher(t_id):
    assert isinstance(t_id, str)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("dbtool init failed")
        return False
    sql = "DELETE FROM teacher WHERE t_id='%s';" % t_id
    if dbtool.raw_query(sql) is None or not dbtool.commit():
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.destroy()
        return False

    dbtool.destroy()
    return True


def search_stu_list(search_str):
    assert isinstance(search_str, str)

    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("dbtool init failed")
        return None

    sql = ("SELECT stu_id, stu_name, class_name FROM "
           "student, class WHERE "
           "student.class_id=class.class_id AND "
           "(stu_id LIKE \"%s%%\" or "
           "stu_name LIKE \"%s%%\");") % (search_str, search_str)

    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.destroy()
        return None

    students = []
    for (stu_id, stu_name, class_name) in ret_data:
        students.append({"stu_id": stu_id, "stu_name": stu_name,
                         "class_name": class_name})
    return {"students": students}


def modify_stu(old_stu_id, new_stu_id, new_stu_name, new_class_id):
    assert isinstance(old_stu_id, str)
    assert isinstance(new_stu_id, str)
    assert isinstance(new_stu_name, str)
    assert isinstance(new_class_id, int)

    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("dbtool init failed")
        return False
    sql = ("UPDATE student SET stu_id='%s', stu_name='%s', class_id=%d "
           "WHERE stu_id='%s';" % (new_stu_id, new_stu_name,
                                   new_class_id, old_stu_id))
    if dbtool.raw_query(sql) is None or not dbtool.commit():
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.destroy()
        return False

    dbtool.destroy()
    return True


def del_stu(stu_id):
    assert isinstance(stu_id, str)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("dbtool init failed")
        return False
    sql = "DELETE FROM student WHERE stu_id='%s';" % stu_id
    if dbtool.raw_query(sql) is None or not dbtool.commit():
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.destroy()
        return False

    dbtool.destroy()
    return True


def add_stu(stu_id, stu_name, class_id):
    assert isinstance(stu_id, str)
    assert isinstance(stu_name, str)
    assert isinstance(class_id, int)

    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("dbtool init failed")
        return False
    sql = ("INSERT INTO student(stu_id, stu_name, class_id) "
           "VALUES('%s', '%s', %d);" % (stu_id, stu_name, class_id))

    if dbtool.raw_query(sql) is None or not dbtool.commit():
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.destroy()
        return False

    dbtool.destroy()
    return True


def _test_add_stu_and_del_stu():
    dbtool = DbTool()
    assert dbtool.init()
    sql = "DELETE FROM student WHERE stu_id='test_stu';"
    assert dbtool.raw_query(sql) is not None and dbtool.commit()

    assert add_stu("test_stu", "test_stu", 123456)
    sql = "SELECT * FROM student WHERE stu_id='test_stu';"
    ret_data = dbtool.raw_query(sql)
    assert ret_data is not None and 1 == len(ret_data)

    assert del_stu("test_stu")

    # 不加这两行代码的话，del_stu实际删除了数据库内容，
    # 但是下面的raw_query还是会查到，不知道是否因为缓存。
    # 测试到原因可能是Mysql的事务隔离，connector默认开启事务，所以，当执行了任意一条sql
    # 语句但是没有commit时，下一次读取到的内容不是数据库的最新数据。
    # 因此，这里执行commit之后，重新开启了一个新的事务，下一条select可以读取到
    # 最后问题解决，是因为InnoDB引擎默认采用REPEATABLE READ
    # dbtool.destroy()
    # dbtool.init()
    dbtool.commit()

    sql = "SELECT * FROM student WHERE stu_id='test_stu';"
    ret_data = dbtool.raw_query(sql)
    assert ret_data is not None and 0 == len(ret_data)

    dbtool.destroy()


def _test_modify_stu():
    dbtool = DbTool()
    assert dbtool.init()
    sql = "DELETE FROM student WHERE stu_id='test_stu_2';"
    assert dbtool.raw_query(sql) is not None and dbtool.commit()
    sql = "INSERT IGNORE INTO student(stu_id, stu_name, class_id) VALUES('test_stu', 'test_stu', 123456);"
    assert dbtool.raw_query(sql) is not None and dbtool.commit()

    modify_stu("test_stu", "test_stu_2", "test", 123456)
    sql = "SELECT * FROM student WHERE stu_id='test_stu_2';"
    ret_data = dbtool.raw_query(sql)
    assert ret_data is not None and 1 == len(ret_data)

    sql = "DELETE FROM student WHERE stu_id='test_stu_2';"
    assert dbtool.raw_query(sql) is not None and dbtool.commit()

    dbtool.destroy()


def _test_search_stu():
    print "\n================test_search_stu========="
    print search_stu_list("")
    print search_stu_list("123456")
    print "========================================\n"


def _test_del_teacher():
    dbtool = DbTool()
    assert dbtool.init()
    sql = ("INSERT IGNORE INTO student(stu_id, stu_name, class_id) VALUES('test_stu', 'test_stu', )")
    dbtool.destroy()
    print del_teacher("teacher_a")


def _test_add_teacher():
    print add_teacher("teacher_a", "teacher", [123456])


def _test_modify_teacher():
    print modify_teacher("teacher", "teacher10", "hehe", [])


def _test_search_teacher_list():
    print search_teacher_list("")
    print search_teacher_list("123456")
    print search_teacher_list("teacher")


if __name__ == "__main__":
    # _test_search_teacher_list()
    # _test_modify_teacher()
    # _test_add_teacher()
    # _test_del_teacher()

    _test_add_stu_and_del_stu()
    _test_modify_stu()
    _test_search_stu()
