from   app_config import os as platform
import xlsxwriter
import datetime
from   os import path
from   util.logger import log
import cx_Oracle
from   model.call_report import set_status_report

# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)
# Принят ДИА 13.02.2023

report_name = 'Количество иждивенцев и сумма 0701 за период'
report_code = 'DIA_0701_01'

#document.ridt_id: 6 - Выплаты из ГФСС, 7 - 10% удержания, 8 - удержания из соц.выплат
#document.status:  0 - Документ сформирован на выплату, 1 - Сформирован платеж, 2 - Платеж на выплате; rfds_doc_status
stmt_itogo = """
select count_dependant, 
       sum(cnt_dependant),
       sum(ucnt_pnpt_id),
       sum(sum_pay)
from (       
    select /*+ parallel(2) */ 
	       substr(pt.rfpm_id,8,1) count_dependant,
           sum(0) as cnt_dependant,
           count(unique pt.pnpt_id) ucnt_pnpt_id,
           sum(pt.sum_pay) sum_pay -- 21 665 968 909 на 13.02.2023
    from pnpt_payment pt,
         pnpd_document doc
    where pt.pnpt_id=doc.source_id
    and substr(pt.rfpm_id,1,4) = :p1
	and doc.ridt_id in (6,7,8)
	and doc.status in (0,1,2)
    and doc.pncp_date Between to_date(:dt_from,'yyyy-mm-dd') And to_date(:dt_to,'yyyy-mm-dd')
    group by substr(pt.rfpm_id,8,1)
    union 
    select /*+ parallel(4) */ 
		   substr(pt.rfpm_id,8,1) count_dependant,
           count(unique pd.sicid) cnt_dependant, 
           sum(0),
           sum(0)
    from pnpt_payment pt,
         pnpd_document doc,
         pnpd_payment_dependant pd
    where substr(pt.rfpm_id,1,4) = :p1
    and doc.pncp_date Between to_date(:dt_from,'yyyy-mm-dd') And to_date(:dt_to,'yyyy-mm-dd')
	and doc.ridt_id in (6,7,8)
	and doc.status in (0,1,2)
    and pt.pnpt_id=doc.source_id
    and pt.pnpt_id=pd.pnpt_id(+)
    group by substr(pt.rfpm_id,8,1)
) group by count_dependant
  order by 1
"""


stmt_itogo_2 = """
select count_dependant, 
       sum(cnt_dependant),
       sum(ucnt_pnpt_id),
       sum(sum_pay)
from (       
    select /*+ parallel(4) */ 
	       substr(pt.rfpm_id,8,1) count_dependant,
           sum(0) as cnt_dependant,
           count(unique pt.pnpt_id) ucnt_pnpt_id,
           sum(pt.sum_pay) sum_pay -- 21 665 968 909 на 13.02.2023
    from payment_history pt,
         pnpd_document doc
    where pt.pnpt_id=doc.source_id
    and substr(pt.rfpm_id,1,4) = :p1
	and doc.ridt_id in (6,7,8)
	and doc.status in (0,1,2)
    and doc.pncp_date Between to_date(:dt_from,'yyyy-mm-dd') And to_date(:dt_to,'yyyy-mm-dd')
	and pt.act_month = trunc(to_date(:dt_from, 'yyyy-mm-dd'),'MM')
    group by substr(pt.rfpm_id,8,1)
    union 
    select /*+ parallel(4) */ 
		   substr(pt.rfpm_id,8,1) count_dependant,
           count(unique pd.sicid) cnt_dependant, 
           sum(0),
           sum(0)
    from payment_history pt,
         pnpd_document doc,
         pnpd_payment_dependant pd
    where substr(pt.rfpm_id,1,4) = :p1
    and doc.pncp_date Between to_date(:dt_from,'yyyy-mm-dd') And to_date(:dt_to,'yyyy-mm-dd')
	and doc.ridt_id in (6,7,8)
	and doc.status in (0,1,2)
    and pt.pnpt_id=doc.source_id
    and pt.pnpt_id=pd.pnpt_id(+)
	and pt.act_month = trunc(to_date(:dt_from, 'yyyy-mm-dd'),'MM')
    group by substr(pt.rfpm_id,8,1)
) group by count_dependant
  order by 1
"""


active_stmt = stmt_itogo


def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)

	worksheet.set_column(0, 0, 7)
	worksheet.set_column(1, 1, 14)
	worksheet.set_column(2, 2, 14)
	worksheet.set_column(3, 3, 14)
	worksheet.set_column(4, 4, 18)

	worksheet.write(2, 0, '№', common_format)
	worksheet.write(2, 1, 'Кол-во иждивенцев согласно коду выплаты', common_format)
	worksheet.write(2, 2, 'Кол-во иждивенцев на выплате', common_format)
	worksheet.write(2, 3, 'Количество уникальных выплат', common_format)
	worksheet.write(2, 4, 'Сумма выплат', common_format)


def do_report(file_name: str, date_from: str, date_to: str):
	#cx_Oracle.init_oracle_client(lib_dir='c:/instantclient_21_3')
	#cx_Oracle.init_oracle_client(lib_dir='/home/aktuar/instantclient_21_8')
	log.info(f'DO REPORT. START {report_code}. RFPM_ID: 0701, DATE_FROM: {date_from}, FILE_PATH: {file_name}')
	with cx_Oracle.connect(user='sswh', password='sswh', dsn="172.16.17.12/gfss", encoding="UTF-8") as connection:
		workbook = xlsxwriter.Workbook(file_name)

		title_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
		title_format.set_align('vcenter')
		title_format.set_border(1)
		title_format.set_text_wrap()
		title_format.set_bold()

		title_name_report = workbook.add_format({'align': 'left', 'font_color': 'black', 'font_size': '14'})
		title_name_report .set_align('vcenter')
		title_name_report .set_bold()

		common_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
		common_format.set_align('vcenter')
		common_format.set_border(1)

		sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
		sum_pay_format.set_border(1)
		date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
		date_format.set_border(1)
		date_format.set_align('vcenter')

		digital_format = workbook.add_format({'num_format': '# ### ##0', 'align': 'center'})
		digital_format.set_border(1)
		digital_format.set_align('vcenter')

		money_format = workbook.add_format({'num_format': '# ### ### ### ##0', 'align': 'right'})
		money_format.set_border(1)
		money_format.set_align('vcenter')

		now = datetime.datetime.now()
		log.info(f'Начало формирования {file_name}: {now.strftime("%d-%m-%Y %H:%M:%S")}')
		worksheet = workbook.add_worksheet('Список')
		sql_sheet = workbook.add_worksheet('SQL')
		merge_format = workbook.add_format({
			'bold':     False,
			'border':   6,
			'align':    'left',
			'valign':   'vcenter',
			'fg_color': '#FAFAD7',
			'text_wrap': True
		})
		sql_sheet.merge_range('A1:I35', active_stmt, merge_format)

		worksheet.activate()
		format_worksheet(worksheet=worksheet, common_format=title_format)

		worksheet.write(0, 0, report_name, title_name_report)
		worksheet.write(1, 0, f'За период: {date_from} - {date_to}', title_name_report)

		row_cnt = 1
		shift_row = 2
		cnt_part = 0
		m_val = [0,0,0,0]
		rec_num = 3

		cursor = connection.cursor()
		log.info(f'Загружаем данные за период {date_from} : {date_to} -> {file_name}')
		try:
			rfpm_id = '0701'
			cursor.execute(active_stmt, [rfpm_id, date_from, date_to])
		except cx_Oracle.DatabaseError as e:
			error, = e.args
			log.error(f"Oracle error: {error.code} : {error.message}")
			log.error(f"DO REPORT. EXECUTE. FINISH WITH ERROR. {file_name}")
			log.error(f"DO REPORT. EXECUTE. STMT: {active_stmt}")
			return

		log.info(f'DO REPORT. EXECUTE START FETCHALL')
		try:
			records = cursor.fetchall()
		except cx_Oracle.DatabaseError as e:
			error, = e.args
			log.error(f"Oracle error: {error.code} : {error.message}")
			log.error(f"DO REPORT. FETCHALL. FINISH WITH DATABASE ERROR. {file_name}")
			return
		except MemoryError as e:
			log.error(f"DO REPORT. FETCHALL. FINISH WITH MEMORY ERROR. {file_name}")
			return
		#for record in records:
		for record in records:
			col = 1
			worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
			for list_val in record:
				if col in (1,2,3):
					worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
				if col == 4:
					worksheet.write(row_cnt+shift_row, col, list_val, money_format)
				m_val[col-1] = int(m_val[col-1]) + int(list_val)
				col += 1
			row_cnt += 1
			cnt_part += 1
			if cnt_part > 999:
				log.info(f'{file_name}. LOADED {row_cnt} records.')
				cnt_part = 0
			rec_num = rec_num + 1
		#worksheet.write(row_cnt+1, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)

		worksheet.write(rec_num, 2, m_val[1], digital_format)
		worksheet.write(rec_num, 3, m_val[2], digital_format)
		worksheet.write(rec_num, 4, m_val[3], money_format)
		workbook.close()
		now = datetime.datetime.now()
		log.info(f'DO REPORT. SUCCESS REPORT. {now.strftime("%d-%m-%Y %H:%M:%S")} : {file_name}')
		set_status_report(file_name, 2)


def get_file_path(file_name: str, date_from: str, date_to: str):
	full_file_name = f'{file_name}.0701_01.{date_from}_{date_to}.xlsx'
	return full_file_name


def thread_report(file_name: str, date_from: str, date_to: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: date_from: {date_from}, date_to: {date_to}')
	threading.Thread(target=do_report, args=(file_name, date_from, date_to), daemon=True).start()
	return {"status": 1, "file_path": file_name}

	
	#if platform == 'linux':
	#	from os import fork
	#	pid = fork()
	#	if pid:
	#		return {"status": 1, "file_path": file_name}
	#	else:
	#		log.info(f'MAKE_REPORT. CHILD FORK PROCESS. {file_name}')
	#		do_report(file_name, rfpm_id, date_from, date_to)
	#else:
	#	import threading
	#	log.info(f'MAKE_REPORT. THREAD PROCESS. {file_name}')
	#	threading.Thread(target=do_report, args=(file_name, rfpm_id, date_from, date_to), daemon=True).start()
	#	return {"status": 1, "file_path": file_name}




if __name__ == "__main__":
    log.info(f'MAIN. Отчет запускается.')
    do_report('0701_01.xlsx', '01.01.2022','31.12.2022')
