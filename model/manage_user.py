from app_config import URL_LOGIN, debug_level
from ais_gfss_parameter import public_name
from main_app import log
import requests


def get_user_roles(username, passwd):
    request_json = { "app_name": public_name, "username": username, "passwd": passwd }
    url = f'{URL_LOGIN}/get-roles'
    try:
        resp = requests.post(url, json=request_json)
        resp_json = resp.json()
    except Exception as e:
        log.error(f'---> GET USER ROLES. URL: {url}, ERROR: {e}')
        resp_json = {"status": 'ERROR', "username": username, "roles": [], "mess": f'{e}'}
    finally:
        if debug_level > 2:
            log.info(f'-----> resp_json: {resp_json}, type: {type(resp_json)}')
        return resp_json


def change_passwd(username, passwd, new_passwd):
    request_json = { "app_name": public_name, "username": username, "passwd": passwd, "new_passwd": new_passwd }
    url = f'{URL_LOGIN}/change-passwd'
    try:
        resp = requests.post(url, json=request_json)
        resp_json = resp.json()
    except Exception as e:
        log.error(f'CHANGE PASSWD. ERROR. URL: {url}, ERROR: {e}')
        resp_json = {'status': 'ERROR', 'mess': f'{e}'}
    finally:
        if debug_level > 2:
            log.info(f"CHANGE PASSWD. USERNAME: {username}, STATUS: {resp_json['status']}")
        return resp_json


def user_info(username):
    request_json = { "app_name": public_name, "username": username }
    url = f'{URL_LOGIN}/user-info'
    try:
        resp = requests.post(url, json=request_json)
        resp_json = resp.json()
    except Exception as e:
        log.error(f'USER INFO. ERROR. URL: {url}, ERROR: {e}')
        resp_json = {'status': 'ERROR', 'mess': f'{e}'}
    finally:
        if debug_level > 2:
            log.info(f"USER INFO. USERNAME: {username}, STATUS: {resp_json['status']}")
        return resp_json