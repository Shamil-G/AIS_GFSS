from app_config import debug_level
from main_app import log
from db.connect import plsql_proc_s, get_connection, plsql_proc, select_one
#import cx_Oracle
import oracledb
import os


stmt_list_reports = """
    select  to_char(st.date_execute,'YYYY-MM-DD'), st.num, st.date_first, st.date_second, st.rfpm_id, 
            st.rfbn_id, st.name, st.live_time, st.status, st.file_path,
            case when st.status = 2 then
                    date_execute + 
                    (case when live_time>0 then live_time/24 else 1 end) -
                    (case when live_time>0 then sysdate else date_execute end) 
                when trunc(st.date_execute) != trunc(sysdate) and st.status = 1 then
                     0
                else live_time 
            end           
    from load_report_status st
    where trunc(st.date_execute,'DD') = to_date(:i_date,'YYYY-MM-DD')
"""

stmt_file_path = f"""
    select st.file_path
    from LOAD_REPORT_STATUS st 
    where to_char(st.date_execute, 'YYYY-MM-DD') = :i_date_report
    and   st.num = :i_num
"""


def remove_file(date_report: str, num_report: int):
    mistake, result, err_msg = select_one(stmt_file_path, [date_report, num_report])
    log.info(f"CHECK_REPORT. MISTAKE: {mistake},  err_msg: {err_msg}, result: {result}")
    if mistake == 0:
        if result:
            file_path = result[0]
            if os.path.exists(file_path):
                os.remove(file_path)
                if debug_level > 2:
                    log.info(f"CHECK_REPORT. REMOVE_FILE. date_report: {date_report}, num_report: {num_report}, file_path: {file_path}")
                return True
    return False


def remove_report(date_report: str, num_report: int):
    if remove_file(date_report, num_report):
        plsql_proc_s('REMOVE BY FILE NAME', 'reports.reps.remove_report', [date_report, num_report])
    if debug_level > 2:
        log.info(f'REMOVE BY FILE NAME')


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
                    remain_time = row[10]
                    file_exist = os.path.exists(row[9])
                    status = int(row[8])
                    if remain_time <= 0:
                        log.info(f"CHECK_REPORT. REMOVE. REMAIN TIME: {remain_time} <= 0, date_report: {request_day}, inum_report: {row[1]}")
                        remove_report(row[0], row[1])
                    elif not file_exist and status == 2:
                        remove_report(row[0], row[1])
                        log.info(f"CHECK_REPORT. REMOVE. FILE NOT EXISTS. date_report: {request_day}, num_report: {row[1]}, file: {row[9]}")
                    else:
                        info = { "date_event": row[0], "num": row[1], "date_first": row[2], "date_second": row[3], 
                                 "rfpm_id": row[4], "rfbn_id": row[5], 
                                 "name": row[6], "live_time": row[7], "status": int(row[8]), "path": row[9]}
                        results.append(info)
                        if debug_level > 2:
                            log.info(f"LIST REPORTS BY DAY. status: {info['status']}, exist: {file_exist}, path: {info['path']}")
                rows.clear()
    return results
