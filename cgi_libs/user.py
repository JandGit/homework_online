# coding=utf-8

from cgi_libs.db_tool import DbTool
from cgi_libs.cgi_log import CgiLog


RET_DB_TOOL_ERR = -3
RET_NO_SUCH_USER = -2
RET_PWD_ERR = -1


def authenticate_user(user_name, password):
    """
    用户帐号密码验证
    :return: (result, user_type)，其中result代表验证结果，0表示验证通过，-1表示密码错误，-2表示帐号不存在，-3表示参数有误
               其他值表示服务器异常。user_type在验证成功时会赋值为用户类型，如"admin"、"student"等
    """
    if not isinstance(user_name, str) or not isinstance(password, str):
        CgiLog.debug("user:bad params")
        return RET_DB_TOOL_ERR, ""

    dbtool = DbTool()
    if not dbtool.init():
        return RET_DB_TOOL_ERR, ""

    ret_data = dbtool.query("user", "user_name, password, user_type",
                            "user_name=\"%s\"" % user_name)

    dbtool.destroy()
    if ret_data is None:
        return RET_DB_TOOL_ERR, ""
    if 0 == len(ret_data):
        CgiLog.debug("user:find no user")
        return RET_NO_SUCH_USER, ""

    expected_ret_field_len = 3
    if len(ret_data[0]) != expected_ret_field_len:
        CgiLog.debug("user:db return wrong field count")
        return RET_DB_TOOL_ERR, ""

    (ret_user_name, ret_password, ret_user_type) = ret_data[0]
    if ret_user_name != user_name or ret_password != password:
        CgiLog.debug("user:password incorrect")
        return RET_PWD_ERR, ""

    return 0, ret_user_type


def get_notices(user_name):
    """
    获取公告信息
    :param user_name: 用户名
    :return: 返回dict存放公告，为data字段的内容。返回None表示获取失败。
    """
    if not isinstance(user_name, str):
        CgiLog.debug("user: user_name is not str")
        return None
    dbtool = DbTool()
    if not dbtool.init():
        CgiLog.debug("user: dbtool init failed while get_notices")
        return None

    sql = ("SELECT notice.notice_id, notice.title, notice.date, "
           "notice.user_name, content FROM "
           "notify, notice WHERE notice.notice_id=notify.notice_id AND "
           "notify.user_name=\"%s\"" % user_name)
    ret_data = dbtool.raw_query(sql)
    dbtool.destroy()

    if ret_data is None:
        CgiLog.debug("user: dbtool error while get_notices")
        return None

    notices = []
    for (notice_id, title, date, author, content) in ret_data:
        notices.append({"notice_id": notice_id,
                            "title": title,
                            "date": str(date),
                            "author": author,
                            "content": content})

    return {"notices": notices}
