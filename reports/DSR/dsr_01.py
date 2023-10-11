import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   db_config import report_db_user, report_db_password, report_db_dsn
from   model.call_report import set_status_report

# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)

report_name = 'Контроль сроков выплаты '
report_code = 'dsr.01'

stmt_create = """
select /*+parallel(4)*/ 
       UNIQUE 
       doc.rfbn_id, 
       sipr.iin, 
       sipr.date_approve, 
       ( select unique first_value(st.dat) over(partition by sipr_id order by st.dat asc) 
         from ss_m_sol_st st 
         where st.sid=sipr.sipr_id
         and   st.st2=20
       ) date_20,
       sipr.sum_all, 
       first_value(pd.pay_date) over(partition by sipr.iin, sipr.sipr_id order by pd.pay_date asc) pncd_date,
       ( first_value(pd.pay_date) over(partition by sipr.iin, sipr.sipr_id order by pd.pay_date asc) - 
       sipr.date_approve ) as cnt_days,
       first_value(doc.pay_sum) over(partition by sipr.iin, sipr.sipr_id order by doc.pncp_date) sum_doc,
       first_value(doc.sum_debt) over(partition by sipr.iin, sipr.sipr_id order by doc.pncp_date) sum_debt
from sipr_maket_first_approve_2 sipr, pnpd_document doc, pmpd_pay_doc pd 
where sipr.date_approve>=to_date(:date_first,'YYYY-MM-DD')
and   sipr.date_approve<=to_date(:date_second,'YYYY-MM-DD')
and   doc.knp = :knp
and   substr(sipr.rfpm_id, 1, 4) = :rfpm_id
and sipr.pnpt_id = doc.source_id
and doc.mhmh_id = pd.mhmh_id(+)
"""

active_stmt = stmt_create

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 28)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 24)
	worksheet.set_row(3, 24)

	worksheet.set_column(0, 0, 9)
	worksheet.set_column(1, 1, 10)
	worksheet.set_column(2, 2, 14)
	worksheet.set_column(3, 3, 12)
	worksheet.set_column(4, 4, 12)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 12)
	worksheet.set_column(9, 9, 16)

	worksheet.merge_range('A3:A4', '№', common_format)
	worksheet.merge_range('B3:B4', 'Код региона', common_format)
	worksheet.merge_range('C3:C4', 'ИИН получателя', common_format)
	worksheet.merge_range('D3:D4', 'Дата назначения', common_format)
	worksheet.merge_range('E3:E4', 'Дата 20', common_format)
	worksheet.merge_range('F3:F4', 'Размер СВ', common_format)
	worksheet.merge_range('G3:G4', 'Первая дата выплаты', common_format)
	worksheet.merge_range('H3:H4', 'Кол-во дней', common_format)
	worksheet.merge_range('I3:I4', 'Сумма выплаты', common_format)
	worksheet.merge_range('J3:J4', 'Сумма задолженности', common_format)

def do_report(file_name: str, date_first: str, date_second: str, srfpm_id: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name
	#cx_Oracle.init_oracle_client(lib_dir='c:/instantclient_21_3')
	#cx_Oracle.init_oracle_client(lib_dir='/home/aktuar/instantclient_21_8')
	with oracledb.connect(user=report_db_user, password=report_db_password, dsn=report_db_dsn, encoding="UTF-8") as connection:
		with connection.cursor() as cursor:
			workbook = xlsxwriter.Workbook(file_name)

			title_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_color': 'black'})
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

			date_format_it = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format_it.set_align('vcenter')
			date_format_it.set_italic()

			digital_format = workbook.add_format({'num_format': '# ### ##0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '# ### ### ### ##0.00', 'align': 'right'})
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

			worksheet.write(0, 0, f'{report_name} : {srfpm_id}', title_name_report)
			worksheet.write(1, 0, f'За период: {date_first} - {date_second}, ', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0
			m_val = [0]
			v_knp='000'
			
			match srfpm_id:
				case '0703':
					v_knp='048'
				case '0705':
					v_knp='091'
				case _:
					v_knp='000'

			log.info(f'{file_name}. Загружаем данные за период {date_first} - {date_second}, КНП: {v_knp}, RFPM: {srfpm_id}')
			cursor.execute(active_stmt, date_first=date_first, date_second=date_second, rfpm_id=srfpm_id, knp=v_knp)

			records = cursor.fetchall()

			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (1,2,7):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col in (3,4,6):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					# if col in(4,):
					# 	worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col in (5,8,9):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				cnt_part += 1
				if cnt_part > 9999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0
				row_cnt += 1

			worksheet.write(row_cnt + shift_row, 8, m_val[0], money_format)

			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			worksheet.write(1, 8, f'Дата формирования: {now}', date_format_it)

			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {file_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			set_status_report(file_name, 2)
			return file_name


def get_file_path(file_name: str, date_first: str, date_second: str, srfpm_id: str):
	full_file_name = f'{file_name}.{report_code}.{srfpm_id}.{date_first}-{date_second}.xlsx'
	return full_file_name


def thread_report(file_name: str, date_first: str, date_second: str, srfpm_id: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: rfpm_id: {srfpm_id}, date_first: {date_first}, date_second: {date_second}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second, srfpm_id), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    #make_report('0701', '01.10.2022','31.10.2022')
    do_report('01.01.2023')
