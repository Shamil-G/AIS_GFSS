# from concurrent.futures.thread import BrokenThreadPool
# from gc import enable
from socket import close
import db_config as cfg
from reports_gfss_parameter import LD_LIBRARY_PATH
from util.logger import log
from util.ip_addr import ip_addr 
import oracledb


def init_session(connection, requestedTag_ignored):
    cursor = connection.cursor()
    cursor.execute("ALTER SESSION SET NLS_TERRITORY = 'CIS'")
    cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'DD.MM.YYYY HH24:MI'")
    log.info("--------------> Executed: ALTER SESSION SET NLS_TERRITORY = 'CIS'")
    cursor.close()


# Для работы "толстого клиента", сначала выполняется init_oracle_client
# Для работы с версией БД ЦРТР требуется толстый клиент
oracledb.init_oracle_client(lib_dir=LD_LIBRARY_PATH)

_pool = oracledb.create_pool(user=cfg.username, 
                             password=cfg.password, 
                             dsn=cfg.dsn,
                             timeout=cfg.timeout, 
                             wait_timeout=cfg.wait_timeout,
                             max_lifetime_session=cfg.max_lifetime_session,
                             min=cfg.pool_min, max=cfg.pool_max, 
                             increment=cfg.pool_inc,
                             expire_time=cfg.expire_time,
                             tcp_connect_timeout=cfg.tcp_connect_timeout,
                             session_callback=init_session)

log.info(f'Пул соединенй БД Oracle создан. Timeout: {_pool.timeout}, wait_timeout: {_pool.wait_timeout}, '
            f'max_lifetime_session: {_pool.max_lifetime_session}, min: {cfg.pool_min}, max: {cfg.pool_max}')


def get_connection():
    global _pool
    return _pool.acquire()


def close_connection(connection):
    global _pool

    if cfg.Debug > 2:
        log.debug("Освобождаем соединение...")
    _pool.release(connection)


def select(stmt):
    results = []
    mistake = 0
    err_mess = ''
    with get_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(stmt)
                recs = cursor.fetchall()
                for rec in recs:
                    results.append(rec)
            except oracledb.DatabaseError as e:
                error, = e.args
                mistake = 1
                err_mess = f"Oracle error: {error.code} : {error.message}"
                log.error(f"ERROR with ------select------>\nmess: {err_mess}")
            finally:
                return mistake, results, err_mess


def select_one(stmt, args):
    mistake = 0
    err_mess = ''
    with get_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(stmt, args)
                rec = cursor.fetchone()
            except oracledb.DatabaseError as e:
                error, = e.args
                mistake = 1
                rec = ''
                err_mess = f"Oracle error: {error.code} : {error.message}"
                log.error(f"ERROR ------select------>\n{stmt}\nARGS: {args}\n{err_mess}")
            finally:
                return mistake, rec, err_mess


def plsql_execute(cursor, f_name, cmd, args):
    try:
        cursor.execute(cmd, args)
    except oracledb.DatabaseError as e:
        error, = e.args
        log.error(f"ERROR ------execute------> FNAME:{f_name}\nIP_Addr: {ip_addr()}, args: {args}\nerror: {error.code} : {error.message}")


def plsql_proc(cursor, f_name, proc_name, args):
    try:
        cursor.callproc(proc_name, args)
    except oracledb.DatabaseError as e:
        error, = e.args
        log.error(f"ERROR -----plsql-proc-----> FNAME: {f_name}\nARGS: {args}\nerror: {error.code} : {error.message}")


def plsql_proc_s(f_name, proc_name, args):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            plsql_proc(cursor, f_name, proc_name, args)


def plsql_func(cursor, f_name, func_name, args):
    ret = ''
    try:
        ret = cursor.callfunc(func_name, args)
    except oracledb.DatabaseError as e:
        error, = e.args
        log.error(f"ERROR -----plsql-func-----> FNAME: {f_name}\nargs: {args}\nerror: {error.code} : {error.message}")
    finally:
        return ret


def plsql_func_s(f_name, proc_name, args):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            return plsql_func(cursor, f_name, proc_name, args)


if __name__ == "__main__":
    log.debug("Тестируем CONNECT блок!")
    con = get_connection()
    log.debug("Версия: " + con.version)
    val = "Hello from main"
    con.close()
    _pool.close()