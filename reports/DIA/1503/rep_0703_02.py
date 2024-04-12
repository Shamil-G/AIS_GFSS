import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   db_config import report_db_user, report_db_password, report_db_dsn
from   model.call_report import set_status_report


report_name = 'Получатели СВпр, выплата которым назначена в тот же месяц, что и месяц окончания СВпр'
report_code = '1503.02'

stmt_1 = """
		with list_stop as(
			select ph.stopdate as date_stop, 
				   ph.sum_pay,
				   ph.date_open,
				   p.rn as iin
			from payment_history ph, person p 
			where trunc(ph.stopdate, 'MM') = trunc(to_date(:dt_from,'YYYY-MM-DD'), 'MM')
			and trunc(ph.act_month, 'MM') = trunc(to_date(:dt_from,'YYYY-MM-DD'), 'MM')
			and substr(ph.rfpm_id,1,4)='0703'
			and ph.pncd_id = p.sicid
		),
		list_start as(
			select /*+ Parallel(4) */
				   sfa.rfbn_id,
				   sfa.rfpm_id, 
				   sfa.iin,
				   sfa.risk_date, 
				   sfa.date_approve,
				   sfa.date_stop, 
				   sfa.sum_all,
				   sfa.ksu,
				   sfa.sum_avg
			from  sipr_maket_first_approve_2 sfa
			where trunc(sfa.date_approve, 'MM') = trunc(to_date(:dt_from,'YYYY-MM-DD'), 'MM')
			and   substr(sfa.rfpm_id,1,4)='0703'
		)
		select /*+ Parallel(4) */
			   s.rfbn_id, 
			   s.rfpm_id, 
			   s.iin,
			   case when p.sex = 0 then 'Ж' else 'М' end sex,
			   s.risk_date,
			   s.date_approve,
			   f.date_stop date_stop_prev,
			   s.date_stop date_stop_cur,
			   f.sum_pay prev_sum_all,
			   s.sum_all, 
			   s.ksu,
			   s.sum_avg
		from list_start s, list_stop f, person p
		where s.iin=f.iin
		and   f.date_open!=s.date_approve
		and   s.iin=p.rn(+)
		and   s.risk_date <= f.date_stop
"""

active_stmt = stmt_1

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 22)
	worksheet.set_row(3, 22)

	worksheet.set_column(0, 0, 8)
	worksheet.set_column(1, 1, 14)
	worksheet.set_column(2, 2, 14)
	worksheet.set_column(3, 3, 14)
	worksheet.set_column(4, 4, 8)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 12)
	worksheet.set_column(9, 9, 14)
	worksheet.set_column(10, 10, 14)
	worksheet.set_column(11, 11, 8)
	worksheet.set_column(12, 12, 14)

	worksheet.merge_range('A3:A4', '№', common_format)
	worksheet.merge_range('B3:B4', 'Код региона', common_format)
	worksheet.merge_range('C3:C4', 'Код выплаты', common_format)
	worksheet.merge_range('D3:D4', 'ИИН получателя', common_format)
	worksheet.merge_range('E3:E4', 'Пол', common_format)
	worksheet.merge_range('F3:F4', 'Дата риска', common_format)
	worksheet.merge_range('G3:G4', 'Дата назначения', common_format)
	worksheet.merge_range('H3:H4', 'Дата окончания', common_format)
	worksheet.merge_range('I3:I4', 'Новая дата окончания СВ', common_format)
	worksheet.merge_range('J3:J4', 'Размер предыдущей СВ', common_format)
	worksheet.merge_range('K3:K4', 'Новый размер СВ', common_format)
	worksheet.merge_range('L3:L4', 'КСУ', common_format)
	worksheet.merge_range('M3:M4', 'СМД', common_format)

def do_report(file_name: str, date_first: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name
	#cx_Oracle.init_oracle_client(lib_dir='c:/instantclient_21_3')
	#cx_Oracle.init_oracle_client(lib_dir='/home/aktuar/instantclient_21_8')
	with oracledb.connect(user=report_db_user, password=report_db_password, dsn=report_db_dsn) as connection:
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
			worksheet.write(1, 0, f'Месяц расчёта: {date_first}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0
			m_val = [0]

			log.info(f'{file_name}. Загружаем данные за период {date_first}')
			cursor.execute(active_stmt, dt_from=date_first)

			records = cursor.fetchall()
			
			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (1,2,3):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col == 4:
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col in (5,6,7,8):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					if col in (9,10,11,12):
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
			worksheet.write(1, 10, f'Дата формирования: {now}', date_format_it)

			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {file_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			set_status_report(file_name, 2)
			return file_name


def thread_report(file_name: str, date_first: str):
	import threading
	log.info(f'THREAD REPORT. DATE FOR REPORT: {date_first}, FILE_NAME: {file_name}')
	threading.Thread(target=do_report, args=(file_name, date_first), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    #make_report('0701', '01.10.2022','31.10.2022')
    do_report('01.01.2023')
