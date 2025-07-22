from configparser import ConfigParser
import xlsxwriter
import datetime
from   util.logger import log
import oracledb
import os.path
from   model.manage_reports import set_status_report

report_name = 'СО по КНП, регионам, количеству участников и сумм (5CO)'
report_code = '5CO'

stmt_report = """
Select /*+ parallel(4) */
      knp, 
      coalesce(reg,'ZZ'),
	  sex,
      Count(Unique sicid) cnt, 
      Sum(sum_pay) sm
From( Select /*+ parallel(4) */
            m.sicid, 
			case when p.sex=0 then 'Ж' else 'М' end as sex,
            m.knp knp, 
            m.sum_pay sum_pay,
            FIRST_VALUE(substr(coalesce(cb.RFBN_ID,'ZZ'),1,2)) 
				over(partition by m.sicid order by m.pay_date_gfss desc) reg
      From  si_member_2 m, rfon_organization o, cato_branch cb, person p
      Where m.PAY_DATE_GFSS >= to_date(:dt_from,'YYYY-MM-DD')
	  and	m.sicid = p.sicid
	  and	m.PAY_DATE_GFSS < to_date(:dt_to,'YYYY-MM-DD') + 1
	  AND   m.PAY_DATE >= add_months(to_date(:dt_from,'YYYY-MM-DD'),-1) 
	  AND	m.PAY_DATE < to_date(:dt_to,'YYYY-MM-DD') + 1
      and   m.p_rnn=o.bin(+)
      and   o.cato=cb.code(+)
) 
group by reg, knp, sex
order by reg, knp
"""


def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 14)
	#worksheet.set_row(3, 48)

	worksheet.set_column(0, 0, 6)
	worksheet.set_column(1, 1, 8)
	worksheet.set_column(2, 2, 12)
	worksheet.set_column(3, 3, 8)
	worksheet.set_column(4, 4, 16)
	worksheet.set_column(5, 6, 18)

	worksheet.write(2,0, '1', common_format)
	worksheet.write(2,1, '2', common_format)
	worksheet.write(2,2, '3', common_format)
	worksheet.write(2,3, '4', common_format)
	worksheet.write(2,4, '5', common_format)
	worksheet.write(2,5, '5', common_format)
	worksheet.write(3,0, '№', common_format)
	worksheet.write(3,1, 'КНП', common_format)
	worksheet.write(3,2, 'Код района', common_format)
	worksheet.write(3,3, 'Пол', common_format)
	worksheet.write(3,4, 'Общее количество сотрудников за которых поступили СО', common_format)
	worksheet.write(3,5, 'Общая сумма СО', common_format)


def do_report(file_name: str, date_first: str, date_second: str):
	if os.path.isfile(file_name):
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

			title_format = workbook.add_format({'bg_color': '#D1FFFF', 'align': 'center', 'font_color': 'black'})
			#title_format = workbook.add_format({'bg_color': '#C5FFFF', 'align': 'center', 'font_color': 'black'})
			title_format.set_align('vcenter')
			title_format.set_border(1)
			title_format.set_text_wrap()
			title_format.set_bold()

			title_name_report = workbook.add_format({'align': 'left', 'font_color': 'black', 'font_size': '14'})
			title_name_report.set_align('vcenter')
			title_name_report.set_bold()

			title_format_it = workbook.add_format({'align': 'right'})
			title_format_it.set_align('vcenter')
			title_format_it.set_italic()

			title_report_code = workbook.add_format({'align': 'right', 'font_size': '14'})
			title_report_code.set_align('vcenter')
			title_report_code.set_bold()

			common_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
			common_format.set_align('vcenter')
			common_format.set_border(1)

			region_name_format = workbook.add_format({'align': 'left', 'font_color': 'black'})
			region_name_format.set_align('vcenter')
			region_name_format.set_border(1)

			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			sum_pay_format.set_border(1)

			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			digital_format = workbook.add_format({'num_format': '### ### ##0', 'align': 'right'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			digital_format_center = workbook.add_format({'num_format': '### ### ##0', 'align': 'center'})
			digital_format_center.set_border(1)
			digital_format_center.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '# ### ### ##0.00', 'align': 'right'})
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
			sql_sheet.merge_range(f'A1:I{len(stmt_report.splitlines())}', f'{stmt_report}', merge_format)

			worksheet[page_num-1].activate()
			format_worksheet(worksheet=worksheet[page_num-1], common_format=title_format)

			worksheet[page_num-1].write(0, 0, report_name, title_name_report)
			worksheet[page_num-1].write(1, 0, f'За период: {date_first}  -  {date_second}', title_name_report)

			row_cnt = 1
			all_cnt = 0
			shift_row = 3
			cnt_part = 0

			log.info(f'REPORT {report_code}. CREATING REPORT')

			try:
				cursor.execute(stmt_report, dt_from=date_first, dt_to=date_second)
			except oracledb.DatabaseError as e:
				error, = e.args
				log.error(f"ERROR. REPORT {report_code}. error_code: {error.code}, error: {error.message}")
				log.info(f'\n---------\n{stmt_report}\n---------')
				set_status_report(file_name, 3)
				return
			finally:
				log.info(f'REPORT: {report_code}. Выборка из курсора завершена')
			
			log.info(f'REPORT: {report_code}. Формируем выходную EXCEL таблицу')

			records = []
			records = cursor.fetchall()
			#for record in records:
			for record in records:
				col = 1
				worksheet[page_num-1].write(row_cnt+shift_row, 0, all_cnt, digital_format_center)
				for list_val in record:
					if col in (1,3):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, common_format)
					if col in (2,):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, digital_format_center)
					if col in (4,):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, digital_format)
					if col in (5,):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, money_format)
					col+= 1
				row_cnt+= 1
				cnt_part+= 1
				all_cnt+=1
				if (all_cnt//1000000) +1 > page_num:
					page_num=page_num+1
					row_cnt=1
					# ADD a new worksheet
					worksheet.append( workbook.add_worksheet(f'Список {page_num}') )
					# Formatting column and rows, ADD HEADERS
					format_worksheet(worksheet=worksheet[page_num-1], common_format=title_format)
					worksheet[page_num-1].write(0, 0, report_name, title_name_report)
					worksheet[page_num-1].write(1, 0, f'За период: {date_first}-{date_second}', title_name_report)
					

				if cnt_part > 250000:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			now = datetime.datetime.now()
			stop_time = now.strftime("%H:%M:%S")

			for i in range(page_num):
				# Шифр отчета
				worksheet[i].write(0, 0, report_code, title_report_code)
				worksheet[i].write(0, 3, f'Дата формирования: {now.strftime("%d.%m.%Y ")}({s_date} - {stop_time})', title_format_it)

			workbook.close()
			set_status_report(file_name, 2)
			log.info(f'REPORT: {report_code}. Формирование отчета {file_name} завершено ({s_date} - {stop_time}), Загружено {all_cnt} записей')


def thread_report(file_name: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: date_from: {date_first}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('minSO_01.xlsx', '01.10.2022','31.10.2022')
