from app_config import debug_level, REPORT_PATH
from main_app import app, log
from flask import  session, flash, request, render_template, redirect, url_for, send_from_directory
from flask_login import  login_required
from model.reports_info import get_owner_reports, get_list_groups, get_list_reports
from model.call_report import call_report
import os
from model.manage_user import change_passwd
from model.reports import list_reports_by_day, remove_report
from datetime import date
from util.get_i18n import get_i18n_value
from model.call_report import check_report

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
            if len(params)>0:
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
def view_running_reports():
    if '_flashes' in session:
        session['_flashes'].clear()
    request_date = date.today().strftime('%Y-%m-%d')
    if request.method == "POST":
        request_date = request.form['request_date']
    if debug_level > 2:
        log.info(f'RUNNING REPORTS. REQUEST DATE: {request_date}')
    list_reports = list_reports_by_day(request_date)
    if debug_level > 2:
        log.info(f'RUNNING REPORTS. LIST REPORTS: {list_reports}')
    return render_template("running_reports.html", list = list_reports)


@app.route('/uploads/<path:full_path>')
def uploaded_file(full_path):
    path, file_name = os.path.split(full_path)
    status = check_report(f'{REPORT_PATH}/{file_name}')
    if debug_level > 2:
        log.info(f"UPLOADED_FILE. STATUS: {status} : {type(status)}, PATH: {path}, file_name: {file_name}, REPORT_PATH: {REPORT_PATH}")
    if status == 2:
        log.info(f"UPLOADED_FILE. PATH: {path}, FILE_NAME: {file_name}")
        return send_from_directory(REPORT_PATH, file_name)
    return redirect(url_for('view_running_reports'))


@app.route('/remove-reports/<string:date_report>/<int:num_report>')
def view_remove_report(date_report,num_report):
    if debug_level > 2:
        log.info(f'REMOVE REPORT. DATE_REPORT: {date_report}, NUM_REPORT: {num_report}')
    remove_report(date_report, num_report)
    return redirect(url_for('view_running_reports'))
