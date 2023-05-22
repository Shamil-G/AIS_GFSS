from typing import List, Any
from flask import render_template, request, redirect, flash, url_for, g, session
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from util.utils import *
import cx_Oracle
from werkzeug.security import check_password_hash, generate_password_hash
from db.connect import get_connection, ip_addr
from main_app import app, log
import app_config as cfg


login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

log.debug("UserLogin стартовал...")


class User:
    roles = ''
    debug = False
    msg = ''
    iin = ''
    language = ''

    def get_user_by_num_order(self, username, lang):
        conn = get_connection()
        cursor = conn.cursor()
        password = cursor.var(cx_Oracle.DB_TYPE_VARCHAR)
        msg = cursor.var(cx_Oracle.DB_TYPE_VARCHAR)
        try:
            cursor.callproc('pdd.admin.login', (username, password, msg))
            self.msg = msg.getvalue()
            if self.msg:
                log.error(f"LM. ORACLE ERROR. NUM_ORDER: {username}, ip_addr: {ip_addr()}, "
                            f"lang: {lang}, Error: {self.msg}")
                print(f"--------------> msg: {msg}")
                return None
            self.username = username
            self.password = password.getValue()
            self.ip_addr = ip_addr()
            self.roles = []
            self.get_roles(cursor)
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            log.error(f"LM. ORACLE EXCEPTION. USER_NAME: {username}, ip_addr: {ip_addr()}, "
                        f"lang: {lang}, Error: {error.code} : {error.message}")
        finally:
            cursor.close()
            conn.close()
        if self.passsword is None:
            log.info(f"LM. FAIL. USERNAME: {username}, ip_addr: {self.ip_addr},  password: {password.getValue()}")
            return None
        else:
            if cfg.debug_level > 3:
                log.info(f"LM. SUCCESS. USERNAME: {username}, ip_addr: {self.ip_addr},  password: {password.getValue()}")
            return self

    def get_roles(self, cursor):
        my_var = cursor.var(cx_Oracle.CURSOR)
        if cfg.debug_level > 3:
            print("LM. Get Roles for: " + str(self.username) + ', id_user: ' + str(self.id_user))
        try:
            cursor.callproc('cop.cop.get_roles', [self.id_user, my_var])
            rows = my_var.getvalue().fetchall()
            self.roles.clear()
            for row in rows:
                # print(f'GET Role: {row[0]}')
                self.roles.extend([row[0]])
            rows.clear()
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            log.error(f'LM. GET ALL ROLES. {self.username}')
            log.error(f'Oracle Error: {error.code} : {error.message}')

    def have_role(self, role_name):
        return role_name in self.roles

    def is_authenticated(self):
        if self.id_order < 1:
            return False
        else:
            return True

    def is_active(self):
        if self.id_order > 0:
            return True
        else:
            return False

    def is_anonymous(self):
        if self.id_order < 1:
            return True
        else:
            return False

    def get_id(self):
        return self.num_order


@login_manager.user_loader
def loader_user(num_order):
    if cfg.debug_level > 3:
        log.debug(f"LM. Loader User: {num_order}")
    return User().get_user_by_num_order(num_order, session['language'])


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    log.info(f"LM. LOGOUT. NUM_ORDER: {User().num_order}, IIN: {User().iin}, ip_addr: {User().ip_addr}")
    logout_user()
    return redirect(url_for('view_index'))


@app.after_request
def redirect_to_signing(response):
    if response.status_code == 401:
        return redirect(url_for('view_index') + '?next=' + request.url)
    return response
    

@app.before_request
def before_request():
    g.user = current_user


# @app.context_processor
# def get_current_user():
    # if g.user.id_user:
    # if g.user.is_anonymous:
    #     log.debug('Anonymous current_user!')
    # if g.user.is_authenticated:
    #     log.debug('Authenticated current_user: '+str(g.user.username))
    # return{"current_user": 'admin_user'}


def authority():
    if 'order_num' in session:
        order_num = session['order_num']
    else:
        log.info(f"AUTHORITY. Absent ORDER_NUM. ip_addr: {ip_addr()}")
        session['info'] = 'ORDER_NUM_ABSENT'
        return redirect(url_for('view_index'))
    try:
        if order_num:
            log.info(f"AUTHORITY. ORDER_NUM: {order_num}, ip_addr: {ip_addr()}, lang: {session['language']}")
            # Создаем объект регистрации
            user = User().get_user_by_num_order(order_num, session['language'])
            if user.is_authenticated():
                login_user(user)
                if type(user.remain_time) is int and user.remain_time > 0:
                    log.info(f"AUTHORITY. Идем на тестирование. {user.num_order}, "
                             f"IIN: {user.iin}, ip_addr: {user.ip_addr}, remain_time: {user.remain_time}")
                    return 1
                if type(user.remain_time) is int and user.remain_time <= 0:
                    log.info(f"AUTHORITY. remain time = 0. {user.num_order}, "
                             f"IIN: {user.iin}, ip_addr: {user.ip_addr}")
                    session['info'] = get_i18n_value('TEST_COMPLETED')
        return 0
    except Exception as e:
        error, = e.args
        log.error(f"ERROR AUTHORITY. ORDER_NUM: {order_num}, IIN: {session['iin']}, ip_addr: {ip_addr()}, "
                  f"Error Code: {error.code}, Error Message: {error.message}")
        return 0


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if cfg.debug_level > 0:
        log.info("Login Page")
    if request.method == "POST":
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')
        if authority():
            log.info("Login Page. AUTHORITY SUCCESS")
            next_page = request.args.get('next')
            if next_page is not None:
                return redirect(next_page)
            else:
                return redirect(url_for('view_models'))
        else:
            flash("Имя пользователя или пароль неверны")
            return redirect(url_for('login_page'))
    flash('Введите имя и пароль')
    return render_template('login.html')
