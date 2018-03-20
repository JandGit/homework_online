# coding=utf-8

import json

# from cgi_libs.db_tool import DbTool
# from cgi_libs.cgi_log import CgiLog
from db_tool import DbTool
from cgi_log import CgiLog


def get_student_info(user_name):
    assert isinstance(user_name, str)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.debug("student_lib: dbtool init failed while get_student_info")
        return None

    sql = ("SELECT stu_id, class_name, stu_name FROM student, class "
           "WHERE student.class_id=class.class_id AND student.stu_id=\"%s\"" %
           user_name)
    ret_data = dbtool.raw_query(sql)

    if ret_data is None:
        CgiLog.debug("student_lib: raw query failed while get_student_info")
        dbtool.destroy()
        return None

    dbtool.destroy()
    return ret_data[0]


def get_student_homework(user_name):
    assert isinstance(user_name, str)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.error("student_lib: dbtool init failed "
                     "while get_student_homework")
        return None

    sql = ("SELECT homework.hw_id, homework.title, homework.date_start, "
           "homework.date_end, t_name FROM stu_homework, homework, teacher "
           "WHERE stu_id=\"%s\" AND homework.hw_id=stu_homework.hw_id AND "
           "homework.t_id=teacher.t_id" % user_name)

    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("student_lib: raw query failed while "
                       "get_student_homework")
        dbtool.destroy()
        return None

    dbtool.destroy()
    return ret_data


def _get_free_resp_ques_data(item_data, dbtool):
    assert item_data is not None and dbtool is not None
    assert len(item_data) > 0

    (ques_id, ques_data_id, ques_type, status,
     ques_content, answer, right_answer) = item_data

    sql = ("SELECT answer FROM stu_question_choice WHERE "
           "ques_data_id=%s" % str(ques_data_id))
    ret_data = dbtool.raw_query(sql)
    if ret_data is None or 0 == len(ret_data):
        CgiLog.warning("student_lib: raw query failed while "
                       "_get_choice_ques_data")
        return None

    stu_answer = ret_data[0][0]
    return {"ques_id": ques_id, "ques_content": str(ques_content),
            "ques_type": str(ques_type), "status": str(status),
            "answer": [], "stu_answer": str(stu_answer)}


def _get_choice_ques_data(item_data, dbtool):
    assert item_data is not None and dbtool is not None
    assert len(item_data) > 0

    (ques_id, ques_data_id, ques_type, status,
     ques_content) = item_data

    sql = ("SELECT answer FROM stu_question_choice WHERE "
           "ques_data_id=%s" % str(ques_data_id))
    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("student_lib: raw query failed while "
                       "_get_choice_ques_data")
        return None

    if 0 == len(ret_data):
        stu_answer = []
    else:
        stu_answer = str(ret_data[0][0]).split(";")

    sql = ("SELECT answer, right_answer FROM question, question_choice WHERE "
           "question.ques_id=%s AND question.ques_data_id=question_choice.ques_data_id"
           % str(ques_id))
    ret_data = dbtool.raw_query(sql)
    if ret_data is None or 0 == len(ret_data):
        CgiLog.warning("student_lib: raw query failed")
        return None
    (answer, right_answer) = ret_data[0]

    if 1 == right_answer.count(";"):
        ques_type = "single_choice"
    else:
        ques_type = "multi_choice"

    return {"ques_id": ques_id, "ques_content": str(ques_content),
            "ques_type": str(ques_type), "status": str(status),
            "answer": str(answer).split(";"), "stu_answer": stu_answer}


def commit_homework(stu_id, hw_id, finished_ques):
    assert isinstance(hw_id, int) and isinstance(stu_id, str)
    assert isinstance(finished_ques, list)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed "
                       "while get_homework_detail")
        return False

    dbtool.start_transaction()
    ret = dbtool.raw_query("UPDATE stu_homework SET status=\"committed\", "
                           "date_finished=NOW() WHERE stu_id=\"%s\" "
                           "AND hw_id=%s" %
                           (stu_id, str(hw_id)))
    if ret is None:
        CgiLog.warning("insert into stu_homework failed")
        dbtool.destroy()
        return False

    for one_ques in finished_ques:
        answer = json.dumps(one_ques["stu_answer"],
                            ensure_ascii=False).replace("\"", "\\\"")

        ques_id = one_ques["ques_id"]
        sql = ("UPDATE stu_question SET date_finished=NOW(), "
               "status=\"committed\", answer=\"%s\" WHERE stu_id=\"%s\" "
               "AND hw_id=%s AND ques_id=%s" %
               (answer, stu_id, str(hw_id), str(ques_id)))
        ret = dbtool.raw_query(sql)
        if ret is None:
            CgiLog.warning("insert into stu_question failed")
            dbtool.rollback()
            dbtool.destroy()
            return False

    dbtool.commit()
    dbtool.destroy()
    return True


def get_homework_detail(stu_id, hw_id):
    assert isinstance(hw_id, int) and isinstance(stu_id, str)
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.warning("student_lib: dbtool init failed "
                       "while get_homework_detail")
        return None

    sql = ("SELECT question.ques_id, stu_question.ques_data_id, ques_type, status, "
           "ques_content FROM "
           "stu_question, question WHERE question.ques_id=stu_question.ques_id AND "
           "stu_id=\"%s\" AND hw_id=%s" % (stu_id, str(hw_id)))

    ret_data = dbtool.raw_query(sql)
    if ret_data is None or len(ret_data) == 0:
        CgiLog.warning("student_lib: raw query failed, sql:%s", sql)
        dbtool.destroy()
        return None

    questions = []
    for (ques_id, ques_data_id, ques_type, status,
            ques_content) in ret_data:
        if ques_type == "choice":
            questions_item = _get_choice_ques_data(
                (ques_id, ques_data_id, ques_type, status,
                 ques_content), dbtool)
        elif ques_type == "free_resp":
            questions_item = _get_free_resp_ques_data(
                (ques_id, ques_data_id, ques_type, status,
                 ques_content), dbtool)
        else:
            CgiLog.warning("there is a question with invalid ques_type, ignore")
            continue
        questions.append(questions_item)

    dbtool.destroy()
    return {"hw_id": hw_id, "title": "title", "author": "author",
            "status": "status", "date_start": "date_start",
            "date_end": "date_end", "questions": questions}


if __name__ == "__main__":
    # print get_homework_detail("123456", 1)
    print commit_homework("123456", 1, [{"ques_id": 1, "stu_answer": ["这是学生写的答案1", "这是学生写的答案2"]}])