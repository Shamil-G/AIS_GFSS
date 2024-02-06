from   db_config import report_db_user, report_db_password, report_db_dsn
import xlsxwriter
import datetime
import os.path
from   util.logger import log
from   model.call_report import set_status_report
import oracledb

# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)

report_name = 'Список лиц, которым назначена социальная выплата на случай потери дохода в связи с уходом за ребенком по достижении им возраста 1 года'
report_code = '6020.5'

stmt_1 = """
SELECT 
          sfa.rfbn_id code_region, --"Код региона",
          sfa.rfpm_id rfpm, --"Код выплаты",
          p.rn rnn, --"ИИН",
          p.lastname || ' ' || p.firstname || ' ' || p.middlename fio,--"ФИО",
          case when p.sex=0 then 'ж' else 'м' end sx,--"Пол",
          sfa.birthdate,
          sfa.risk_date risk,--"Дата риска",
		  sfa.date_approve d_resh, --"Дата решения",
          sfa.sum_avg sumavg,--"СМД, тенге",
          sfa.kzd sfa_kzd,--"КЗД",
          sfa.mrzp sfa_mrzp,--"МЗП",
          sfa.count_donation donation,--"Количество месяцев",
          sfa.sum_all sfa_all, --"Назначенный размер, тенге"
          case when p.status in (4,2) then 'Умерший' else 'Получатель' end status
        FROM sipr_maket_first_approve_2 sfa, person p
        WHERE sfa.sicp_id = p.sicid
        AND sfa.rfpm_id LIKE '0705%'
        AND trunc(sfa.date_approve) Between to_date(:d1,'yyyy-mm-dd') And to_date(:d2,'yyyy-mm-dd')
        order by rfbn_id, p.lastname
"""

active_stmt = stmt_1

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)

	worksheet.set_column(0, 0, 7)
	worksheet.set_column(1, 1, 8)
	worksheet.set_column(2, 2, 9)
	worksheet.set_column(3, 3, 15)
	worksheet.set_column(4, 4, 40)
	worksheet.set_column(5, 5, 8)
	worksheet.set_column(6, 6, 16)
	worksheet.set_column(7, 7, 16)
	worksheet.set_column(8, 8, 12)
	worksheet.set_column(9, 9, 11)
	worksheet.set_column(10, 10, 8)
	worksheet.set_column(11, 11, 8)
	worksheet.set_column(12, 12, 12)
	worksheet.set_column(13, 13, 15)
	worksheet.set_column(14, 14, 12)


	worksheet.write(2, 0, '№', common_format)
	worksheet.write(2, 1, 'Код региона', common_format)
	worksheet.write(2, 2, 'Код выплаты', common_format)
	worksheet.write(2, 3, 'ИИН', common_format)
	worksheet.write(2, 4, 'ФИО', common_format)
	worksheet.write(2, 5, 'Пол', common_format)
	worksheet.write(2, 6, 'Дата рождения', common_format)
	worksheet.write(2, 7, 'Дата риска', common_format)
	worksheet.write(2, 8, 'Дата решения', common_format)
	worksheet.write(2, 9, 'СМД, тенге', common_format)
	worksheet.write(2, 10, 'КЗД', common_format)
	worksheet.write(2, 11, 'МЗП', common_format)
	worksheet.write(2, 12, 'Количество месяцев', common_format)
	worksheet.write(2, 13, 'Назначенный размер', common_format)
	worksheet.write(2, 14, 'Статус', common_format)
	




def do_report(file_name: str, date_first: str, date_second: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name
	log.info(f'DO REPORT. START {report_code}. RFPM_ID: 0701, DATE_FROM: {date_first}, FILE_PATH: {file_name}')
	with oracledb.connect(user=report_db_user, password=report_db_password, dsn=report_db_dsn, encoding="UTF-8") as connection:
		with connection.cursor() as cursor:
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

			date_format_it = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'left'})
			date_format_it.set_align('vcenter')
			date_format_it.set_italic()
			
			name_format = workbook.add_format({'align': 'left', 'font_color': 'black'})
			name_format.set_align('vcenter')
			name_format.set_border(1)

			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			sum_pay_format.set_border(1)
			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			digital_format = workbook.add_format({'num_format': '#0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '# ### ##0', 'align': 'right'})
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
			worksheet.write(1, 0, f'За период: {date_first} - {date_second}', title_name_report)

			row_cnt = 1
			shift_row = 2
			cnt_part = 0

			cursor = connection.cursor()
			log.info(f'{file_name}. Загружаем данные за период {date_first} : {date_second}')
			cursor.execute(active_stmt, d1=date_first, d2=date_second)

			records = cursor.fetchall()
			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (2,4):
						worksheet.write(row_cnt+shift_row, col, list_val, name_format)
					if col in (6,7,8):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					else:
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					col += 1
				row_cnt += 1
				cnt_part += 1
				if cnt_part > 999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			#worksheet.write(row_cnt+1, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)
			# Шифр отчета
			worksheet.write(0, 10, report_code, title_name_report)
			
			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			worksheet.write(1, 10, f'Дата формирования: {now}', date_format_it)

			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {file_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			set_status_report(file_name, 2)


def thread_report(file_name: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. DATE BETWEEN REPORT: {date_first} - {date_second}, FILE_NAME: {file_name}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_name} запускается.')
    do_report('01.06.2023','10.06.2023')
