from flask import render_template, request, redirect, flash, url_for, g, session
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from os import environ

from ldap.ldap_login import LDAP_User
from ldap.ldap_user_info import ldap_user_info
# from db.connect import get_connection
from main_app import app, log
import app_config as cfg
# from gfss_parameter import public_name
from util.ip_addr import ip_addr


login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message = "Необходимо зарегистрироваться в системе"
login_manager.login_message_category = "warning"

log.debug("user_login стартовал...")

@login_manager.user_loader
def loader_user(id_user):
    if cfg.debug_level > 1:
        log.debug(f"LM. Loader ID User: {id_user}")
    # return User().get_user_by_name(id_user)
    return LDAP_User().get_user_by_name(id_user)


@app.after_request
def redirect_to_signing(response):
    if response.status_code == 401:
        return redirect(url_for('view_systems') + '?next=' + request.url)
    return response
    

@app.before_request
def before_request():
    g.user = current_user


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    log.info(f"LM. LOGOUT. USERNAME: {session['username']}, ip_addr: {ip_addr()}")
    logout_user()
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
    return redirect(url_for('login_page'))
    # return redirect(url_for('login_page'))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if "STYLE" in environ:
        session['styles']=environ["STYLES"]
    else:
        session['styles']=cfg.styles
    
    if '_flashes' in session:
         session['_flashes'].clear()
    
    if request.method == "POST":
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')
        log.debug(f"LOGIN_PAGE. POST. lang: username: {session['username']}, password: {session['password']}, ip_addr: {ip_addr()}")

        # user = User().get_user_by_name(session['username'])
        user = LDAP_User().get_user_by_name(session['username'])

        # Если такой username существует и объект user создался, надо проверить пароль и вытащить атрибуты
        if user:
            login_user(user)
            next_page = request.args.get('next')
            if next_page is not None:
                log.info(f'LOGIN_PAGE. SUCCESS AUTHORITY. GOTO NEXT PAGE: {next_page}')
                return redirect(next_page)
            else:
                return redirect(url_for('view_systems'))
        else:
            log.error(f'LOGIN_PAGE. FAIL USERNAME. {session['username']}')
        flash("Имя пользователя или пароль неверны")
        log.error(f'LOGIN_PAGE. FAIL AUTHORITY')
    flash('Введите имя и пароль')
    return render_template('login.html')



# @app.context_processor
# def get_current_user():
    # if g.user.id_user:
    # if g.user.is_anonymous:
    #     log.debug('Anonymous current_user!')
    # if g.user.is_authenticated:
    #     log.debug('Authenticated current_user: '+str(g.user.username))
    # return{"current_user": 'admin_user'}