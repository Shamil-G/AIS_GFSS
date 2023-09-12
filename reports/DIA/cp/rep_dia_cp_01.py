import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   db_config import report_db_user, report_db_password, report_db_dsn
from   model.call_report import set_status_report


report_name = 'Участники ЕП'
report_code = 'ЕдПл.01'

stmt_1 = """
	select /*+ parallel (4)*/
		pd.PAY_DATE,
		pd.sum_pay,
		case when p.sex=0 then 'ж' else 'м' end sex,
		rN,
		pay_month,
		pd.pay_date_gfss,
		p.birthdate, 
		floor(months_between(sysdate, p.birthdate)/12) age
	from si_member_2 pd, person p
	where pd.type_payment = 'О'
	and	  pd.knp = '012'
	and   trunc(pd.pay_date_gfss,'DD') between to_date(:dt_from, 'YYYY-MM-DD') and to_date(:dt_to, 'YYYY-MM-DD')
    and si.pay_date_gfss  >= to_date('01.02.2023','dd.mm.yyyy')
    and si.pay_date	  >= to_date('01.02.2023','dd.mm.yyyy')
	and   pd.pay_date > (to_date(:dt_from, 'YYYY-MM-DD') - 14 )
	and   pd.pay_date <= to_date(:dt_to, 'YYYY-MM-DD')
	and   pd.sicid = p.sicid
"""

active_stmt = stmt_1

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 22)
	worksheet.set_row(3, 22)

	worksheet.set_column(0, 0, 8)
	worksheet.set_column(1, 1, 14)
	worksheet.set_column(2, 2, 16)
	worksheet.set_column(3, 3, 8)
	worksheet.set_column(4, 4, 14)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 8)

	worksheet.merge_range('A3:A4', '№', common_format)
	worksheet.merge_range('B3:B4', 'Дата платежа', common_format)
	worksheet.merge_range('C3:C4', 'Сумма СО', common_format)
	worksheet.merge_range('D3:D4', 'Пол', common_format)
	worksheet.merge_range('E3:E4', 'ИИН', common_format)
	worksheet.merge_range('F3:F4', 'Период', common_format)
	worksheet.merge_range('G3:G4', 'Дата поступления в ГФСС', common_format)
	worksheet.merge_range('H3:H4', 'Дата рождения', common_format)
	worksheet.merge_range('I3:I4', 'Возраст', common_format)

def do_report(file_name: str, date_first: str, date_second: str):
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

			worksheet.write(0, 0, report_name, title_name_report)
			worksheet.write(1, 0, f'Период расчёта: с {date_first} по {date_second}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0
			m_val = [0]

			log.info(f'{file_name}. Загружаем данные с {date_first} по {date_second}')
			cursor.execute(active_stmt, dt_from=date_first,dt_to=date_second)

			records = cursor.fetchall()
			
			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (2,4,8):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col == 3:
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col in (1,5,6,7):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					if col in (2,):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				cnt_part += 1
				if cnt_part > 9999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0
				row_cnt += 1

			#worksheet.write(row_cnt+shift_row, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)
			#worksheet.write(row_cnt + shift_row, 8, m_val[0], money_format)

			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			worksheet.write(1, 6, f'Дата формирования: {now}', date_format_it)

			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {file_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			set_status_report(file_name, 2)
			return file_name


def thread_report(file_name: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. DATE BETWEEN REPORT: {date_first} - {date_second}, FILE_NAME: {file_name}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    #make_report('0701', '01.10.2022','31.10.2022')
    do_report('01.01.2023', '15.01.2023')
