from   db_config import report_db_user, report_db_password, report_db_dsn
import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   model.manage_reports import set_status_report


report_name = 'Списочная часть смешанных ЕП-шников(СВ)'
report_code = 'CP.05'

stmt_2 = """
with all_data as (
               select /*+parallel(2)*/ si.sicid, sfa.rfbn_id, sfa.iin, sfa.rfpm_id,  sfa.risk_date, sfa.sum_avg, sfa.kzd,mrzp, sfa.count_donation, sfa.sum_all, sfa.date_approve, si.type_payment
               from   si_member_2 si, sipr_maket_first_approve_2 sfa
               where  si.sicid=sfa.sicid
               and    sfa.date_approve >= to_date(:d1,'YYYY-MM-DD') 
			   and    sfa.date_approve <  to_date(:d2,'YYYY-MM-DD') + 1
               and    si.pay_month between add_months(sfa.risk_date,-24) and sfa.risk_date
               and    si.pay_date > add_months(sfa.risk_date,-24)
         ),
ep as (
               select unique sicid
               from   all_data a
               where  nvl(a.type_payment,'U')='О'
         )
        ,
non_ep as (
               select unique sicid
               from   all_data a
               where  nvl(a.type_payment,'U')!='О' --or type_payer is null
         )
select a.sicid, a.rfbn_id, a.iin, a.rfpm_id, a.risk_date, a.sum_avg, a.kzd, a.mrzp, a.count_donation, a.sum_all, a.date_approve
from (
      select sicid from ep
      intersect
      select sicid from non_ep
     )b, all_data a
where b.sicid=a.sicid
group by a.sicid, a.rfbn_id, a.iin, a.rfpm_id, a.risk_date, a.sum_avg, a.kzd, a.mrzp, a.count_donation, a.sum_all, a.date_approve
"""

active_stmt = stmt_2

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)

	worksheet.set_column(0, 0, 7)
	worksheet.set_column(1, 1, 12)
	worksheet.set_column(2, 2, 8)
	worksheet.set_column(3, 3, 17)
	worksheet.set_column(4, 4, 16)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 16)
	worksheet.set_column(7, 7, 10)
	worksheet.set_column(8, 8, 10)
	worksheet.set_column(9, 9, 13)
	worksheet.set_column(10, 10, 10)
	worksheet.set_column(11, 11, 12)

	worksheet.write(2, 0, '№', common_format)
	worksheet.write(2, 1, 'СИК ID', common_format)
	worksheet.write(2, 2, 'Код региона', common_format)
	worksheet.write(2, 3, 'ИИН', common_format)
	worksheet.write(2, 4, 'Код выплаты', common_format)
	worksheet.write(2, 5, 'Дата риска', common_format)
	worksheet.write(2, 6, 'СМД', common_format)
	worksheet.write(2, 7, 'КЗД', common_format)
	worksheet.write(2, 8, 'МРЗП', common_format)
	worksheet.write(2, 9, 'Количество месяцев', common_format)
	worksheet.write(2, 10, 'Общая сумма', common_format)
	worksheet.write(2, 11, 'Дата назначения', common_format)


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
					if col in (5,11):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					else:
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					col += 1
				row_cnt += 1
				cnt_part += 1
				if cnt_part > 999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			# Шифр отчета
			worksheet.write(0, 7, report_code, title_name_report)

			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			worksheet.write(1, 7, f'Дата формирования: {now}', date_format_it)

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
