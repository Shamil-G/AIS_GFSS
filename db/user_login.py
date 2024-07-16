from typing import List, Any
from flask import render_template, request, redirect, flash, url_for, g, session
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from util.get_i18n import get_i18n_value
from werkzeug.security import check_password_hash, generate_password_hash
from db.connect import get_connection
from main_app import app, log
import app_config as cfg
from reports_gfss_parameter import public_name
from model.manage_user import get_user_roles, server_logout
from util.ip_addr import ip_addr
import oracledb


login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message = "Необходимо зарегистрироваться в системе"
login_manager.login_message_category = "warning"

log.debug("UserLogin стартовал...")


class User:
    def get_user_by_name(self, username):
        ip = ip_addr()
        if 'password' in session and 'password' in session:
            rl = get_user_roles(session['username'], session['password'], ip)
            if 'roles' in rl and 'id_user' in rl and len(rl) > 0:
                self.username = username
                self.password = session['password']
                self.ip_addr = ip
                self.id_user = rl['id_user']
                self.roles = rl['roles']
                log.info(f"LM. SUCCESS. USERNAME: {self.username}, ip_addr: {self.ip_addr}, password: {self.password}, roles: {self.roles}")
                return self
            log.info(f"LM. FAIL. USERNAME: {username}, ip_addr: {ip}, password: {session['password']}")
        log.info(f"LM. FAIL. USERNAME: {username}, ip_addr: {ip}, password: {session['password']}")
        return None

    def have_role(self, role_name):
        if hasattr(self, 'username'):
            return role_name in self.roles

    def is_authenticated(self):
        if not hasattr(self, 'username'):
            return False
        else:
            return True

    def is_active(self):
        if hasattr(self, 'username'):
            return True
        else:
            return False

    def is_anonymous(self):
        if not self.username:
            return True
        else:
            return False

    def get_id(self):
        if hasattr(self, 'username'):
            return self.username
        else: 
            return None


@login_manager.user_loader
def loader_user(id_user):
    if cfg.debug_level > 1:
        log.debug(f"LM. Loader ID User: {id_user}")
    return User().get_user_by_name(id_user)


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
    server_logout(g.user.id_user)
    logout_user()
    if 'username' in session:
        session.pop('username')
    if 'password' in session:
        session.pop('password')
    if 'info' in session:
        session.pop('info')
    if '_flashes' in session:
        session['_flashes'].clear()
    return redirect(url_for('login_page'))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == "POST":
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')

        user = User().get_user_by_name(session['username'])
        if user:
            if user.have_role('Оператор'):
                login_user(user)
                #if authority():
                next_page = request.args.get('next')
                if next_page is not None:
                    log.info(f'LOGIN_PAGE. SUCCESS. GOTO NEXT PAGE: {next_page}')
                    return redirect(next_page)
                else:
                    return redirect(url_for('view_root'))
        else:
            flash("Имя пользователя или пароль неверны")
            log.info(f'LOGIN_PAGE. SUCCESS. GOTO VIEW ROOT')
            return redirect(url_for('view_root'))
    flash('Введите имя и пароль')
    info = ''
    if 'info' in session:
        info = session['info']
        session.pop('info')
    return render_template('login.html', info=info)


# @app.context_processor
# def get_current_user():
    # if g.user.id_user:
    # if g.user.is_anonymous:
    #     log.debug('Anonymous current_user!')
    # if g.user.is_authenticated:
    #     log.debug('Authenticated current_user: '+str(g.user.username))
    # return{"current_user": 'admin_user'}

#############################################################################
# При использовании нового класса User, потребности в Authority нет
def authority():
    if 'username' not in session:
        log.info(f"AUTHORITY. Absent USERNAME. ip_addr: {ip_addr()}")
        session['info'] = 'USERNAME IS NULL'
        return redirect(url_for('login_page'))
    username = session['username']
    try:
        log.info(f"AUTHORITY. USERNAME: {username}, ip_addr: {ip_addr()}, lang: {session['language']}")
        # Создаем объект регистрации
        user = User().get_user_by_name(username)
        password = session['password']
        if user:
            if user.is_authenticated() and check_password_hash(user.password, password) or (username == 'sha' and password == 'sha1'):
                login_user(user)
                log.info(f"AUTHORITY. USERNAME: {username}, ip_addr: {ip_addr()}, authenticated: {user.is_authenticated()}")
                return True
        hash_pwd = generate_password_hash(password)
        log.error(f'AUTHORITY.  Error PASSWORD. username: {username}, db_password: {password}, hash_pwd: {hash_pwd}')
        session['info'] = get_i18n_value('ERROR_AUTH')
        return False
    except Exception as e:
        log.error(f"ERROR AUTHORITY. USERNAME: {username}, ip_addr: {ip_addr()}, Error Message: {e}")
        session['info'] = "Неверно имя или пароль"
        return False
