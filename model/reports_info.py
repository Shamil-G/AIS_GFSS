from util.logger import log
from app_config import debug_level
from flask import session,redirect, url_for
from model.list_reports import dict_reports


def get_owner_reports():
    list_owner = []
    for i in  dict_reports:
        it = { "dep_name": i }
        list_owner.append(it)
    if debug_level > 3:
        log.info(f'LIST: {list_owner}')
    return list_owner

def get_list_groups():
    if 'dep_name' in session:
        dep_name = session['dep_name']
        dep_reps = dict_reports.get(dep_name)
        if dep_reps:
            list_grp = []
            for grp in dep_reps:
                list_grp.append({"grp": grp})
            if debug_level > 3:
                log.info(f'List groups: {list_grp}')
            return list_grp
    return redirect(url_for('view_root'))


def get_list_reports():
    names_reps = []
    dep_name = session['dep_name']
    grp_name = session['grp_name']
    if debug_level > 3:
        log.info(f'{dep_name}: {grp_name}')
    if dep_name and grp_name:
        dep_grps = dict_reports.get(dep_name)
        reps_grp = dep_grps.get(str(grp_name))
        # Определим реальное количество отчетов, без вспомогательных атрибутов
        real_len = len(reps_grp) - 2
        for num in range(1, real_len+1):
            num_rep = str(num).zfill(2)
            rep = reps_grp.get(num_rep)
            rep_name = rep.get('name')
            params = rep.get('params')
            names_reps.append({"num": num_rep, "name": rep_name, "params": params})
        if debug_level > 3:
            log.info(f'\nList reps: {names_reps}')
    return names_reps