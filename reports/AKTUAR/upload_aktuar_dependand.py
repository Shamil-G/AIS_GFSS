from configparser import ConfigParser
from   os import path
import xlsxwriter
import datetime

import oracledb
from   util.logger import log
from   util.trunc_date import first_day
from   model.manage_reports import set_status_report


report_name = 'Таблица AKTUAR_DEPENDANT'
report_code = 'AD.01'

stmt = """
select  /*+parallel(8)*/pncd_id, pnpt_id, 
		sex, birthdate, 
		rfpm_id, 
		appointdate, stopdate, sum_pay, depend_sicid, 
		depend_sex, 
		depend_birthdate, sic_bw_f, sic_bw_m,
		mnth
from sswh.aktuar_dependant
where mnth = trunc(to_date(:month_download,'YYYY-MM-DD'), 'MM')
"""

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)

	worksheet.set_column(0, 0, 8)
	worksheet.set_column(1, 1, 14)
	worksheet.set_column(2, 2, 11)
	worksheet.set_column(3, 3, 8)
	worksheet.set_column(4, 4, 12)
	worksheet.set_column(5, 5, 10)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 12)
	worksheet.set_column(9, 9, 12)
	worksheet.set_column(10, 10, 8)
	worksheet.set_column(11, 11, 12)
	worksheet.set_column(12, 12, 20)
	worksheet.set_column(13, 13, 20)
	worksheet.set_column(14, 14, 12)
	worksheet.set_column(15, 15, 12)

	# worksheet.write(2, 2, 'Код региона', common_format)
	worksheet.write(2, 0, '№', common_format)
	worksheet.write(2, 1, 'Ид плательщика', common_format)
	worksheet.write(2, 2, 'Ид выплаты', common_format)
	worksheet.write(2, 3, 'Пол плательщика', common_format)
	worksheet.write(2, 4, 'Дата рождения', common_format)
	worksheet.write(2, 5, 'Код выплаты', common_format)
	worksheet.write(2, 6, 'Дата назначения', common_format)
	worksheet.write(2, 7, 'Дата окончания', common_format)
	worksheet.write(2, 8, 'Сумма выплаты', common_format)
	worksheet.write(2, 9, 'Ид иждивенца', common_format)
	worksheet.write(2, 10, 'Пол иждив.', common_format)
	worksheet.write(2, 11, 'Дата рождения иждивенца', common_format)
	worksheet.write(2, 12, 'SIC матери иждивенца', common_format)
	worksheet.write(2, 13, 'SIC отца иждивенца', common_format)
	worksheet.write(2, 14, 'Месяц расчета', common_format)


def do_report(file_name: str, date_first: str):

	if path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name

	first_d=first_day(date_first)
	s_date = datetime.datetime.now().strftime("%H:%M:%S")

	log.info(f'DO REPORT. START {report_code}. DATE_FROM: {date_first}, FILE_PATH: {file_name}')

	config = ConfigParser()
	config.read('db_config.ini')
	
	ora_config = config['rep_db_loader']
	db_user=ora_config['db_user']
	db_password=ora_config['db_password']
	db_dsn=ora_config['db_dsn']
	log.info(f'{report_code}. db_user: {db_user}, db_dsn: {db_dsn}')
	
	with oracledb.connect(user=db_user, password=db_password, dsn=db_dsn) as connection:
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

			title_format_it = workbook.add_format({'align': 'right'})
			title_format_it.set_align('vcenter')
			title_format_it.set_italic()

			title_report_code = workbook.add_format({'align': 'right', 'font_size': '14'})
			title_report_code.set_align('vcenter')

			common_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
			common_format.set_align('vcenter')
			common_format.set_border(1)

			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			sum_pay_format.set_border(1)

			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			digital_format = workbook.add_format({'num_format': '######0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '# ### ### ### ##0.00', 'align': 'right'})
			money_format.set_border(1)
			money_format.set_align('vcenter')

			now = datetime.datetime.now()
			log.info(f'Начало формирования {file_name}: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			page_num = 1
			worksheet = []
			worksheet.append( workbook.add_worksheet(f'Список {page_num}') )

			sql_sheet = workbook.add_worksheet('SQL')
			merge_format = workbook.add_format({
				'bold':     False,
				'border':   6,
				'align':    'left',
				'valign':   'vcenter',
				'fg_color': '#FAFAD7',
				'text_wrap': True
			})
			sql_sheet.merge_range(f'A1:I{len(stmt.splitlines())}', f'{stmt}', merge_format)

			worksheet[page_num-1].activate()
			format_worksheet(worksheet=worksheet[page_num-1], common_format=title_format)

			# worksheet[page_num-1].write(0, 0, report_name, title_name_report)
			# worksheet[page_num-1].write(1, 0, f'Выгрузка за месяц: {first_d}', title_name_report)

			row_cnt = 1
			all_cnt=0
			shift_row = 3
			cnt_part = 0

			log.info(f'{file_name}. Загружаем данные за месяц {first_d}')
			try:
				cursor.execute(stmt, month_download=first_d)
			except oracledb.DatabaseError as e:
				error, = e.args
				log.error(f"ERROR. REPORT {report_code}. error_code: {error.code}\n\terror: {error.message}")
				log.info(f'\n---------\n{stmt}\n---------')
				set_status_report(file_name, 3)
				return
			finally:
				log.info(f'REPORT: {report_code}. Выборка из курсора завершена')

			log.info(f'REPORT: {report_code}. Формируем выходную EXCEL таблицу')

			records = cursor.fetchall()

			#for record in records:
			for record in records:
				col = 1
				worksheet[page_num-1].write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (1,2,3,9,10):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, digital_format)
					if col in (5,12,13):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, common_format)
					if col in (4,6,7,11,14):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, date_format)
					if col in (8,):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				row_cnt+= 1
				cnt_part+= 1
				all_cnt+=1
				if (all_cnt//1000000) +1 > page_num:
					page_num=page_num+1
					row_cnt=1
					# ADD a new worksheet
					worksheet.append( workbook.add_worksheet(f'Список {page_num}') )
				if cnt_part > 250000:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			#
			now = datetime.datetime.now()
			stop_time = now.strftime("%H:%M:%S")

			for i in range(page_num):
				# ADD HEADERS
				format_worksheet(worksheet=worksheet[page_num-1], common_format=title_format)
				worksheet[page_num-1].write(0, 0, report_name, title_report_code)
				worksheet[page_num-1].write(1, 0, f'Выгрузка за месяц: {first_d}', title_name_report)
				# Шифр отчета
				worksheet[i].write(0, 14, report_code, title_name_report)

				worksheet[i].write(1, 14, f'Дата формирования: {now.strftime("%d.%m.%Y ")}({s_date} - {stop_time})', title_format_it)


			workbook.close()
			set_status_report(file_name, 2)
			log.info(f'Формирование отчета {file_name} завершено: {now}, Загружено {all_cnt} записей')


def thread_report(file_name: str, date_first: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: date_from: {date_first}')
	threading.Thread(target=do_report, args=(file_name, date_first), daemon=True).start()
	return {"status": 1, "file_path": file_name}
