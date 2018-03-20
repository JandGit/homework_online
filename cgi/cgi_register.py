# coding=utf-8
import json
import time

from flask import Flask
from flask import request, session

from cgi_libs.cgi_log import CgiLog
from cgi_libs.authenticate import authenticate_request
from cgi_libs.authenticate import extract_req_params
from cgi_libs.user import authenticate_user
from cgi_libs.user import get_notices
from cgi_libs.user import RET_PWD_ERR
from cgi_libs.user import RET_NO_SUCH_USER
from cgi_libs import student_lib

app = Flask(__name__)
app.secret_key = "GDUT_SOFTWARE_ENGINEERING"


RESULT_CGI_SUCCESS = 0
RESULT_SESS_EXPIRE = 1
RESULT_CGI_ERR = 300

RESULT_USERNAME_NOT_EXIST = 100
RESULT_PWD_NOT_RIGHT = 101
RESULT_SERVER_ERR = 102
RESULT_BAD_PARAMS = 103


def gen_result_str(result, data):
    assert isinstance(result, int) and isinstance(data, dict)
    return json.dumps({"result": result, "data": data},
                      ensure_ascii=False)


@app.route("/login", methods=["post"])
def login():
    req_params = extract_req_params(request, {"user_name": (str, unicode),
                                              "password": (str, unicode)})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    # 前端传来莫名的unicode，需要转str
    user_name = str(req_params["user_name"])
    password = str(req_params["password"])

    auth_ret, user_type = authenticate_user(user_name, password)
    if auth_ret != 0:
        CgiLog.debug("cgi:authenticate user failed while login")
        if auth_ret == RET_NO_SUCH_USER:
            err_code = RESULT_USERNAME_NOT_EXIST
        elif auth_ret == RET_PWD_ERR:
            err_code = RESULT_PWD_NOT_RIGHT
        else:
            err_code = RESULT_CGI_ERR
        CgiLog.debug("cgi:start return")
        return gen_result_str(err_code, {})

    session["user_name"] = user_name
    session["login_ip"] = request.remote_addr
    session["last_act_time"] = time.time()
    return gen_result_str(RESULT_CGI_SUCCESS,
                          {"user_type": user_type})


@app.route("/student/student_info", methods=["post"])
def get_student_info():
    if not authenticate_request(request, session):
        CgiLog.warning("authenticate_request failed")
        return gen_result_str(RESULT_SESS_EXPIRE, {})

    data = student_lib.get_student_info(session["user_name"])
    if data is None:
        CgiLog.warning("cgi: get_student_info error")
        return gen_result_str(RESULT_CGI_ERR, {})

    (student_id, class_name, student_name) = data
    if (student_id is None or class_name is None
            or student_name is None):
        CgiLog.warning("cgi:wrong db field in student info")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS,
                          {"student_id": student_id,
                           "class_name": class_name,
                           "student_name": student_name})


@app.route("/student/notices", methods=["post"])
def get_student_notices():
    if not authenticate_request(request, session):
        CgiLog.warning("cgi:authenticate_request failed "
                       "while get_student_notices")
        return gen_result_str(RESULT_SESS_EXPIRE, {})

    notices = get_notices(session["user_name"])
    if notices is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    ret_notices = []
    for (notice_id, title, date, author, content) in notices:
        ret_notices.append({"notice_id": notice_id,
                            "title": title,
                            "date": str(date),
                            "author": author,
                            "content": content})

    return gen_result_str(RESULT_CGI_SUCCESS,
                          {"notices": ret_notices})


@app.route("/student/homeworks", methods=["post"])
def get_student_homeworks():
    if not authenticate_request(request, session):
        CgiLog.warning("cgi:authenticate_request failed while "
                       "get_student_homeworks")
        return gen_result_str(RESULT_SESS_EXPIRE, {})
    req_params = extract_req_params(request,
                                    {"homework_type": (str, unicode)})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    ret_data = student_lib.get_student_homework(session["user_name"],
                                                req_params["homework_type"])
    if ret_data is None:
        return gen_result_str(RESULT_CGI_ERR, {})

    ret_homeworks = []
    for (hw_id, title, date_start, date_end, author) in ret_data:
        ret_homeworks.append({"hw_id": hw_id,
                              "title": title,
                              "date_start": str(date_start),
                              "date_end": str(date_end),
                              "author": author})

    return gen_result_str(RESULT_CGI_SUCCESS,
                          {"homeworks": ret_homeworks})


@app.route("/student/commit_homework", methods=["post"])
def commit_homework():
    if not authenticate_request(request, session):
        CgiLog.warning("cgi:authenticate_request failed while "
                       "get_homework_detail")
        return gen_result_str(RESULT_SESS_EXPIRE, {})
    req_params = extract_req_params(request, {"questions": list,
                                              "hw_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    questions = req_params["questions"]
    hw_id = req_params["hw_id"]
    result = student_lib.commit_homework(session["user_name"],
                                         hw_id, questions)
    if result:
        return gen_result_str(RESULT_CGI_SUCCESS, {})
    else:
        return gen_result_str(RESULT_CGI_ERR, {})


@app.route("/student/homework_detail", methods=["post"])
def get_homework_detail():
    if not authenticate_request(request, session):
        CgiLog.warning("cgi:authenticate_request failed while "
                       "get_homework_detail")
        return gen_result_str(RESULT_SESS_EXPIRE, {})
    req_params = extract_req_params(request, {"hw_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    hw_detail = student_lib.get_homework_detail(session["user_name",
                                                req_params["hw_id"]])
    if hw_detail is None:
        CgiLog.warning("get homework detail error")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, hw_detail)

