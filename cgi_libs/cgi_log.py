# coding=utf-8
import logging

LOG_DIR = "/home/ljj/"
LOG_FILE = LOG_DIR + "cgi_log.log"

# DEBUG表示LOG输出的最低级别为DEBUG
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(filename)s[line:%(lineno)d] "
                           "%(levelname)s %(message)s", filename=LOG_FILE)

CgiLog = logging



# class CgiLog(object):
#     @staticmethod
#     def _init():
#         # 检查全局日志文件是否打开，如果没有打开则打开它，文件无法打开时抛出异常给上层
#         # 这里不处理文件没有close的问题，因为进程退出时会清理文件缓冲区
#         global G_LOG_FILE_OBJ
#         if G_LOG_FILE_OBJ is None:
#             lock = threading.Lock()
#             with lock:
#                 if G_LOG_FILE_OBJ is None:
#                     G_LOG_FILE_OBJ = open(LOG_FILE, "a")
#
#     @staticmethod
#     def debug(log_str):
#         if not isinstance(log_str, (str, unicode)):
#             return
#         CgiLog._init()
#
#         G_LOG_FILE_OBJ.write("[Debug %s] %s\n" % (time.ctime(time.time()),
#                                                   log_str))
#         G_LOG_FILE_OBJ.flush()
