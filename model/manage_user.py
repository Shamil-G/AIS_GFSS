from app_config import URL_GET_ROLES, URL_CHANGE_PASSWD
from ais_gfss_parameter import public_name
from main_app import log
import requests


def get_user_roles(username, passwd):
    request_json = { "app_name": public_name, "username": username, "passwd": passwd }
    resp = requests.post(URL_GET_ROLES, json=request_json)
    log.info(f'---> GET USER ROLES. RESP: {resp} : {type(resp)}')
    try:
        resp_json = resp.json()
    except Exception as e:
        resp_json = {'status': 'ERROR', 'mess': f'{e}'}
    finally:
        log.info(f'-----> resp_json: {resp_json}, type: {type(resp_json)}')
        return resp_json


def change_passwd(username, passwd, new_passwd):
    request_json = { "app_name": public_name, "username": username, "passwd": passwd, "new_passwd": new_passwd }
    resp = requests.post(URL_CHANGE_PASSWD, json=request_json)
    resp_json = resp.json()
    log.info(f"SET USER PASSWD. STATUS: {resp_json['status']}")
    return resp_json