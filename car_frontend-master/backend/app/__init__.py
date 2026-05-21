from flask import Flask
import logging

# 禁用Flask默认的HTTP请求日志
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__,
            template_folder="../../frontend/dist",
            static_folder="../../frontend/dist/static")

from app import app
