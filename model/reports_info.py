from flask import session,redirect, url_for
from util.logger import log
from model.list_reports import dict_reports


def get_owner_reports():
    list_owner = []
    for i in  dict_reports:
        it = { "dep_name": i }
        list_owner.append(it)
    log.debug(f'GET OWNER REPORTS. LIST: {list_owner}')
    return list_owner

def get_list_groups():
    if 'dep_name' in session:
        dep_name = session['dep_name']
        dep_reps = dict_reports.get(dep_name)
        log.debug(f'GET LIST GROUPS. dep_reps: {dep_reps}')
        if dep_reps:
            list_grp = []
            for grp in dep_reps:
                log.debug(f'\n---> GET LIST REPORTS. grp: {grp}')
                list_grp.append(grp['grp_name'])
            log.debug(f'\n------> GET LIST REPORTS. List groups: {list_grp}')
            return list_grp
    return redirect(url_for('view_root'))


def get_list_reports():
    names_reps = []
    dep_name = session['dep_name']
    grp_name = session['grp_name']
    log.debug(f"---> GET_LIST_REPORTS. dep_name: {dep_name}, grp_name: {grp_name}")
    if dep_name and grp_name:
        dep_grps = dict_reports.get(dep_name)
        if dep_grps:
            for grp in dep_grps:
                if grp_name == grp['grp_name']:
                    log.debug(f"---> GET_LIST_REPORTS. grp: {grp}")
                    # Выберем все отчеты из списка группы отчетов
                    for rep in grp['list']:
                        log.debug(f"\n---> GET_LIST_REPORTS. REP: {rep}")
                        rep_name = rep.get('name')
                        num_rep = rep.get('num_rep')
                        params = rep.get('params')
                        names_reps.append({"num": num_rep, "name": rep_name, "params": params})
        else:
            log.info(f"\nERROR GET_LIST_REPORTS. dep_grps: {dep_grps}")
    return names_reps