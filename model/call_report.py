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
create index XN_LOAD_REPORT_STATUS_DATE_EXECUTE on LOAD_REPORT_STATUS (DATE_EXECUTE)
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
      select st.date_execute, st.num, st.status, 
            case when st.status = 2 then
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
    log.info(f"CHECK_REPORT. MISTAKE: {mistake},  err_msg: {err_msg}, file_path: {file_path}")
    if mistake == 0:
        if result:
            date_report = result[0]
            num_report = result[1]
            status = result[2]
            remain_time = result[3]
            log.info(f"CHECK_REPORT. RESULT: {result}, status: {status}, idate_report: {date_report}, inum_report: {num_report}")
            if remain_time <= 0:
                log.info(f"CHECK_REPORT. REMAIN TIME: {remain_time}, idate_report: {date_report}, inum_report: {num_report}")
                remove_report(date_report, num_report)
                if os.path.exists(file_path):
                    os.remove(file_path)
                status = 0
            return status
        return 10
    return -100


def init_report(name_report: str, date_first: str, date_second: str, rfpm_id: str, rfbn_id: str, live_time: str, file_path: str):
    plsql_proc_s('INIT REPORT', 'reports.reps.add_report', [name_report, date_first, date_second, rfpm_id, rfbn_id, live_time, file_path])
    # 0 - файл отсутствует
    # 1 - Файл готовится
    # 2 - Файл готов
    # 10 - Журнал не содержит информаци об отчете


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



def call_report(dep: str, group: str, code: str, params: dict):
    if debug_level > 3:
        log.info(f'--- CALL REPORT. DEP: {dep}, group: {group}, code: {code}, params: {params}')
    #Определим владельца отчета-департамент
    if dep in dict_reports:
        dp = dict_reports[dep]
        if debug_level > 3:
            log.info(f'--- CALL REPORT. DP: {dp}')
        #Определим группу отчетов
        if group in dp:
            grp = dp[group]
            if debug_level > 3:
                log.info(f'--- CALL REPORT. GRP: {grp}')
            #Определяем код отчета в группе
            if code in grp:
                cd = grp[code]
                if debug_level > 2:
                    log.info(f'--- CALL REPORT. DEP: {dep}, group: {group}, code: {code}, params: {params}')
                #Определим по коду отчета имя Python модуля для последующей загрузке
                if 'proc' in cd:
                    proc = cd['proc']
                    #Определим время жизни отчета
                    live_time = 0
                    if 'live_time' in grp:
                        live_time = grp['live_time']
                    init_report_path = f'{REPORT_PATH}/{dep}.{group}'
                    # Дополним параметром начального пути для отчета
                    params['file_name']=init_report_path
                    log.info(f'CALL_REPORT. PARAMS: {params}')

                    #Определим путь для импорта необходимого Python модуля-отчета
                    module_dir = grp['module_dir']
                    module_path = f"{module_dir}.{proc}"
                    #loaded_module = __import__(module_path, globals(), locals(), ['make_report'], 0)
                    loaded_module = importlib.import_module(module_path)
                    # Получаем полный путь к файлу - результату
                    file_name = loaded_module.get_file_path(**params)

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
                        date_first = ''
                        date_second = ''
                        rfpm_id = ''
                        rfbn_id = ''
                        if 'date_first' in params:
                            date_first = params['date_first']
                        if 'date_second' in params:
                            date_second = params['date_second']
                        if 'srfpm_id' in params:
                            rfpm_id = params['srfpm_id']
                        if 'srfbn_id' in params:
                            rfbn_id = params['srfbn_id']

                        init_report(f'{group}.{code}', date_first, date_second, rfpm_id, rfbn_id, live_time, file_name)

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

