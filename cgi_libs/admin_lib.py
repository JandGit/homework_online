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
    assert isinstance(search_str, (str, unicode))

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
    assert isinstance(t_id, (str, unicode))
    assert isinstance(t_name, (str, unicode))
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
    assert isinstance(old_t_id, (str, unicode))
    assert isinstance(new_t_id, (str, unicode))
    assert isinstance(new_t_name, (str, unicode))
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
    assert isinstance(t_id, (str, unicode))
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
    assert isinstance(search_str, (str, unicode))

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


def _test_del_teacher():
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
    _test_del_teacher()
