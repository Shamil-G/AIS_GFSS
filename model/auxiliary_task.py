from util.logger import log
from model.xls_loader import load_excel

def load_minso_dia(file_name:str ):
    table_name = "CTRL_MINSO"
    columns = ["BIN", "CTRL_DATE"]
    log.info(f"LOAD_MINSO. FILE: {file_name}, columns: {columns}, table: {table_name}")
    st = load_excel(f"c:\loads\{file_name}", table_name, columns)
    return st