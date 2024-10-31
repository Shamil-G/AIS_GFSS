from util.logger import log
from model.xls_loader import load_excel

def load_minso_dia(file_name:str ):
    table_name = "CTRL_MINSO"
    columns = ["RFBN_ID","BIN", "CTRL_DATE"]
    cnt_rows, all_rows, mess = load_excel(file_name, table_name, columns)
    log.info(f"LOAD_MINSO. FILE: {file_name}, columns: {columns}, table: {table_name}, mess: {mess}")
    return cnt_rows, all_rows, table_name, mess