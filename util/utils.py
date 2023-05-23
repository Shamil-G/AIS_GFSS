from app_config import debug_level, src_lang, language
from util.i18n import log, i18n
from flask import request, session
from db.connect import get_connection
from ais_gfss_parameter import using


def ip_addr():
    if using.startswith('PROD'):
        return request.environ.get('HTTP_X_REAL_IP')
    else:
        return request.remote_addr

def get_i18n_value(res_name):
    if 'language' in session:
        lang = session['language']
    else:
        lang = language
        session['language'] = language
    if debug_level > 3:
        log.info(f'UTIL. GET_i18n_VALUE. LANG: {lang}, RES_NAME: {res_name}')
    if src_lang == 'db':
        with get_connection().cursor() as cursor:
            return_value = cursor.callfunc("i18n.get_value", str, [lang, res_name])
    if src_lang == 'file':
        return_value = i18n.get_resource(lang, res_name)
    if debug_level > 3:
        log.info(f'GET_i18n_VALUE. DEBUG_LEVEL: {debug_level}, RETURN_VALUE: {return_value}')
    return return_value