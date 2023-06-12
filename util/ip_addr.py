from flask import  request
from ais_gfss_parameter import using


def ip_addr():
    if using.startswith('PROD'):
        return request.environ.get('HTTP_X_REAL_IP')
    else:
        return request.remote_addr