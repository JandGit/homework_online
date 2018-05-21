#! /bin/bash

G_LOG_DIR="/home/ljj/";
G_LOG_FILE=${G_LOG_DIR}"cgi_log.log";

G_BAK_LOG_DIR=${G_LOG_DIR}log_`date +%Y-%m-%d`"/";

mkdir -p ${G_BAK_LOG_DIR};

# 使用先cp然后再重定向输出的方法，确保log日志正常转移的同时，不影响现在运行的log模块
cp ${G_LOG_FILE} ${G_BAK_LOG_DIR};
echo "[system crontab]: the earlier logs have been save to backup directory." > ${G_LOG_FILE};