from app_config import debug_level
from main_app import log
from db.connect import plsql_proc_s, get_connection, plsql_proc, select_one
import cx_Oracle
import os

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
    with get_connection().cursor() as cursor:
        myCursor = cursor.var(cx_Oracle.CURSOR)
        if debug_level > 2:
            log.info(f'LIST REPORTS BY DAY. request_day: {request_day}')
        plsql_proc(cursor, 'LIST REPORTS BY DAY', 'reports.reps.list_reports', [request_day, myCursor])
        val_cursor = myCursor.getvalue() 
        if val_cursor:
            rows = val_cursor.fetchall()
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
                    if debug_level > 2:
                        log.info(f'LIST REPORTS BY DAY. DAY:{request_day}, INFO: {info}')
                    results.append(info)
            rows.clear()
    return results
