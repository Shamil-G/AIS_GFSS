from app_config import src_lang, language
from util.i18n import log, i18n
from flask import request, session
from db.connect import get_connection


def get_i18n_value(res_name):
    if 'language' in session:
        lang = session['language']
    else:
        lang = language
        session['language'] = language
    log.debug(f'UTIL. GET_i18n_VALUE. LANG: {lang}, RES_NAME: {res_name}')
    if src_lang == 'db':
        with get_connection().cursor() as cursor:
            return_value = cursor.callfunc("i18n.get_value", str, [lang, res_name])
    if src_lang == 'file':
        return_value = i18n.get_resource(lang, res_name)
    log.debug(f'GET_i18n_VALUE. RETURN_VALUE: {return_value}')
    return return_value