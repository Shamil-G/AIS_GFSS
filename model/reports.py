from app_config import debug_level
from main_app import log
from db.connect import plsql_proc_s, get_connection, plsql_proc, select_one
#import cx_Oracle
import oracledb
import os


stmt_list_reports = """
    select st.date_execute, st.num, st.name, st.live_time, st.status, st.file_path 
    from load_report_status st
    where trunc(st.date_execute,'DD') = to_date(:i_date,'YYYY-MM-DD')
"""


def remove_by_file_name(full_file_path):
    plsql_proc_s('REMOVE BY FILE NAME', 'reports.reps.remove_report', [full_file_path])
    if debug_level > 2:
        log.info(f'REMOVE BY FILE NAME')


def get_status(full_file_path):
    stmt = f"select st.status from load_report_status st where st.file_path = '{full_file_path}'"
    log.info(f'GET STATUS. STMT: {stmt}')
    mistake, rec, err_mess = select_one(stmt, [])
    if debug_level > 2:
        log.info(f'GET STATUS. STMT: {stmt}, rec: {rec}')
    if mistake == 0: 
        return rec[0]
    else:
        log.error(f'ERROR GET STATUS. err_mess: {err_mess}')
        return -100


def list_reports_by_day(request_day):
    results = []
    if debug_level > 2:
        log.info(f'LIST REPORTS BY DAY. request_day: {request_day}')
    with get_connection() as connection:
        with connection.cursor() as cursor:
            if debug_level > 3:
                log.info(f'LIST REPORTS BY DAY. CURSOR CREATED')
            cursor.execute(stmt_list_reports, i_date=request_day)
            if debug_level > 2:
                log.info(f'LIST REPORTS BY DAY. request_day: {request_day}')
            rows = cursor.fetchall() 
            if rows:
                for row in rows:
                    info = { "num": row[1], "name": row[2], "live_time": row[3], "status": row[4], "path": row[5]}
                    exist = os.path.exists(row[5])
                    if debug_level > 2:
                        log.info(f'LIST REPORTS BY DAY. status: {row[4]}, exist: {exist}, path: {row[5]}')
                    if int(row[4]) == 2 and not exist:
                        if debug_level > 2:
                            log.info(f'LIST REPORTS BY DAY. FILE NOT EXISTS. REMOVE FROM DB: {row[5]}.')
                        remove_by_file_name(row[5])
                    else:
                        dir_path, f_name = os.path.split(row[5])
                        if debug_level > 2:
                            log.info(f'LIST REPORTS BY DAY. DAY:{request_day}, FILENAME: {f_name}')
                        results.append(f_name)
                rows.clear()
    return results
