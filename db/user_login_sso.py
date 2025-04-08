from flask import render_template, request, redirect, flash, url_for, g, session
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from db.sso_login import SSO_User
from werkzeug.security import check_password_hash, generate_password_hash
from db.connect import get_connection
from main_app import app, log
from app_config import sso_server
from gfss_parameter import public_name, debug
from util.ip_addr import ip_addr
from os import environ
import requests 
import json

login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message = "Необходимо зарегистрироваться в системе"
login_manager.login_message_category = "warning"

log.info("user_login_sso стартовал...")

@login_manager.user_loader
def loader_user(id_user):
    log.debug(f"LM. Loader ID User: {id_user}")
    # return User().get_user_by_name(id_user)
    return SSO_User().get_user_by_name(id_user)


@app.after_request
def redirect_to_signing(response):
    if response.status_code == 401:
        return redirect(url_for('view_root') + '?next=' + request.url)
    return response
    

@app.before_request
def before_request():
    g.user = current_user


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    log.info(f"LM. LOGOUT. USERNAME: {session['username']}, ip_addr: {ip_addr()}")
    logout_user()
    username = session['username']
    if 'username' in session:
        session.pop('username')
    if 'password' in session:
        session.pop('password')
    if 'info' in session:
        session.pop('info')
    if 'list_bd' in session:
        session.pop('list_bd')
    if '_flashes' in session:
        session['_flashes'].clear()

    req_json = {'ip_addr': f'{ip_addr()}'}

    resp = requests.post(url=f'{sso_server}/close', json=req_json)

    if resp.status_code != 200:
        log.info(f'----------------\n\tОшибка {resp.status_code} соединения {username} с сервером SSO\n----------------')
        return redirect(url_for('view_root'))

    resp_json = resp.json()

    if 'status' in resp_json and resp_json['status'] !=200:
        log.info(f'----------------\n\tОшибка закрытия сессии. Статус: {resp_json['status']}/{ip_addr()}\n----------------')

    return redirect(url_for('view_root'))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    log.info(f'LOGIN. \n\taddr: {sso_server}/check from {ip_addr()}')
    if 'styles' not in session:
        if "STYLE" in environ:
            session['styles']=environ["STYLES"]
        else:
            session['styles']='styles'
    
    if '_flashes' in session:
         session['_flashes'].clear()
    
    user = ''
    json_user = ''

    if request.method == "GET":
        req_json = {'ip_addr': f'{ip_addr()}'}
        resp = requests.post(url=f'{sso_server}/check', json=req_json)

        log.debug(f'LOGIN CHECK. \n\taddr: {sso_server}/check\n\tresp: {resp}')
        if resp.status_code == 200:
            resp_json=resp.json()
            log.debug(f'LOGIN GET. resp_json: {resp_json}')
            if 'status' in resp_json and resp_json['status'] == 200:
                json_user = resp_json['user']
                log.info(f'LOGIN GET. json_user: {json_user}')
                session['username'] = json_user['login_name']
            else:
                log.info(f'----------------\n\tUSER {ip_addr()} not Registred\n----------------')
                return render_template('login.html')

    if request.method == "POST":
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')

        req_json = {'login_name': session['username'], 'password': session['password'], 'ip_addr': ip_addr() }
        log.debug(f'LOGIN POST. REQUEST JSON: {req_json}')

        resp = requests.post(url=f'{sso_server}/login', json=req_json)
        if resp.status_code != 200:
            log.info(f'----------------\n\tОшибка {resp.status_code} соединения с сервером SSO\n----------------')
            return render_template('login.html')

        resp_json=resp.json()
        log.debug(f'LOGIN POST. resp_json: {resp_json}/{type(resp_json)}')
        if resp_json['status'] !=200:
            log.info(f'----------------\n\tUSER {session['username']}/{session['password']} not Registred\n----------------')
            return render_template('login.html')

        json_user = resp_json['user']
        # session['username'] = json_user['login_name']
        # session['password'] = json_user['password']
        log.info(f'LOGIN POST. json_user: {json_user}')

    # Если такой username существует и объект user создался, надо проверить пароль и вытащить атрибуты
    if json_user:
        log.info(f'LOGIN. json_user: {json_user}')
        user = SSO_User().get_user_by_name(json_user)

        login_user(user)
        next_page = request.args.get('next')
        if next_page is not None:
            log.info(f'LOGIN_PAGE. SUCCESS AUTHORITY. GOTO NEXT PAGE: {next_page}')
            return redirect(next_page)
        else:
            return redirect(url_for('view_root'))
    
    return render_template('login.html')


# @app.context_processor
# def get_current_user():
    # if g.user.id_user:
    # if g.user.is_anonymous:
    #     log.debug('Anonymous current_user!')
    # if g.user.is_authenticated:
    #     log.debug('Authenticated current_user: '+str(g.user.username))
    # return{"current_user": 'admin_user'}