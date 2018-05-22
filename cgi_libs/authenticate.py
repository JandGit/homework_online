# coding=utf-8
import time
import json

from cgi_libs.cgi_log import CgiLog

# 限制最大页面闲置时间为半小时
MAX_INACTIVE_TIME = 1800


def authenticate_request(request, session, req_user_type):
    """
    验证用户是否有效，安全性校验
    :param request: flask的全局变量
    :param session: flask的全局变量
    :return: True表示用户有效，False表示用户无效，用户无效时应当重新登录
    """
    if ("user_name" not in session or "login_ip" not in session
            or "user_type" not in session):
        CgiLog.info("user_name or login_ip or user_type not in session")
        return False
    if session["login_ip"] != request.remote_addr:
        CgiLog.info("current ip not equal to last login_ip, cur=%s, last=%s" %
                    (request.remote_addr, session["login_ip"]))
        return False
    if "last_act_time" not in session:
        CgiLog.info("last_act_time not in session")
        return False
    if time.time() - session["last_act_time"] > MAX_INACTIVE_TIME:
        CgiLog.info("user session timeout")
        return False

    if session["user_type"] != req_user_type:
        CgiLog.info("user type is not correct, require type:%s, "
                    "current type:%s" % (req_user_type,
                                         session["user_type"]))
        return False

    return True


def extract_req_params(req_param_str, require_params):
    """
    检查用户请求的参数是否合法，合法时将请求参数解析成dict返回
    :param req_param_str: request form string
    :param require_params: dict，{"user_name": str, "hw_id": int}这种格式
    :return: 检查到参数合法时返回dict，否则返回None
    """
    assert (isinstance(req_param_str, (str, unicode)) and
            isinstance(require_params, dict))

    if isinstance(req_param_str, unicode):
        req_param_str = req_param_str.encode("utf-8")
    try:
        req_json_obj = _json_loads_byteified(req_param_str)
    except Exception as e:
        CgiLog.exception("request params load failed:%s" % str(e))
        return None

    for require_key, require_type in require_params.iteritems():
        if require_key not in req_json_obj:
            CgiLog.info("key %s not in request" % require_key)
            return None
        if not isinstance(req_json_obj[require_key], require_type):
            CgiLog.info("key %s is type %s, require %s" %
                         (require_key, type(req_json_obj[require_key]),
                          require_type))
            return None

    return req_json_obj


def _json_loads_byteified(json_text):
    """
    这个函数对json.loads进行封装，使之生成的json对象的字符串型k、v都是str类型
    """
    return _byteify(json.loads(json_text, object_hook=_byteify, strict=False),
                    ignore_dicts=True)


def _byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True):
            _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()}
    # if it's anything else, return it in its original form
    return data


if __name__ == "__main__":
    print _json_loads_byteified('{"k1": {"k2": "v"}}')
    # print json.loads('{"key": "value"}')
