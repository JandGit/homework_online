# coding=utf-8
import json
import time
import functools

from flask import Flask
from flask import request
from flask import session
from flask import redirect

from cgi_libs.cgi_log import CgiLog
from cgi_libs.authenticate import authenticate_request
from cgi_libs.authenticate import extract_req_params
from cgi_libs.user import authenticate_user
from cgi_libs.user import RET_PWD_ERR
from cgi_libs.user import RET_NO_SUCH_USER
from cgi_libs import student_lib
from cgi_libs import teacher_lib
from cgi_libs import admin_lib
from cgi_libs import user

app = Flask(__name__)
app.secret_key = "GDUT_SOFTWARE_ENGINEERING"


# 返回给前端的结果码reuslt定义
RESULT_CGI_SUCCESS = 0              # 成功
RESULT_SESS_EXPIRE = 1              # 登录信息过期
RESULT_USERNAME_NOT_EXIST = 100     # 登录用户名不存在
RESULT_PWD_NOT_RIGHT = 101          # 登录密码错误
RESULT_SERVER_ERR = 201             # 服务器内部错误
RESULT_BAD_PARAMS = 202             # CGI调用参数出错
RESULT_CGI_ERR = 203                # CGI程序出错


def auth_user(req_user_type):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            if not authenticate_request(request, session, req_user_type):
                CgiLog.warning("authenticate_request failed")
                return gen_result_str(RESULT_SESS_EXPIRE, {})
            else:
                return func(*args, **kw)
        return wrapper

    return decorator


def gen_result_str(result, data):
    assert isinstance(result, int) and isinstance(data, dict)
    return json.dumps({"result": result, "data": data},
                      ensure_ascii=False)


@app.route("/login", methods=["post"])
def login():
    req_params = extract_req_params(request.data,
                                    {"user_name": str,
                                     "password": str})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    CgiLog.debug("login user_name=%s, pwd=%s" %
                 (req_params["user_name"], req_params["password"]))
    user_name = req_params["user_name"]
    password = req_params["password"]

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
    session["user_type"] = user_type
    session["login_ip"] = request.remote_addr
    session["last_act_time"] = time.time()
    return gen_result_str(RESULT_CGI_SUCCESS,
                          {"user_type": user_type})


@app.route("/student/student_info", methods=["post"])
@auth_user("student")
def get_student_info():
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
@auth_user("student")
def get_student_notices():
    ret_notices = user.get_notices(session["user_name"])
    if ret_notices is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    return gen_result_str(RESULT_CGI_SUCCESS, ret_notices)


@app.route("/student/homeworks", methods=["post"])
@auth_user("student")
def get_student_homeworks():
    req_params = extract_req_params(request.data,
                                    {"homework_type": str})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    ret_data = student_lib.get_student_homework(
        session["user_name"], str(req_params["homework_type"]))
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
@auth_user("student")
def commit_homework():
    req_params = extract_req_params(request.data,
                                    {"questions": list, "hw_id": int})
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
@auth_user("student")
def get_homework_detail():
    req_params = extract_req_params(request.data, {"hw_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    hw_detail = student_lib.get_homework_detail(session["user_name"],
                                                req_params["hw_id"])
    if hw_detail is None:
        CgiLog.warning("get homework detail error")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, hw_detail)


@app.route("/teacher/stu_homeworks", methods=["post"])
@auth_user("teacher")
def get_stu_homeworks():
    req_params = extract_req_params(request.data,
                                    {"homework_type": str,
                                     "class_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    ret_data = teacher_lib.get_stu_homeworks(
        req_params["homework_type"], req_params["class_id"], session["user_name"])
    if ret_data is None:
        CgiLog.warning("get student homeworks failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, ret_data)


@app.route("/teacher/stu_homeworks_detail", methods=["post"])
@auth_user("teacher")
def get_stu_homeworks_detail():
    req_params = extract_req_params(request.data,
                                    {"stu_id": str,
                                     "hw_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    ret_data = teacher_lib.get_stu_homeworks_detail(
        req_params["stu_id"], req_params["hw_id"])
    if ret_data is None:
        CgiLog.warning("stu_homeworks_detail failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, ret_data)


@app.route("/teacher/stu_homeworks/check", methods=["post"])
@auth_user("teacher")
def check_stu_homework():
    req_params = extract_req_params(request.data,
                                    {"stu_id": str,
                                     "hw_id": int,
                                     "score": (int, float),
                                     "comment": str})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    if not teacher_lib.check_stu_homework(req_params["stu_id"],
                                          req_params["hw_id"],
                                          req_params["score"],
                                          req_params["comment"]):
        CgiLog.warning("check student hw failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/teacher/questions", methods=["get"])
@auth_user("teacher")
def get_questions():
    ret_data = teacher_lib.get_questions()
    if ret_data is None:
        CgiLog.warning("stu_homeworks_detail failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, ret_data)


@app.route("/teacher/questions", methods=["post"])
@auth_user("teacher")
def add_question():
    params = extract_req_params(request.data,
                                {"ques_content": str,
                                 "ques_type": str,
                                 "answer": dict})
    if params is None:
        CgiLog.warning("bad params:%s" % str(request.data))
        return gen_result_str(RESULT_BAD_PARAMS, {})

    if not teacher_lib.add_question(params):
        CgiLog.warning("add question failed")
        return gen_result_str(RESULT_CGI_ERR, {})
    else:
        return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/teacher/del_question", methods=["post"])
@auth_user("teacher")
def del_question():
    params = extract_req_params(request.data, {"ques_id": int})
    if params is None:
        CgiLog.warning("bad params:%s" % str(request.data))
        return gen_result_str(RESULT_BAD_PARAMS, {})

    if not teacher_lib.del_question(params["ques_id"]):
        CgiLog.debug("delete question failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/teacher/homeworks", methods=["post"])
@auth_user("teacher")
def get_t_homeworks():
    ret_data = teacher_lib.get_homeworks(session["user_name"])
    if ret_data is None:
        CgiLog.warning("get homeworks failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, ret_data)


@app.route("/teacher/homeworks/publish", methods=["post"])
@auth_user("teacher")
def publish_homework():
    params = extract_req_params(request.data, {"hw_id": int})
    if params is None:
        CgiLog.warning("bad params:%s" % str(request.data))
        return gen_result_str(RESULT_BAD_PARAMS, {})

    if not teacher_lib.publish_homework(params["hw_id"]):
        CgiLog.warning("publish homeworks failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/teacher/homeworks/homeworks_detail", methods=["post"])
@auth_user("teacher")
def get_t_homeworks_detail():
    req_params = extract_req_params(request.data,
                                    {"hw_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    homework_detail = teacher_lib.get_homework_detail(req_params["hw_id"])
    if homework_detail is None:
        CgiLog.warning("get homeworks failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, homework_detail)


@app.route("/teacher/homeworks/edit", methods=["post"])
@auth_user("teacher")
def add_t_homeworks():
    req_params = extract_req_params(request.data,
                                    {"title": str,
                                     "date_start": str,
                                     "date_end": str,
                                     "class_ids": list})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    if not teacher_lib.add_homework(session["user_name"], req_params):
        return gen_result_str(RESULT_SERVER_ERR, {})
    else:
        return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/teacher/teach_class", methods=["get"])
@auth_user("teacher")
def get_teach_class():
    class_info = teacher_lib.get_teach_class(session["user_name"])
    if class_info is None:
        CgiLog.warning("get teach class failed")
        return gen_result_str(RESULT_SERVER_ERR, {})
    else:
        return gen_result_str(RESULT_CGI_SUCCESS, class_info)


@app.route("/teacher/teacher_info", methods=["get"])
@auth_user("teacher")
def get_teacher_info():
    teacher_info = teacher_lib.get_teacher_info(session["user_name"])
    if teacher_info is None:
        CgiLog.warning("get teach class failed")
        return gen_result_str(RESULT_SERVER_ERR, {})
    else:
        return gen_result_str(RESULT_CGI_SUCCESS, teacher_info)


@app.route("/teacher/homeworks/add_question", methods=["post"])
@auth_user("teacher")
def add_question_to_hw():
    req_params = extract_req_params(request.data,
                                    {"hw_id": int, "ques_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    if not teacher_lib.add_question_to_hw(req_params["hw_id"],
                                          req_params["ques_id"]):
        CgiLog.warning("add question to hw failed")
        return gen_result_str(RESULT_SERVER_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/teacher/homeworks/del_question", methods=["post"])
@auth_user("teacher")
def del_question_from_hw():
    req_params = extract_req_params(request.data,
                                    {"hw_id": int, "ques_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    if not teacher_lib.del_question_from_hw(req_params["hw_id"],
                                            req_params["ques_id"]):
        CgiLog.warning("del question to hw failed")
        return gen_result_str(RESULT_SERVER_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/teacher/get_notices", methods=["get"])
@auth_user("teacher")
def teacher_get_notices():
    ret_notices = user.get_notices(session["user_name"])
    if ret_notices is None:
        CgiLog.debug("get notices failed")
        return gen_result_str(RESULT_SERVER_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, ret_notices)


@app.route("/teacher/add_notice", methods=["post"])
@auth_user("teacher")
def teacher_add_notices():
    req_params = extract_req_params(request.data,
                                    {"title": str,
                                     "content": str,
                                     "class_list": list})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})
    
    result = teacher_lib.add_notice(session["user_name"],
                                    req_params["title"],
                                    req_params["content"],
                                    req_params["class_list"])

    if not result:
        CgiLog.debug("add notice failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/teacher/del_notice", methods=["post"])
@auth_user("teacher")
def teacher_del_notice():
    req_params = extract_req_params(request.data,
                                    {"notice_id": int})

    if not teacher_lib.del_notice(session["user_name"],
                                  req_params["notice_id"]):
        CgiLog.debug("del notice failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/admin/teacher_list", methods=["post"])
@auth_user("admin")
def search_teacher_list():
    req_params = extract_req_params(request.data,
                                    {"search": str})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    ret_data = admin_lib.search_teacher_list(req_params["search"])
    if ret_data is None:
        CgiLog.warning("search_teacher_list failed")
        return gen_result_str(RESULT_SERVER_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, ret_data)


@app.route("/admin/add_teacher", methods=["post"])
@auth_user("admin")
def add_teacher():
    req_params = extract_req_params(request.data,
                                    {"t_id": str,
                                     "t_name": str,
                                     "class_list": list})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    result = admin_lib.add_teacher(req_params["t_id"], req_params["t_name"],
                                   req_params["class_list"])
    if not result:
        CgiLog.debug("add teacher failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/admin/class_info", methods=["get"])
@auth_user("admin")
def get_class_info():
    class_list = admin_lib.get_class_info()
    if class_list is None:
        CgiLog.debug("get class info failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, class_list)


@app.route("/admin/del_class", methods=["post"])
@auth_user("admin")
def del_class():
    req_params = extract_req_params(request.data,
                                    {"class_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})
    if not admin_lib.del_class(req_params["class_id"]):
        CgiLog.info("delete failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/admin/add_class", methods=["post"])
@auth_user("admin")
def add_class():
    req_params = extract_req_params(request.data,
                                    {"class_name": str})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})
    if not admin_lib.add_class(req_params["class_name"]):
        CgiLog.info("add class failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/admin/modify_class", methods=["post"])
@auth_user("admin")
def modify_class():
    req_params = extract_req_params(request.data,
                                    {"class_id": int,
                                     "class_name": str})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})
    if not admin_lib.modify_class(req_params["class_id"],
                                  req_params["class_name"]):
        CgiLog.info("modify failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/admin/modify_teacher", methods=["post"])
@auth_user("admin")
def modify_teacher():
    req_params = extract_req_params(request.data,
                                    {"old_t_id": str,
                                     "new_t_id": str,
                                     "new_t_name": str,
                                     "new_class_list": list})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    result = admin_lib.modify_teacher(req_params["old_t_id"],
                                      req_params["new_t_id"],
                                      req_params["new_t_name"],
                                      req_params["new_class_list"])
    if not result:
        CgiLog.debug("modify teacher failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/admin/del_teacher", methods=["post"])
@auth_user("admin")
def del_teacher():
    req_params = extract_req_params(request.data,
                                    {"t_id": str})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    result = admin_lib.del_teacher(req_params["t_id"])
    if not result:
        CgiLog.debug("del teacher failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/admin/stu_list", methods=["post"])
@auth_user("admin")
def search_stu_list():
    req_params = extract_req_params(request.data,
                                    {"search": str})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    students = admin_lib.search_stu_list(req_params["search"])
    if students is None:
        CgiLog.debug("del teacher failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, students)


@app.route("/admin/modify_stu", methods=["post"])
@auth_user("admin")
def modify_stu():
    req_params = extract_req_params(request.data,
                                    {"old_stu_id": str,
                                     "new_stu_id": str,
                                     "new_stu_name": str,
                                     "new_class_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    result = admin_lib.modify_stu(req_params["old_stu_id"],
                                  req_params["new_stu_id"],
                                  req_params["new_stu_name"],
                                  req_params["new_class_id"])
    if not result:
        CgiLog.debug("modify teacher failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/admin/del_stu", methods=["post"])
@auth_user("admin")
def del_stu():
    req_params = extract_req_params(request.data,
                                    {"stu_id": str})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    result = admin_lib.del_stu(req_params["stu_id"])
    if not result:
        CgiLog.debug("del student failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})


@app.route("/admin/add_stu", methods=["post"])
@auth_user("admin")
def add_stu():
    req_params = extract_req_params(request.data,
                                    {"stu_id": str,
                                     "stu_name": str,
                                     "class_id": int})
    if req_params is None:
        return gen_result_str(RESULT_BAD_PARAMS, {})

    result = admin_lib.add_stu(req_params["stu_id"], req_params["stu_name"],
                               req_params["class_id"])
    if not result:
        CgiLog.debug("add student failed")
        return gen_result_str(RESULT_CGI_ERR, {})

    return gen_result_str(RESULT_CGI_SUCCESS, {})
