# coding=utf-8
import json

from cgi_libs.db_tool import DbTool
from cgi_libs.cgi_log import CgiLog


def _deal_choice_ques(item_data):
    assert item_data is not None
    (ques_id, ques_content, ques_type, ques_extra_data) = item_data
    # 将ques_extra_data解析成预计的选择题附加字段格式
    try:
        extra_data_json = json.loads(ques_extra_data.replace("\\\"", "\""))
    except Exception:
        CgiLog.exception("json load error")
        return None
    if "choices" not in extra_data_json or "answer" not in extra_data_json:
        CgiLog.warning("error extra_data_json")
        return None

    return {"ques_id": ques_id, "ques_content": ques_content,
            "ques_type": ques_type,
            "answer": {"choices": extra_data_json["choices"],
                       "answer": extra_data_json["answer"]}}


def _deal_free_resp_ques(item_data):
    assert item_data is not None
    (ques_id, ques_content, ques_type, ques_extra_data) = item_data
    return {"ques_id": ques_id, "ques_content": ques_content,
            "ques_type": ques_type, "answer": {}}


def get_questions(ques_id=None, ques_type=None, ques_content=None):
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.debug("student_lib: dbtool init failed")
        return None

    # 这样处理是为了使用sql语句的LIKE匹配时，None字段可以无条件匹配
    if ques_id is None:
        ques_id = ""
    if ques_type is None:
        ques_type = ""
    if ques_content is None:
        ques_content = ""

    sql = ("SELECT ques_id, ques_content, ques_type, ques_extra_data FROM " 
           "question WHERE ques_id LIKE \"%s%%\" AND ques_type LIKE \"%s%%\" "
           "AND ques_content LIKE \"%s%%\"" % (ques_id, ques_type,
                                               ques_content))

    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("exec sql failed:%s" % sql)
        dbtool.destroy()
        return None

    questions = []
    idx = 0
    for (ques_id, ques_content, ques_type, ques_extra_data) in ret_data:
        if ques_type == "single_choice" or ques_type == "multi_choice":
            json_item = _deal_choice_ques(ret_data[idx])
        elif ques_type == "free_resp":
            json_item = _deal_free_resp_ques(ret_data[idx])
        else:
            # 发现异常题目
            CgiLog.warning("wrong ques_type %s in db" % ques_type)
            json_item = None

        if json_item is not None:
            questions.append(json_item)
        idx += 1

    dbtool.destroy()
    return {"questions": questions}


def add_question(ques_dict):
    assert isinstance(ques_dict, dict)

    try:
        ques_extra_data = json.dumps(
            ques_dict["answer"], ensure_ascii=False).replace("\"", "\\\"")
    except Exception:
        CgiLog.exception("json dump failed, request_data:%s" %
                         str(ques_dict))
        return False

    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.debug("student_lib: dbtool init failed")
        return False

    if not dbtool.insert("question",
                         {"ques_content": ques_dict["ques_content"],
                          "ques_type": ques_dict["ques_type"],
                          "ques_extra_data": ques_extra_data}):
        CgiLog.warning("insert data to question failed")
        dbtool.destroy()
        return False

    dbtool.destroy()
    return True


def _get_homework_item(item_data, dbtool):
    assert item_data is not None and dbtool is not None
    (hw_id, status, title, date_start, date_end, t_name) = item_data
    sql = ("SELECT class_name from class, homework_class WHERE "
           "homework_class.class_id=class.class_id AND "
           "homework_class.hw_id=%s" % hw_id)
    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("query failed")
        return None

    class_names = []
    for (one_name,) in ret_data:
        class_names.append(one_name)

    return {"hw_id": hw_id, "status": status, "title": title,
            "date_start": str(date_start), "date_end": str(date_end),
            "author": t_name, "class_names": class_names}


def get_homeworks(t_id, status=None):
    assert isinstance(t_id, (str, unicode))
    # 这样处理是为了sql查询时，status=None表示查询匹配所有
    if status is None:
        status = ""

    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed")
        return None

    sql = ("SELECT hw_id, status, title, date_start, date_end, t_name "
           "FROM homework, teacher WHERE "
           "homework.t_id=teacher.t_id AND "
           "teacher.t_id=\"%s\" AND homework.status LIKE \"%s%%\"" %
           (t_id, status))

    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("query failed")
        dbtool.destroy()
        return None

    homeworks = []
    for item_data in ret_data:
        item = _get_homework_item(item_data, dbtool)
        if item is None:
            CgiLog.warning("get one hw item failed")
        else:
            homeworks.append(item)

    dbtool.destroy()
    return {"homeworks": homeworks}


def get_homework_detail(hw_id):
    assert isinstance(hw_id, int) and hw_id >= 0
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed")
        return None

    sql = ("SELECT title, t_name, status, date_start, date_end FROM " 
           "homework, teacher WHERE homework.t_id=teacher.t_id AND "
           "homework.hw_id=%s" % hw_id)
    ret_data = dbtool.raw_query(sql)
    if ret_data is None or 0 == len(ret_data):
        CgiLog.warning("query failed")
        dbtool.destroy()
        return None
    (title, t_name, status, date_start, date_end) = ret_data[0]
    homework_detail = {"hw_id": hw_id, "title": title, "status": status,
                       "date_start": str(date_start),
                       "date_end": str(date_end)}

    sql = ("SELECT class_id, class_name FROM homework_class, class WHERE "
           "homework_class.class_id=class.class_id AND hw_id=%s" % hw_id)
    ret_data = dbtool.raw_query(sql)
    if ret_data is None or 0 == len(ret_data):
        CgiLog.warning("query failed")
        dbtool.destroy()
        return None
    class_ids = []
    class_names = []
    for (a_class_id, a_class_name) in ret_data:
        class_ids.append(a_class_id)
        class_names.append(a_class_name)
    homework_detail["class_ids"] = class_ids
    homework_detail["class_names"] = class_names

    sql = ("SELECT ques_id, ques_content, ques_type, ques_extra_data FROM "
           "question, homework_question WHERE "
           "question.ques_id=homework_question.ques_id AND "
           "homework_question.hw_id=%s" % hw_id)
    ret_data = dbtool.raw_query(sql)
    if ret_data is None or 0 == len(ret_data):
        CgiLog.warning("query failed")
        dbtool.destroy()
        return None

    questions = []
    idx = 0
    for (ques_id, ques_content, ques_type, ques_extra_data) in ret_data:
        if ques_type == "single_choice" or ques_type == "multi_choice":
            json_item = _deal_choice_ques(ret_data[idx])
        elif ques_type == "free_resp":
            json_item = _deal_free_resp_ques(ret_data[idx])
        else:
            # 发现异常题目
            CgiLog.warning("wrong ques_type %s in db" % ques_type)
            json_item = None

        if json_item is not None:
            questions.append(json_item)
        idx += 1

    homework_detail["questions"] = questions
    dbtool.destroy()
    return homework_detail


def get_stu_homeworks(homework_type, class_id):
    assert isinstance(homework_type, (str, unicode))
    assert isinstance(class_id, int)
    if homework_type == "all":
        homework_type = ""
    elif homework_type == "unchecked":
        homework_type = "committed"
    if -1 == class_id:
        class_id = ""

    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed")
        return None

    sql = ("SELECT homework.hw_id, homework.title, homework.date_start, "
           "homework.date_end, student.stu_id, student.stu_name, "
           "stu_homework.date_finished, class_name FROM stu_homework, homework, "
           "student, class WHERE stu_homework.hw_id=homework.hw_id AND "
           "stu_homework.stu_id=student.stu_id AND "
           "student.class_id=class.class_id AND "
           "stu_homework.status LIKE \"%s%%\" AND "
           "student.class_id LIKE \"%s%%\"" %
           (homework_type, class_id))
    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("query failed")
        dbtool.destroy()
        return None

    homeworks = []
    for (hw_id, title, date_start, date_end, stu_id, stu_name,
            date_finished, class_name) in ret_data:
        homeworks.append({"hw_id": hw_id, "title": title,
                          "date_start": str(date_start),
                          "date_end": str(date_end),
                          "stu_id": stu_id, "stu_name": stu_name,
                          "date_finished": str(date_finished),
                          "class_name": class_name})

    dbtool.destroy()
    return {"homeworks": homeworks}


def get_stu_homeworks_detail(stu_id, hw_id):
    assert isinstance(stu_id, (str, unicode))
    assert isinstance(hw_id, int) and hw_id >= 0
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed")
        return None

    sql = ("SELECT homework.title, t_name, stu_homework.status, "
           "homework.date_start, "
           "homework.date_end, student.stu_name, "
           "class_name, score, comment FROM "
           "homework, teacher, student, stu_homework, class WHERE "
           "class.class_id=student.class_id AND "
           "homework.t_id=teacher.t_id AND "
           "student.stu_id=stu_homework.stu_id AND "
           "homework.hw_id=stu_homework.hw_id AND "
           "student.stu_id=\"%s\" AND homework.hw_id=%s" % (stu_id, hw_id))
    ret_data = dbtool.raw_query(sql)
    if ret_data is None or 0 == len(ret_data):
        CgiLog.warning("query failed")
        dbtool.destroy()
        return None
    (title, t_name, status, date_start, date_end, stu_name, class_name,
        score, comment) = ret_data[0]
    homework_detail = {"hw_id": hw_id, "title": title, "status": status,
                       "date_start": str(date_start),
                       "date_end": str(date_end),
                       "stu_name": stu_name, "class_name": class_name,
                       "score": score}

    sql = ("SELECT question.ques_id, question.ques_content, "
           "question.ques_type, question.ques_extra_data, "
           "stu_question.answer, stu_question.score, "
           "stu_question.comment FROM "
           "question, stu_question WHERE "
           "question.ques_id=stu_question.ques_id AND "
           "stu_question.stu_id=\"%s\" AND "
           "stu_question.hw_id=%s" % (stu_id, hw_id))
    ret_data = dbtool.raw_query(sql)
    if ret_data is None or 0 == len(ret_data):
        CgiLog.warning("query failed")
        dbtool.destroy()
        return None

    questions = []
    idx = 0
    for (ques_id, ques_content, ques_type, ques_extra_data,
            stu_answer, score, comment) in ret_data:
        if ques_type == "single_choice" or ques_type == "multi_choice":
            json_item = _deal_choice_ques((ques_id, ques_content,
                                           ques_type, ques_extra_data))
        elif ques_type == "free_resp":
            json_item = _deal_free_resp_ques((ques_id, ques_content,
                                              ques_type, ques_extra_data))
        else:
            # 发现异常题目
            CgiLog.warning("wrong ques_type %s in db" % ques_type)
            json_item = None

        if json_item is not None:
            try:
                stu_answer_json_obj = json.loads(
                    stu_answer.replace("\\\"", "\""))
            except Exception:
                stu_answer_json_obj = {}
            json_item["stu_answer"] = stu_answer_json_obj
            json_item["score"] = score
            json_item["comment"] = comment
            questions.append(json_item)
        idx += 1

    homework_detail["questions"] = questions
    dbtool.destroy()
    return homework_detail


def add_homework(t_id, hw_params):
    assert isinstance(t_id, (str, unicode))
    assert isinstance(hw_params, dict)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed")
        return False

    class_ids = hw_params["class_ids"]
    del hw_params["class_ids"]

    dbtool.start_transaction()
    sql = ("INSERT INTO homework(title, date_start, date_end, t_id) VALUES "
           "(\"%s\", \"%s\", \"%s\", \"%s\")" %
           (hw_params["title"], hw_params["date_start"],
            hw_params["date_end"], t_id))
    if dbtool.raw_query(sql) is None:
        CgiLog.warning("insert failed")
        dbtool.destroy()
        return False

    ret_data = dbtool.raw_query("SELECT LAST_INSERT_ID()")
    if ret_data is None or 0 == len(ret_data):
        CgiLog.warning("get last insert id failed")
        dbtool.rollback()
        dbtool.destroy()
        return False
    hw_id = ret_data[0]

    for a_class_id in class_ids:
        sql = ("INSERT INTO homework_class(hw_id, class_id) VALUES (%s, %s)"
               % (hw_id, a_class_id))
        if dbtool.raw_query(sql) is None:
            CgiLog.warning("insert failed")
            dbtool.rollback()
            dbtool.destroy()
            return False

    dbtool.commit()
    dbtool.destroy()
    return True


def get_teach_class(t_id):
    assert isinstance(t_id, (str, unicode))
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed")
        return None

    sql = ("SELECT class.class_id, class.class_name FROM class, "
           "teacher_class WHERE class.class_id=teacher_class.class_id "
           "AND t_id=\"%s\"" % t_id)
    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("raw_query failed")
        dbtool.destroy()
        return None

    class_info = []
    for (class_id, class_name) in ret_data:
        class_info.append({"class_id": class_id, "class_name": class_name})

    dbtool.destroy()
    return {"class": class_info}


def get_teacher_info(t_id):
    assert isinstance(t_id, (str, unicode))
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed")
        return None

    sql = ("SELECT t_name, dept_name FROM teacher, department WHERE "
           "teacher.dept_id=department.dept_id AND "
           "teacher.t_id=\"%s\"" % t_id)

    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("raw_query failed")
        dbtool.destroy()
        return None

    (t_name, dept_name) = ret_data[0]
    dbtool.destroy()
    return {"t_name": t_name, "t_id": t_id, "dept_name": dept_name}


def add_question_to_hw(hw_id, ques_id):
    assert isinstance(hw_id, int) and isinstance(ques_id, int)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed")
        return False

    sql = ("INSERT IGNORE INTO homework_question(hw_id, ques_id) " 
           "VALUES (%s, %s)" % (hw_id, ques_id))
    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("raw_query failed")
        dbtool.destroy()
        return False

    dbtool.destroy()
    return True


def del_question_from_hw(hw_id, ques_id):
    assert isinstance(hw_id, int) and isinstance(ques_id, int)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed")
        return False

    sql = ("DELETE FROM homework_question WHERE hw_id=%s AND ques_id=%s" %
           (hw_id, ques_id))
    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("raw_query failed")
        dbtool.destroy()
        return False

    dbtool.destroy()
    return True
