from flask import  request
from reports_gfss_parameter import platform


def ip_addr():
    if platform=='unix':
        return request.environ.get('HTTP_X_REAL_IP')
    else:
        return request.remote_addr