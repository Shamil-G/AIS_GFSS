from typing import List, Any
from flask import render_template, request, redirect, flash, url_for, g, session
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from util.utils import ip_addr, get_i18n_value
import cx_Oracle
from werkzeug.security import check_password_hash, generate_password_hash
from db.connect import get_connection
from main_app import app, log
import app_config as cfg
from ais_gfss_parameter import public_name
from model.manage_user import get_user_roles


login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message = "Необходимо зарегистрироваться в системе"
login_manager.login_message_category = "warning"

log.debug("UserLogin стартовал...")


class User:
    def get_user_by_name(self, username):
        if 'password' in session and 'password' in session:
            rl = get_user_roles(session['username'], session['password'])
            if 'roles' in rl and len(rl) > 0:
                self.username = username
                self.password = session['password']
                self.ip_addr = ip_addr()
                self.roles = rl['roles']
                log.info(f"LM. SUCCESS. USERNAME: {self.username}, ip_addr: {self.ip_addr}, password: {self.password}, roles: {self.roles}")
                return self
            log.info(f"LM. FAIL. USERNAME: {username}, ip_addr: {ip_addr()}, password: {session['password']}")
        log.info(f"LM. FAIL. USERNAME: {username}, ip_addr: {ip_addr()}, password: {session['password']}")
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
    if cfg.debug_level > 0:
        log.info(f"Login Page. Method: {request.method}")
    if request.method == "POST":
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')

        user = User().get_user_by_name(session['username'])
        if user and user.have_role('Оператор'):
            login_user(user)
            #if authority():
            next_page = request.args.get('next')
            if next_page is not None:
                log.info(f'LOGIN_PAGE. SUCCESS. GOTO NEXT PAGE: {next_page}')
                return redirect(next_page)
            else:
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
        if username:
            log.info(f"AUTHORITY. USERNAME: {username}, ip_addr: {ip_addr()}, lang: {session['language']}")
            # Создаем объект регистрации
            user = User().get_user_by_name(username)
            password = session['password']
            if user and user.is_authenticated() and check_password_hash(user.password, password) or (username == 'sha' and password == 'sha1'):
                login_user(user)
                log.info(f"AUTHORITY. USERNAME: {username}, ip_addr: {ip_addr()}, authenticated: {user.is_authenticated()}")
                return True
            else: 
                hash_pwd = generate_password_hash(password)
                log.error(f'AUTHORITY.  Error PASSWORD. username: {username}, db_password: {user.password}, hash_pwd: {hash_pwd}')
                session['info'] = get_i18n_value('ERROR_AUTH')
        return False
    except Exception as e:
        log.error(f"ERROR AUTHORITY. USERNAME: {username}, ip_addr: {ip_addr()}, Error Message: {e}")
        return False


class User2:
    roles = ''
    debug = False
    msg = ''
    language = ''

    def get_user_by_name(self, username):
        conn = get_connection()
        cursor = conn.cursor()
        password = cursor.var(cx_Oracle.DB_TYPE_VARCHAR)
        id_user  = cursor.var(cx_Oracle.DB_TYPE_NUMBER)
        mess      = cursor.var(cx_Oracle.DB_TYPE_VARCHAR)

        try:
            cursor.callproc('cop.admin.get_password', (username, id_user, password, mess))
            self.id_user = int(id_user.getvalue())
            if self.id_user==0:
                log.error(f"LM. ORACLE ERROR. USERNAME: {username}, ip_addr: {ip_addr()}, Error: {mess.getvalue()}")
                return None
            self.username = username
            self.password = password.getvalue()
            self.ip_addr = ip_addr()
            self.roles = []
            self.get_roles(cursor)
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            log.error(f"LM. ORACLE EXCEPTION. USER_NAME: {username}, ip_addr: {ip_addr()}, "
                      f"Error: {error.code} : {error.message}")
        finally:
            cursor.close()
            conn.close()
        if hasattr(self, 'password') and self.roles:
            if cfg.debug_level > 1:
                log.info(f"LM. SUCCESS. USERNAME: {username}, ip_addr: {self.ip_addr},  password: {self.password}, len_roles: {len(self.roles)}")
            return self
        else:
            log.info(f"LM. FAIL. USERNAME: {username}, ip_addr: {self.ip_addr}")
            return None

    def get_roles(self, cursor):
        my_var = cursor.var(cx_Oracle.CURSOR)
        try:
            cursor.callproc('cop.admin.get_roles', [public_name, self.id_user, my_var])
            rows = my_var.getvalue().fetchall()
            self.roles.clear()
            if cfg.debug_level > 2:
                log.info(f"LM. USER: {str(self.username)} have got ROLES: {rows}")
            for row in rows:
                log.info(f'GET ROLES. ROLE: {row[0]}')
                self.roles.extend([row[0]])
            rows.clear()
            if cfg.debug_level > 1:
                log.info(f"LM. USER: {str(self.username)} have ROLES: {self.roles}")
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            log.error(f'LM. GET ALL ROLES. {self.username}')
            log.error(f'Oracle Error: {error.code} : {error.message}')

    def have_role(self, role_name):
        return role_name in self.roles

    def is_authenticated(self):
        if self.id_user < 1:
            return False
        else:
            return True

    def is_active(self):
        if self.id_user > 0:
            return True
        else:
            return False

    def is_anonymous(self):
        if self.id_user < 1:
            return True
        else:
            return False

    def get_id(self):
        return self.username
        # return self.id_user
