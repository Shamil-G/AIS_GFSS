from  db.connect import select_one, plsql_proc_s, get_connection, plsql_execute, plsql_proc_s
from  main_app import log
import importlib
from   app_config import REPORT_PATH, debug_level, platform
from   model.list_reports import dict_reports
from   model.reports import remove_report
import os


stmt_table = """
CREATE TABLE LOAD_REPORT_STATUS(
  date_execute DATE,
  num          number(3),
  code         varchar2(16),
  live_time    NUMBER(6,2),
  status       VARCHAR2(8),
  file_path    VARCHAR2(512)
)
tablespace DATA
  pctfree 10
  initrans 1
  maxtrans 255
  storage
  (
    initial 64K
    next 1M
    minextents 1
    maxextents unlimited
  );
"""

stmt_index = """
create unique index XU_LOAD_REPORT_STATUS_F_NAME on LOAD_REPORT_STATUS (file_path)
  tablespace DATA
  pctfree 10
  initrans 2
  maxtrans 255
  storage
  (
    initial 64K
    next 1M
    minextents 1
    maxextents unlimited
  );
"""
stmt_index_2 = """
create unique index XN_LOAD_REPORT_STATUS_DATE_EXECUTE_NUM on LOAD_REPORT_STATUS (DATE_EXECUTE, NUM)
  tablespace DATA
  pctfree 10
  initrans 2
  maxtrans 255
  storage
  (
    initial 64K
    next 1M
    minextents 1
    maxextents unlimited
  );
"""

def check_report(file_path: str):
    stmt = f"""
      select to_char(st.date_execute,'YYYY-MM-DD'), st.num, st.status, 
            case 
                when st.live_time = 0 then 1
                when st.status = 2 then
                    date_execute + 
                    (case when st.live_time>0 then st.live_time/24 else 1 end) -
                    (case when st.live_time>0 then sysdate else st.date_execute end) 
                when trunc(st.date_execute) != trunc(sysdate) and st.status = 1 then
                     0
                else st.live_time 
            end           
      from LOAD_REPORT_STATUS st 
      where st.file_path = :file_path
    """
    mistake, result, err_msg = select_one(stmt, [file_path])
    if debug_level > 1:
        log.info(f"CHECK_REPORT. MISTAKE: {mistake},  err_msg: {err_msg}, file_path: {file_path}")
    if mistake == 0:
        if result:
            date_report = result[0]
            num_report = result[1]
            status = int(result[2])
            remain_time = result[3]
            if debug_level > 1:
                log.info(f"CHECK_REPORT. RESULT: {result}, status: {status}, idate_report: {date_report}, inum_report: {num_report}")
            if remain_time <= 0:
                log.info(f"CHECK_REPORT. REMOVE. REMAIN TIME: {remain_time}, idate_report: {date_report}, inum_report: {num_report}")
                remove_report(date_report, num_report)
                status = 0
            return status
        return 10
    return -100


def init_report(name_report: str, date_first: str, date_last: str, rfpm_id: str, rfbn_id: str, live_time: str, file_path: str):
    status = 0
    with get_connection() as conn:
        with conn.cursor() as cursor:
            status =cursor.callfunc('reps.add_report', int, [name_report, date_first, date_last, rfpm_id, rfbn_id, live_time, file_path])
    # 0 - файл отсутствует
    # 1 - Файл готовится
    # 2 - Файл готов
    # 10 - Журнал не содержит информаци об отчете
    return status


def set_status_report(file_path: str, status: int):
    stmt_upd = f"""
      begin
          update LOAD_REPORT_STATUS st
          set st.status = :status,
              st.date_execute = sysdate
          where st.file_path = '{file_path}';
          commit;
      end;
    """
    with get_connection().cursor() as cursor:
        plsql_execute(cursor, 'SET STATUS REPORT', stmt_upd, [status])



def call_report(dep_name: str, group_name: str, code: str, params: dict):
    if debug_level > 1:
        log.info(f'\nCALL REPORT. DEP: {dep_name}, group: {group_name}, code: {code}, params: {params}')
    #Определим владельца отчета-департамент
    if dep_name in dict_reports:
        dp = dict_reports[dep_name]
        if debug_level > 3:
            log.info(f'\n---> CALL REPORT. DP: {dp}')
        #Переберем все группы для выбора нужной по имени
        for cur_group in dp:
            if cur_group['grp_name'] == group_name:
                list_reports = cur_group['list']
                if debug_level > 2:
                    log.info(f'\n-----> CALL REPORT. CUR_GROUP: {cur_group}')
                    log.info(f'\n-------> CALL REPORT. LIST_REPORTS: {list_reports}')
                for curr_report in list_reports:
                    #Определяем код отчета в группе
                    if code == curr_report['num_rep']:
                        if debug_level > 2:
                            log.info(f'\n-------> CALL REPORT. CODE. DEP: {dep_name}, CODE: {code}, CUR_GROUP: {cur_group}, params: {params}')
                        #Определим по коду отчета имя Python модуля для последующей загрузке
                        if 'proc' in curr_report:
                            proc = curr_report['proc']
                            if debug_level > 2:
                                log.info(f'\n-------> CALL REPORT. PROC: {proc}')
                            #Определим время жизни отчета
                            live_time = 0
                            if 'live_time' in cur_group:
                                live_time = cur_group['live_time']
                            #  Параметры дат отчетов надо заложить в имя файла
                            date_first = ''
                            date_last = ''
                            if 'date_first' in params:
                                date_first = params['date_first']
                            if 'date_last' in params:
                                date_last = params['date_last']
                            if date_first and date_last:
                                init_report_path = f'{REPORT_PATH}/{dep_name}.{group_name}.{code}.{date_first}_{date_last}.xlsx'
                            elif date_first:
                                init_report_path = f'{REPORT_PATH}/{dep_name}.{group_name}.{code}.{date_first}.xlsx'
                            else:
                                init_report_path = f'{REPORT_PATH}/{dep_name}.{group_name}.{code}.xlsx'
                            # Дополним параметром начального пути для отчета
                            params['file_name']=init_report_path
                            if debug_level > 2:
                                log.info(f'CALL_REPORT. PARAMS: {params}')
                            #Определим путь для импорта необходимого Python модуля-отчета
                            module_dir = cur_group['module_dir']
                            module_path = f"{module_dir}.{proc}"
                            if debug_level > 2:
                                log.info(f'CALL REPORT. MODULE DIR: {module_dir}, MODULE PATH: {module_path}')
                            #loaded_module = __import__(module_path, globals(), locals(), ['make_report'], 0)
                            loaded_module = importlib.import_module(module_path)
                            # Получаем полный путь к файлу - результату
                            # file_name = loaded_module.get_file_path(**params)
                            file_name = init_report_path

                            #log.info(f'CALL REPORT. GET FILE NAME. file_name: {file_name}')
                            status = int(check_report(file_name))
 
                            ##log.info(f'CALL REPORT. CHECK REPORT. status: {status}')
                            if status < 0:
                                log.info(f'CALL REPORT. Ошибка статуса. {status}. {file_name}')
                                return {"status": status}
                            # Если запись об отчете в БД присутствует
                            if status in (1, 2): # Файл готовится или готов
                                if status == 1:
                                    log.info(f'CALL REPORT. Отчет готовится. status: {status}. {file_name}')
                                if status == 2:
                                    log.info(f'CALL REPORT. Отчет готов. status: {status}. {file_name}')
                                return {"status": status, "file_path": file_name}

                            # Если запись об отчете в БД отсутствует, то ее надо сделать
                            if status in (0,10):
                                rfpm_id = ''
                                rfbn_id = ''

                                if 'srfpm_id' in params:
                                    rfpm_id = params['srfpm_id']
                                if 'srfbn_id' in params:
                                    rfbn_id = params['srfbn_id']

                                if debug_level > 2:
                                    log.info(f"\nCALL REPORT. name:\t{f'{group_name}.{code}'}\nlive_time:\t{live_time}\ndate_first:\t{date_first}\ndate_last:\t{date_last}\nrfpm_id:\t{rfpm_id}\nrfbn_id:\t{rfbn_id}")

                                status = init_report(f'{group_name}.{code}', date_first, date_last, rfpm_id, rfbn_id, live_time, file_name)
                                log.info(f'CALL REPORT. Status: {status}')
                                if status == 1:
                                    log.info(f'CALL REPORT. REPORT PREPARING. Status: {status}, file_name: {file_name}')
                                    return {"status": status, "file_path": file_name}
                                if status == 2:
                                    log.info(f'CALL REPORT. RESULT EXIST. Status: {status}, file_name: {file_name}')
                                    return {"status": status, "file_path": file_name}
                                log.info(f'MAKE_REPORT. Start DO REPORT: {file_name}')

                                params['file_name']=file_name

                                # Получаем полный путь к файлу - результату

                                if platform == 'unix':
                                    from os import fork
                                    pid = fork()
                                    if pid:
                                        return {"status": 1, "file_path": file_name}
                                    else:
                                        log.info(f'CALL REPORT. CHILD FORK PROCESS. {file_name}')
                                        loaded_module.do_report(**params)
                                else:
                                    log.info(f'CALL REPORT. THREAD PROCESS. \nBEG PARAMS ---------------------\n{params}\nEND PARAMS ---------------------')
                                    result = loaded_module.thread_report(**params)
                                    return result
    return {"status": 0, "file_path": "Mistake in parameters"}

