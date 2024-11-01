from flask import  session, flash, request, render_template, redirect, url_for, send_from_directory, g
from flask_login import  login_required
from werkzeug.utils import secure_filename
import os

from reports_gfss_parameter import platform
from app_config import REPORT_PATH, debug_level, LOG_PATH
from main_app import app, log
from model.reports_info import get_owner_reports, get_list_groups, get_list_reports
from model.auxiliary_task import load_minso_dia
from model.call_report import call_report, check_report
from model.manage_user import change_passwd
from model.reports import list_reports_by_day
from model.manage_reports import remove_report
from datetime import date
from util.get_i18n import get_i18n_value


list_params = []

empty_response_save = """
<h2>Hello World</h2>
<p>Maybe Must be used POST method with JSON data</p>
"""

empty_call_response = """
<h2>Hello World</h2>
<p>Maybe Must be used POST method with JSON data: DEP, GROUP and CODE parameter</p>
"""

#@app.route('/', methods=['POST', 'GET'])
#def view_index():
#    return empty_response_save, 200, {'Content-Type': 'text/html;charset=utf-8'}


@app.context_processor
def utility_processor():
    log.info(f"CP. {get_i18n_value('APP_NAME')}")
    return dict(res_value=get_i18n_value)


@app.route('/')
@app.route('/home', methods=['POST', 'GET'])
@login_required
def view_root():
    owners = get_owner_reports()
    if debug_level > 1 and 'username' in session:
        log.info(f"VIEW_ROOT. USERNAME: {session['username']}")
    return render_template("index.html", owner_cursor=owners)


@app.route('/dep/<string:dep_name>', methods=['GET','POST'])
@login_required
def view_set_dep(dep_name):
    log.info(f'SET_DEP: {dep_name}')
    #if request.method == 'POST':
    session['dep_name'] = dep_name
    list_groups = get_list_groups()
    if debug_level > 2:
        log.info(f"DEP_NAME: {session['dep_name']}, LIST_GROUPS: {list_groups}")
    return render_template("list_grps.html", cursor=list_groups)


@app.route('/list-reports/<grp>', methods=['POST', 'GET'])
@login_required
def view_set_grp_name(grp):
    session['grp_name'] = str(grp)
    if request.method == 'GET':
        if debug_level > 2:
            log.info(f'SET GRP NAME. GRP: {grp}')
        return render_template("list_reports.html", cursor=get_list_reports())


@app.route('/extract-params/<int:rep_number>', methods=['GET', 'POST'])
@login_required
def view_extract_params(rep_number):
    rep_num = str(rep_number).zfill(2)
    session['rep_code'] = rep_num
    for rep in get_list_reports():
        if rep_num == rep.get('num'):
            params = rep.get('params')
            session['rep_name'] = rep['name']
            if params and len(params)>0:
                session['params'] = params
                return redirect(url_for('view_set_params'))
            if params and len(params)>0:
                session['params'] = params
                return redirect(url_for('view_set_params'))
    return redirect(url_for('view_root'))


@app.route('/set-params', methods=['GET', 'POST'])
@login_required
def view_set_params():
    new_params = {}
    if 'params' not in session:
        log.info(f"EDIT_PARAMS. PARAMS not FOUND")
        return redirect(url_for('view_root'))

    list_params = session['params']
    if request.method == 'POST':
        log.info(f'SET_PARAMS. LIST_PARAMS: {list_params}')
        #Вытащим значения параметров из формы в новый список
        for parm in list_params:
            p = request.form[parm]
            new_params[parm] = p
        if debug_level > 3:
            log.info(f"EDIT_PARAMS. REP_CODE: {rep_code}, new_params: {new_params}")
        #Если параметры вытащили, то вызовем отчет
        if new_params:
            rep_code = session['rep_code']
            for rep in get_list_reports():
                if rep_code == rep.get('num'):
                    report = rep
                    report['params'] = new_params
                    result = call_report(session['dep_name'], session['grp_name'], session['rep_code'], new_params)
                    if debug_level > 3:
                        log.info(f"EDIT_PARAMS. RESULT: {result}, PARAMS: {new_params}, report: {report}")
                    if 'status' in result:
                        status = result['status']
                        # 0 - отчет начал готовится
                        # 1 - отчет уже готовится
                        # 2 - отчет уже готов
                        # Если отчет готов(status==2), то выслать его получателю
                        if status == 2:
                            if 'file_path' in result:
                                row_path = os.path.normpath(result['file_path'])
                                head_tail = os.path.split(row_path)
                                file_path = str(head_tail[0])
                                file_name = str(head_tail[1])
                                log.info(f"EDIT_PARAMS. SEND REPORT. FILE_PATH: {file_path}, FILE_NAME: {file_name}")
                                return send_from_directory(file_path, file_name)
            return redirect(url_for('view_set_grp_name', grp=session['grp_name']))
    return render_template("edit_params.html", params=list_params)


@app.route('/language/<string:lang>')
def set_language(lang):
    log.info(f"Set language. LANG: {lang}, предыдущий язык: {session['language']}")
    session['language'] = lang
    # Получим предыдущую страницу, чтобы на неё вернуться
    current_page = request.referrer
    log.info(f"Set LANGUAGE. {current_page}")
    if current_page is not None:
        return redirect(current_page)
    else:
        return redirect(url_for('view_root'))


@app.route('/change-passwd', methods=['POST', 'GET'])
def view_change_password():
    log.info(f"CHANGE PASSWORD")
    if '_flashes' in session:
        session['_flashes'].clear()
    if request.method == "POST":
        passwd_1 = request.form['password_1']
        passwd_2 = request.form['password_2']
        if passwd_1 != passwd_2:
            flash('Пароли не совпадают')
        else:
            change_passwd(session['username'], session['password'], passwd_1)
            return redirect(url_for('view_root'))
    return render_template("change_passwd.html")


@app.route('/running-reports', methods=['POST', 'GET'])
@login_required
def view_running_reports():
    if '_flashes' in session:
        session['_flashes'].clear()
    if 'request_date' not in session:
        session['request_date'] = date.today().strftime('%Y-%m-%d')
    if request.method == "POST":
        session['request_date'] = request.form['request_date']
    if debug_level > 2:
        log.info(f"RUNNING REPORTS. REQUEST DATE: {session['request_date']}")
    list_reports = list_reports_by_day(session['request_date'])
    if debug_level > 2:
        log.info(f'RUNNING REPORTS. LIST REPORTS: {list_reports}')
    return render_template("running_reports.html", list = list_reports, request_date=session['request_date'])


@app.route('/uploads/<path:full_path>')
def uploaded_file(full_path):
    if platform == 'unix' and not full_path.startswith('/'):
        full_path = f'/{full_path}'
    path, file_name = os.path.split(full_path)
    if full_path.startswith(REPORT_PATH):
        status = check_report(full_path)
        if debug_level > 2:
            log.info(f"UPLOADED_FILE. STATUS: {status} : {type(status)}, PATH: {path}, file_name: {file_name}, REPORT_PATH: {REPORT_PATH}")
        if status == 2:
            log.info(f"UPLOADED_FILE. PATH: {path}, FILE_NAME: {file_name}")
            return send_from_directory(path, file_name)
    else:
        log.info(f"UPLOADED_FILE. FULL_PATH: {full_path}\nsplit_path: {path}\nreprt_path: {REPORT_PATH}")
    return redirect(url_for('view_running_reports'))


@app.route('/remove-reports/<string:date_report>/<int:num_report>')
@login_required
def view_remove_report(date_report,num_report):
    if 'admin' in g.user.roles or 'Руководитель' in g.user.roles:
        log.info(f"REMOVE REPORT. {session['username']}. DATE_REPORT: {date_report}, NUM_REPORT: {num_report}, ROLES: {g.user.roles}")
        remove_report(date_report, num_report)
    return redirect(url_for('view_running_reports'))


@app.route('/auxiliary-task-dia')
@login_required
def view_auxiliary_task_dia():
    if 'Администратор ДИА' in g.user.roles:
        log.info(f"VIEW AUXILIARY TASK DIA. {session['username']}.")
    mess = '' 
    if 'aux_info' in session:
        mess = session['aux_info']
        session.pop('aux_info')
    return render_template("auxiliary_task_dia.html", info=mess)


@app.route('/load_minso_dia', methods=['POST', 'GET'])
@login_required
def view_load_minso_dia():
    if 'Администратор ДИА' in g.user.roles:
        if request.method == "POST":
            log.info(f'request: {request}')
            uploaded_file = request.files['file']
            if uploaded_file.filename!='':
                secure_fname = secure_filename(uploaded_file.filename)
                file_name = os.path.join(LOG_PATH,secure_fname)
                uploaded_file.save(file_name)
                count, all_cnt, table_name, mess = load_minso_dia(file_name)
                session['aux_info'] = mess
                log.info(f"VIEW_LOAD_MINSO. LOAD_FILE: {file_name}, loaded: {count}/{all_cnt} , mess: {mess}")
                if count<all_cnt:
                    log.info(f"VIEW_LOAD_MINSO. DOWNLOAD LOG with ERROR: {LOG_PATH}/load_{secure_fname}.log")
                    return send_from_directory(LOG_PATH, f'load_{table_name}.log')                
    log.info(f"VIEW_LOAD_MINSO. info: {session['aux_info']}")
    return redirect(url_for('view_auxiliary_task_dia'))

