from app_config import debug_level
from main_app import app, log, cfg
from flask import  session, flash, request, render_template, redirect, url_for, send_from_directory
from flask_login import LoginManager, login_required, current_user
from util.utils import get_i18n_value
from model.reports_info import get_owner_reports, get_list_groups, get_list_reports
from model.call_report import call_report
import os
from model.manage_user import change_passwd

#from model.call_report import call_report, call_report

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
    # log.info("Static folder: " + app.static_folder)
    owners = get_owner_reports()
    if debug_level > 1 and 'username' in session:
        log.info(f"VIEW_ROOT. USERNAME: {session['username']}")
    #if not g or 'user' not in g or g.user.is_anonymous():
    #    log.info(f"VIEW MODELS. NOT LOGIN")
    #    return redirect(url_for('login_page'))
    #log.info(f"VIEW MODELS. USER: {g.user.username}")
    #cursor = models_list()
    return render_template("index.html", owner_cursor=owners)


@app.route('/dep/<string:dep_name>', methods=['GET','POST'])
@login_required
def view_set_dep(dep_name):
    log.info(f'SET_DEP: {dep_name}')
    #if request.method == 'POST':
    session['dep_name'] = dep_name
    if debug_level > 3:
        log.info(f"DEP_NAME: {session['dep_name']}")
    cursor = get_list_groups()
    print(cursor)
    return render_template("list_grps.html", cursor=cursor)
        #log.info(f'VIEW GET REPORTS. POST. DATA: {data}')
        #dep = data['dep']
        #group = data['group']
        #code = data['code']
        #params = data['params']
        #if dep and group and code:
        #    log.info(f'VIEW GET REPORTS. CALL REPORT. PARAMS: {params}')
        #    try:
        #        result = call_report(dep, group, code, params)
        #        return result, 200, {'Content-Type': 'text/html;charset=utf-8'}
        #    except TypeError:
        #        return {"status": -100, "file_path": "TypeError in params"}, 200, {'Content-Type': 'text/html;charset=utf-8'}
    #return empty_call_response, 200, {'Content-Type': 'text/html;charset=utf-8'}


@app.route('/list-reports/<int:grp>', methods=['POST', 'GET'])
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
                        #Если отчет готов, то выслать его получателю
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
