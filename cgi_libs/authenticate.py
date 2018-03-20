# coding=utf-8
import time
import json

from cgi_libs.cgi_log import CgiLog

# 限制最大页面闲置时间为半小时
MAX_INACTIVE_TIME = 1800


def authenticate_request(request, session):
    """
    验证用户是否有效，安全性校验
    :param request: flask的全局变量
    :param session: flask的全局变量
    :return: True表示用户有效，False表示用户无效，用户无效时应当重新登录
    """
    if "user_name" not in session or "login_ip" not in session:
        CgiLog.debug("user_name or login_ip not in session")
        return False
    if session["login_ip"] != request.remote_addr:
        CgiLog.debug("current ip not equal to last login_ip, cur=%s, last=%s" %
                     (request.remote_addr, session["login_ip"]))
        return False
    if "last_act_time" not in session:
        CgiLog.debug("last_act_time not in session")
        return False
    if time.time() - session["last_act_time"] > MAX_INACTIVE_TIME:
        CgiLog.debug("user session timeout")
        return False

    return True


def extract_req_params(request, require_params):
    """
    检查用户请求的参数是否合法，合法时将请求参数解析成dict返回
    :param request: flask request
    :param require_params: dict，{"user_name": str, "hw_id": int}这种格式
    :return: 检查到参数合法时返回dict，否则返回None
    """
    assert isinstance(require_params, dict)
    try:
        req_json_obj = json.loads(request.data)
    except Exception as e:
        CgiLog.exception("request params load failed:%s" % str(e))
        return None

    for require_key, require_type in require_params:
        if require_key not in req_json_obj:
            CgiLog.debug("key %s not in request" % require_key)
            return None
        if not isinstance(req_json_obj[require_key], require_type):
            CgiLog.debug("key %s is type %s, require %s" %
                         (require_key, type(req_json_obj[require_key]),
                          require_type))
            return None

    return req_json_obj
