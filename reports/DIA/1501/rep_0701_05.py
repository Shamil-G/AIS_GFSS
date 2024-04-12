from   db_config import report_db_user, report_db_password, report_db_dsn
import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   model.manage_reports import set_status_report


report_name = 'Список кормильцев, по которым назначена социальная выплата 0701'
report_code = '0701_СВ'

stmt_1 = """
	SELECT /*+ parallel(4) */
	  sfa.rfbn_id code_region, --"Код региона",
	  sfa.rfpm_id rfpm, --"Код выплаты",
	  p.rn rnn, --"ИИН",
	  p.lastname || ' ' || p.firstname || ' ' || p.middlename fio,--"ФИО",
	  case when p.sex=0 then 'ж' else 'м' end sx,--"Пол",
	  sfa.birthdate,
	  sfa.risk_date risk,--"Дата риска",
	  sfa.sum_avg sumavg,--"СМД, тенге",
	  sfa.ksu sfa_ksu, --"КСУ",
	  sfa.kzd sfa_kzd,--"КЗД",
	  sfa.kut sfa_kut, --"КУТ",
	  sfa.mrzp sfa_mrzp,--"МЗП",
	  sfa.count_donation donation,--"Количество месяцев",
	  sfa.sum_all sfa_all, --"Назначенный размер, тенге"
	  floor(months_between(sfa.risk_date,sfa.birthdate) / 12) as "Возраст кормильца",
	  (
	   select rfpm_id
	   from pnpd_document pd1 
	   where pd1.pncd_id=sfa.sicp_id
	   and  substr(pd1.rfpm_id,1,4) = '0702'
	   and  pd1.pncp_date>=add_months(pd.pncp_date, -1)
	   AND pD.RIDT_ID IN (4, 6, 7, 8)
	   AND pD.STATUS IN (0, 1, 2, 3, 5, 7)
	   AND pD.PNSP_ID > 0
	   and rownum = 1
	  ) as rfpm_id_ut,
	  sfa.sicp_id as "SICID кормильца",
	  pd.pncd_id as "SICID получателя"
	FROM pnpd_document pd, 
		 sipr_maket_first_approve_2 sfa, 
		 person p
	WHERE substr(pd.rfpm_id,1,4)='0701' 
	and   pd.source_id = sfa.pnpt_id(+)
	and  sfa.sicp_id = p.sicid(+)
	AND pD.RIDT_ID IN (4, 6, 7, 8)
	AND pD.STATUS IN (0, 1, 2, 3, 5, 7)
	AND pD.PNSP_ID > 0
	and pd.pncp_date between to_date(:date_first,'YYYY-MM-DD') and to_date(:date_second,'YYYY-MM-DD') 
	order by sfa.rfbn_id, p.lastname
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
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 11)
	worksheet.set_column(9, 9, 8)
	worksheet.set_column(10, 10, 8)
	worksheet.set_column(11, 11, 8)
	worksheet.set_column(12, 12, 8)
	worksheet.set_column(13, 13, 12)
	worksheet.set_column(14, 14, 15)
	worksheet.set_column(15, 15, 12)
	worksheet.set_column(16, 16, 12)


	worksheet.write(2, 0, '№', common_format)
	worksheet.write(2, 1, 'Код региона', common_format)
	worksheet.write(2, 2, 'Код выплаты', common_format)
	worksheet.write(2, 3, 'ИИН', common_format)
	worksheet.write(2, 4, 'ФИО', common_format)
	worksheet.write(2, 5, 'Пол', common_format)
	worksheet.write(2, 6, 'Дата рождения', common_format)
	worksheet.write(2, 7, 'Дата риска', common_format)
	worksheet.write(2, 8, 'СМД, тенге', common_format)
	worksheet.write(2, 9, 'КСУ', common_format)
	worksheet.write(2, 10, 'КЗД', common_format)
	worksheet.write(2, 11, 'КУТ', common_format)
	worksheet.write(2, 12, 'МЗП', common_format)
	worksheet.write(2, 13, 'Количество месяцев', common_format)
	worksheet.write(2, 14, 'Назначенный размер', common_format)
	worksheet.write(2, 15, 'Возраст кормильца', common_format)
	worksheet.write(2, 16, 'Код выплаты 0702', common_format)


def do_report(file_name: str, date_first: str, date_second: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name
	log.info(f'DO REPORT. START {report_code}. RFPM_ID: 0701, DATE_FROM: {date_first}, FILE_PATH: {file_name}')
	with oracledb.connect(user=report_db_user, password=report_db_password, dsn=report_db_dsn) as connection:
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

			money_format = workbook.add_format({'num_format': '# ### ### ### ##0.00', 'align': 'right'})
			money_format.set_border(1)
			money_format.set_align('vcenter')
			
			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			digital_format = workbook.add_format({'num_format': '#0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format_center = workbook.add_format({'num_format': '# ### ##0.00', 'align': 'center'})
			money_format_center.set_border(1)
			money_format_center.set_align('vcenter')

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
			cursor.execute(active_stmt, date_first=date_first, date_second=date_second)

			records = cursor.fetchall()
			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (1,2,3,13,15,16):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col in (9,10,11):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format_center)
					if col in (4,):
						worksheet.write(row_cnt+shift_row, col, list_val, name_format)
					if col in (5,):
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col in (6,7,):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					if col in (8,12,14):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				row_cnt += 1
				cnt_part += 1
				if cnt_part > 9999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			#worksheet.write(row_cnt+1, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)

			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			worksheet.write(1, 13, f'Дата формирования: {now}', date_format_it)

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
