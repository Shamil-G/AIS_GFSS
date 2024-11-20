from flask import  request
from gfss_parameter import platform, http_ip_context


def ip_addr():
    if platform=='unix':
        return request.environ.get(http_ip_context)
    else:
        return request.remote_addr