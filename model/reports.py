from app_config import debug_level
from main_app import log
from db.connect import plsql_proc_s, get_connection, plsql_proc, select_one
from datetime import datetime
import oracledb
import os
from util.trunc_date import first_day, last_day


stmt_list_reports_month = """
    select  to_char(st.date_execute,'YYYY-MM-DD'), st.num, st.date_first, st.date_second, st.rfpm_id, 
            st.rfbn_id, st.name, st.live_time, st.status, st.file_path,
            case 
                when live_time = 0 then 72
                when st.status = 2 then
                    date_execute + 
                    (case when live_time>0 then live_time/24 else 1 end) -
                    (case when live_time>0 then sysdate else date_execute end) 
                when trunc(st.date_execute) != trunc(sysdate) and st.status = 1 then
                     0
                else live_time 
            end           
    from load_report_status st
    where trunc(st.date_execute,'MM') = trunc(to_date(:i_date,'YYYY-MM-DD'), 'MM')
    order by st.num
"""

stmt_list_reports = """
    select  to_char(st.date_execute,'YYYY-MM-DD'), st.num, st.date_first, st.date_second, st.rfpm_id, 
            st.rfbn_id, st.name, st.live_time, st.status, st.file_path,
            case 
                when live_time = 0 then 72
                when st.status = 2 then
                    date_execute + 
                    (case when live_time>0 then live_time/24 else 1 end) -
                    (case when live_time>0 then sysdate else date_execute end) 
                when trunc(st.date_execute) != trunc(sysdate) and st.status = 1 then
                     0
                else live_time 
            end           
    from load_report_status st
    where trunc(st.date_execute,'DD') = to_date(:i_date,'YYYY-MM-DD')
    order by st.num
"""

stmt_file_path = f"""
    select st.file_path
    from LOAD_REPORT_STATUS st 
    where to_char(st.date_execute, 'YYYY-MM-DD') = :i_date_report
    and   st.num = :i_num
"""


def remove_file(date_report: str, num_report: int):
    mistake, result, err_msg = select_one(stmt_file_path, [date_report, num_report])
    if mistake == 0 and result:
        file_path = result[0]
        if os.path.exists(file_path):
            log.info(f"REMOVE_FILE. NUM_REPORT: {num_report}, DATE_REPORT: {date_report}, FILE_PATH: {file_path}")
            os.remove(file_path)
        else:
            log.info(f"REMOVE_FILE. FILE NOT EXISTS: NUM_REPORT: {num_report}, DATE_REPORT: {date_report}, FILE_PATH: {file_path}")
        return True
    log.info(f"REMOVE_FILE. MISTAKE: {mistake},  err_msg: {err_msg}, result: {result}")
    return False


def remove_report(date_report: str, num_report: int):
    if remove_file(date_report, num_report):
        log.info(f'REMOVE REPORT. NUM_REPORT: {num_report}, DATE_REPORT: {date_report}')
        plsql_proc_s('REMOVE REPORT. FILE NAME', 'reps.remove_report', [date_report, num_report])


def list_reports_by_day(request_day):
    current_day = datetime.today().strftime('%Y-%m-%d')
    results = []
    stmt = ''
    if debug_level > 2:
        log.info(f'LIST REPORTS BY DAY. request_day: {request_day}, current_day: {current_day}')
    with get_connection() as connection:
        with connection.cursor() as cursor:
            if debug_level > 1:
                log.info(f'LIST REPORTS BY DAY. CURSOR CREATED')
            if first_day(request_day) == request_day or last_day(request_day) == request_day:
                stmt = stmt_list_reports_month
            else:
                stmt = stmt_list_reports
            cursor.execute(stmt, i_date=request_day)
            if debug_level > 2:
                log.info(f'LIST REPORTS BY DAY. request_day: {request_day}\n--------\n{stmt}\n--------')
            rows = cursor.fetchall() 
            if rows:
                for row in rows:
                    remain_time = row[10]
                    date_execute = row[0]
                    file_exist = os.path.exists(row[9])
                    status = int(row[8])
                    if remain_time <= 0:
                        log.info(f"CHECK_REPORT. REMOVE. REMAIN TIME: {remain_time} <= 0, date_report: {request_day}, inum_report: {row[1]}")
                        remove_report(row[0], row[1])
                    elif not file_exist and status == 2:
                        log.info(f"CHECK_REPORT. REMOVE. FILE NOT EXISTS. num_report: {row[1]}, file: {row[9]}")
                        remove_report(row[0], row[1])
                    elif status == 1 and current_day != date_execute:
                        log.info(f"CHECK_REPORT. REMOVE. STATUS: {status}, date_execute: {date_execute}, current_day: {current_day}, file: {row[9]}")
                        remove_report(row[0], row[1])
                    else:
                        info = { "date_event": row[0], "num": row[1], "date_first": row[2], "date_second": row[3], 
                                 "rfpm_id": row[4], "rfbn_id": row[5], 
                                 "name": row[6], "live_time": row[7], "status": int(row[8]), "path": row[9]}
                        results.append(info)
                        if debug_level > 2:
                            log.info(f"LIST REPORTS BY DAY. status: {info['status']}, exist: {file_exist}, path: {info['path']}")
                rows.clear()
    return results
