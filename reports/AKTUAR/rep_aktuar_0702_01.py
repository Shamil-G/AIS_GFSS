from configparser import ConfigParser
import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   model.manage_reports import set_status_report


report_name = 'Получатели СВут 0702 за период:'
report_code = f'AK_01'

stmt_1 = """
with sum_calc  as(
    select /*+ full(si) parallel(8) */
       sicid, count(unique trunc(si.pay_month)) cnt_pay_month
    from si_member_2 si
    where si.pay_date < :dt_from 
    group by sicid
)
select /*+ Parallel(4) */
       ph.rfbn_id, 
       sfa.rfpm_id, 
       --sfa.iin, 
       p.iin,
       case when sfa.sex = 0 then 'Ж' else 'М' end sex, 
       to_char(p.birthdate,'dd.mm.yyyy'),
       sfa.risk_date, 
       sfa.date_approve, 
       sfa.ksu,
       sfa.kut,
       sfa.sum_avg,
       sc.cnt_pay_month,
       sfa.count_donation,
       ph.sum_pay,
       sfa.sum_all
from  payment_history ph, sipr_maket_first_approve_2 sfa, sum_calc sc
      ,person p
where trunc(ph.act_month,'MM') = :dt_from
and   substr(ph.rfpm_id,1,4)='0702'
and   ph.pnpt_id = sfa.pnpt_id(+)
and   ph.pncd_id = sc.sicid(+)
and   ph.pncd_id = p.sicid
"""

active_stmt = stmt_1

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)

	worksheet.set_column(0, 0, 10)
	worksheet.set_column(1, 1, 14)
	worksheet.set_column(2, 2, 14)
	worksheet.set_column(3, 3, 14)
	worksheet.set_column(4, 4, 8)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 18)
	worksheet.set_column(8, 8, 8)
	worksheet.set_column(9, 9, 8)
	worksheet.set_column(10, 10, 14)
	worksheet.set_column(11, 11, 14)
	worksheet.set_column(12, 12, 14)
	worksheet.set_column(13, 13, 14)
	worksheet.set_column(14, 14, 14)

	worksheet.write(2, 0, '№', common_format)
	worksheet.write(2, 1, 'Код региона', common_format)
	worksheet.write(2, 2, 'Код выплаты', common_format)
	worksheet.write(2, 3, 'ИИН получателя', common_format)
	worksheet.write(2, 4, 'Пол', common_format)
	worksheet.write(2, 5, 'Дата рождения', common_format)
	worksheet.write(2, 6, 'Дата риска', common_format)
	worksheet.write(2, 7, 'Дата назначения', common_format)
	worksheet.write(2, 8, 'КСУ', common_format)
	worksheet.write(2, 9, 'КУТ', common_format)
	worksheet.write(2, 10, 'СМД', common_format)
	worksheet.write(2, 11, 'Стаж участия на дату расчета', common_format)
	worksheet.write(2, 12, 'Стаж участия на дату риска', common_format)
	worksheet.write(2, 13,  'Размер СВ (текущий)', common_format)
	worksheet.write(2, 14, 'Размер СВ  (расчет)', common_format)


def do_report(file_name: str, srfpm_id: str, date_first: str):
	print(f'MAKE REPORT started...')
	if os.path.isfile(file_name):
		print(f'Отчет уже существует {file_name}')
		log.info(f'Отчет уже существует {file_name}')
		return file_name

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
				title_report_code.set_bold()

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
				worksheet.write(1, 0, f'За период: {date_first}', title_name_report)

				row_cnt = 1
				shift_row = 2
				cnt_part = 0
				m_val = [0]

				cursor = connection.cursor()
				log.info(f'{file_name}. Загружаем данные за период {date_first}')
				cursor.execute(active_stmt, [date_first])

				records = cursor.fetchall()
			
				#for record in records:
				for record in records:
					col = 1
					worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
					for list_val in record:
						if col in (1,2,3,11,12):
							worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
						if col in (5,6,7):
							worksheet.write(row_cnt+shift_row, col, list_val, date_format)
						if col == 4:
							worksheet.write(row_cnt+shift_row, col, list_val, common_format)
						if col in (8,9,10,13,14):
							worksheet.write(row_cnt+shift_row, col, list_val, money_format)
						col += 1
					cnt_part += 1
					if cnt_part > 9999:
						log.info(f'{file_name}. LOADED {row_cnt} records.')
						cnt_part = 0
					row_cnt += 1
				worksheet.write(row_cnt + shift_row, 7, m_val[0], money_format)

				#worksheet.write(row_cnt+shift_row, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)
				# Шифр отчета
				worksheet.write(0, 13, report_code, title_report_code)
				now = datetime.datetime.now()
				stop_time = now.strftime("%H:%M:%S")

				worksheet.write(1, 13, f'Дата формирования: {now.strftime("%d.%m.%Y ")}({s_date} - {stop_time})', title_format_it)
				#
				workbook.close()
				set_status_report(file_name, 2)

				log.info(f'REPORT: {report_code}. Формирование отчета {file_name} завершено: {now}. Строк в отчете: {row_cnt-1}')


def thread_report(file_name: str, srfpm_id: str, date_first: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: date_from: {date_first}')
	threading.Thread(target=do_report, args=(file_name, srfpm_id, date_first), daemon=True).start()
	return {"status": 1, "file_path": file_name}
