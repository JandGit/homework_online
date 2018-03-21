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

    if 1 == len(extra_data_json["answer"]):
        ques_type = "single_choice"
    else:
        ques_type = "multi_choice"

    return {"ques_id": ques_id, "ques_content": ques_content,
            "ques_type": ques_type, "answer": extra_data_json["choices"],
            "right_answer": extra_data_json["answer"]}


def _deal_free_resp_ques(item_data):
    assert item_data is not None
    (ques_id, ques_content, ques_type, ques_extra_data) = item_data
    return {"ques_id": ques_id, "ques_content": ques_content,
            "ques_type": ques_type, "answer": [],
            "right_answer": []}


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

    sql = ("SELECT ques_id, ques_content, ques_type, status, "
           "ques_extra_data FROM " 
           "question WHERE ques_id LIKE \"%s\" AND ques_type LIKE \"%s\" "
           "AND ques_content LIKE \"%s\"" % (ques_id, ques_type,
                                             ques_content))

    ret_data = dbtool.raw_query(sql)
    if ret_data is None:
        CgiLog.warning("exec sql failed:%s" % sql)
        return None

    questions = []
    idx = 0
    for (ques_id, ques_content, ques_type, ques_extra_data) in ret_data:
        if ques_type == "choice":
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

    return questions


def add_question(ques_extra_data):
    assert isinstance(ques_extra_data, dict)

