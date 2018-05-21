# coding=utf-8

import json

from cgi_libs.db_tool import DbTool
from cgi_libs.cgi_log import CgiLog


def get_student_info(user_name):
    assert isinstance(user_name, str)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.debug("student_lib: dbtool init failed while get_student_info")
        return None

    sql = ("SELECT stu_id, class_name, stu_name FROM student, class "
           "WHERE student.class_id=class.class_id AND student.stu_id='%s';" %
           user_name)
    ret_data = dbtool.raw_query(sql)

    if ret_data is None:
        CgiLog.debug("student_lib: raw query failed while get_student_info")
        dbtool.destroy()
        return None

    dbtool.destroy()
    return ret_data[0]


def get_student_homework(user_name, homework_type):
    assert (isinstance(user_name, str) and
            isinstance(homework_type, str))
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.error("student_lib: dbtool init failed "
                     "while get_student_homework")
        return None

    sql = ("SELECT homework.hw_id, homework.title, homework.date_start, "
           "homework.date_end, t_name FROM stu_homework, homework, teacher "
           "WHERE stu_id='%s' AND stu_homework.status='%s' AND "
           "homework.status='published' AND "
           "homework.hw_id=stu_homework.hw_id AND "
           "homework.t_id=teacher.t_id;" % (user_name, homework_type))

    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("student_lib: raw query failed")
        dbtool.destroy()
        return None

    dbtool.destroy()
    return ret_data


def _get_free_resp_ques_data(item_data):
    assert item_data is not None and len(item_data) > 0

    (ques_id, ques_type, status, ques_content,
        ques_extra_data, stu_answer) = item_data
    try:
        # 这里使用strict=False，防止存在回车符导致json解析失败
        stu_answer = json.loads(stu_answer, strict=False)["answer"]
    except Exception as err:
        CgiLog.warning("stu_answer has wrong format:%s\n err:%s" %
                       (stu_answer, str(err)))
        stu_answer = ""

    return {"ques_id": ques_id, "ques_content": ques_content,
            "ques_type": ques_type, "status": status,
            "answer": [], "stu_answer": stu_answer}


def _get_choice_ques_data(item_data):
    assert item_data is not None and len(item_data) > 0

    (ques_id, ques_type, status, ques_content,
        ques_extra_data, stu_answer) = item_data

    try:
        extra_json_of_ques = json.loads(ques_extra_data, strict=False)
    except Exception:
        CgiLog.warning("ques_extra_data has wrong format")
        return None
    if ("choices" not in extra_json_of_ques or
            "answer" not in extra_json_of_ques):
        CgiLog.warning("ques_extra_data has wrong format")
        return None
    try:
        stu_answer_json = json.loads(stu_answer, strict=False)
        stu_answer = stu_answer_json["choices"]
    except Exception:
        stu_answer = []

    return {"ques_id": ques_id, "ques_content": ques_content,
            "ques_type": ques_type, "status": status,
            "answer": extra_json_of_ques["choices"],
            "stu_answer": stu_answer}


def commit_homework(stu_id, hw_id, finished_ques):
    assert isinstance(hw_id, int) and isinstance(stu_id, str)
    assert isinstance(finished_ques, list)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed "
                       "while get_homework_detail")
        return False

    dbtool.start_transaction()
    ret = dbtool.raw_query("UPDATE stu_homework SET status='committed', "
                           "date_finished=NOW() WHERE stu_id='%s' "
                           "AND hw_id='%s';" %
                           (stu_id, str(hw_id)))
    if ret is None:
        CgiLog.warning("insert into stu_homework failed")
        dbtool.destroy()
        return False

    for one_ques in finished_ques:
        if (one_ques["ques_type"] == "single_choice" or
                one_ques["ques_type"] == "multi_choice" or
                one_ques["ques_type"] == "judge"):
            answer = json.dumps({"choices": one_ques["stu_answer"]},
                                ensure_ascii=False)
        else:
            answer = json.dumps({"answer": one_ques["stu_answer"]},
                                ensure_ascii=False)
        ques_id = one_ques["ques_id"]
        sql = ("UPDATE stu_question SET date_finished=NOW(), "
               "status='committed', answer='%s' WHERE stu_id='%s' "
               "AND hw_id='%s' AND ques_id='%s';" %
               (answer, stu_id, str(hw_id), str(ques_id)))
        ret = dbtool.raw_query(sql)
        if ret is None:
            CgiLog.warning("insert into stu_question failed")
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


def get_homework_detail(stu_id, hw_id):
    assert isinstance(hw_id, int) and isinstance(stu_id, str)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed "
                       "while get_homework_detail")
        return None

    sql = ("SELECT question.ques_id, ques_type, status, ques_content, "
           "ques_extra_data, answer FROM stu_question, question WHERE "
           "question.ques_id=stu_question.ques_id AND "
           "stu_id='%s' AND hw_id=%s" % (stu_id, str(hw_id)))

    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("student_lib: raw query failed, sql:%s", sql)
        dbtool.destroy()
        return None

    questions = []
    idx = 0
    for (ques_id, ques_type, status, ques_content,
            ques_extra_data, stu_answer) in ret_data:
        if (ques_type == "single_choice" or ques_type == "multi_choice"
                or ques_type == "judge"):
            json_item = _get_choice_ques_data(ret_data[idx])
        elif ques_type == "free_resp":
            json_item = _get_free_resp_ques_data(ret_data[idx])
        else:
            CgiLog.warning("there is a question with "
                           "invalid ques_type, ignore")
            json_item = None

        if json_item is not None:
            questions.append(json_item)
        idx += 1

    sql = ("SELECT homework.title, t_name, stu_homework.status, "
           "homework.date_start, homework.date_end, stu_homework.score, "
           "stu_homework.comment FROM homework, teacher, stu_homework "
           "WHERE homework.hw_id='%s' AND stu_homework.stu_id='%s' AND "
           "stu_homework.hw_id=homework.hw_id "
           "AND homework.t_id=teacher.t_id;" % (hw_id, stu_id))
    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("student_lib: raw query failed, sql:%s", sql)
        dbtool.destroy()
        return None
    (title, author, status, date_start, date_end, score, comment) = ret_data[0]

    dbtool.destroy()
    return {"hw_id": hw_id, "title": title, "author": author,
            "status": status, "date_start": str(date_start),
            "date_end": str(date_end), "questions": questions,
            "score": score, "comment": comment}


if __name__ == "__main__":
    # print get_homework_detail("123456", 1)
    print commit_homework("123456", 1, [{"ques_id": 1, "stu_answer": ["这是学生写的答案1", "这是学生写的答案2"]}])