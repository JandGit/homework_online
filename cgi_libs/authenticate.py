# coding=utf-8
import time

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
