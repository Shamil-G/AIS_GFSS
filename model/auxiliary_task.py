from util.logger import log
from model.xls_loader import load_excel

def load_minso_dia(file_name:str ):
    table_name = "CTRL_MINSO"
    columns = ["BIN", "CTRL_DATE"]
    st, mess = load_excel(f"C:\LOADS\{file_name}", table_name, columns)
    log.info(f"LOAD_MINSO. FILE: {file_name}, columns: {columns}, table: {table_name}, mess: {mess}")
    return st, mess