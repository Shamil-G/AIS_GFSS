from   db_config import report_db_user, report_db_password, report_db_dsn
import xlsxwriter
import datetime
from   util.logger import log
import oracledb
import os.path
from   model.manage_reports import set_status_report

report_name = 'Списочная часть по платежам, рассчитанным от дохода менее 1 МЗП'
report_code = 'minCO.01'

# 
#document.status:  0 - Документ сформирован на выплату, 1 - Сформирован платеж, 2 - Платеж на выплате
stmt_load = "begin sswh.load_min_so_history.make; end;"

stmt_report = """
			select
				  nvl(rb.RFBN_ID, 'нет') rfbn_area, --Код района
				  rb.NAME name_area,	--Район
				  m.p_rnn,				--БИН/ИИН предприятия
				  nvl(n.name_ip, n.fio) name_org,	--Наименование предприятия
				  m.cnt_worker,			-- Общее количество сотрудников
				  p.rn iin,
				  m.PAY_MONTH,
				  m.sum_pay,
				  min_so(m.PAY_MONTH) as base_size,
				  min_so(m.PAY_MONTH) - m.sum_pay as debt
			from min_so_history m, person p
				 , rfrr_id_region r
				 , nk_minfin_iin n
				 , rfbn_branch_site rb
			where trunc(m.ctrl_date,'MM')=trunc(to_date(:control_month,'YYYY-MM-DD'),'MM')
			and   trunc(m.pay_month,'MM') >= add_months(trunc(m.ctrl_date,'MM'), -13)
			and   m.p_rnn = r.id(+)
			and   m.p_rnn = n.iin(+)
			and   m.sicid = p.sicid
			and   r.rfbn_id = rb.RFBN_ID(+)
			AND   coalesce(r.typ, 'I') = 'I'
			order by 1,2,3
	"""


def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 14)
	#worksheet.set_row(3, 48)

	worksheet.set_column(0, 0, 9)
	worksheet.set_column(1, 1, 12)
	worksheet.set_column(2, 2, 48)
	worksheet.set_column(3, 3, 14)
	worksheet.set_column(4, 4, 120)
	worksheet.set_column(5, 5, 18)
	worksheet.set_column(6, 6, 14)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 14)
	worksheet.set_column(9, 9, 12)
	worksheet.set_column(10, 10, 16)

	worksheet.write(2,0, '1', common_format)
	worksheet.write(2,1, '2', common_format)
	worksheet.write(2,2, '3', common_format)
	worksheet.write(2,3, '4', common_format)
	worksheet.write(2,4, '5', common_format)
	worksheet.write(2,5, '6', common_format)
	worksheet.write(2,6, '7', common_format)
	worksheet.write(2,7, '8', common_format)
	worksheet.write(2,8, '9', common_format)
	worksheet.write(2,9, '10', common_format)
	worksheet.write(2,10, '11', common_format)
	worksheet.write(3,0, '№', common_format)
	worksheet.write(3,1, 'Код района', common_format)
	worksheet.write(3,2, 'Район', common_format)
	worksheet.write(3,3, 'БИН/ИИН предприятия', common_format)
	worksheet.write(3,4, 'Наименование предприятия', common_format)
	worksheet.write(3,5, 'Общее количество сотрудников за которых поступили СО', common_format)
	worksheet.write(3,6, 'ИИН сотрудника', common_format)
	worksheet.write(3,7, 'Период платежа', common_format)
	worksheet.write(3,8, 'Платежи менее 1 МЗП, за период', common_format)
	worksheet.write(3,9, 'Мин. ставка СО', common_format)
	worksheet.write(3,10, 'Недоплачено до мин.ставки СО 11=(10-9)', common_format)


def do_report(file_name: str, date_first: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name
	log.info(f'DO REPORT. START {report_code}. DATE_FROM: {date_first}, FILE_PATH: {file_name}')
	with oracledb.connect(user=report_db_user, password=report_db_password, dsn=report_db_dsn) as connection:
		with connection.cursor() as cursor:
			workbook = xlsxwriter.Workbook(file_name)

			title_format = workbook.add_format({'bg_color': '#D1FFFF', 'align': 'center', 'font_color': 'black'})
			#title_format = workbook.add_format({'bg_color': '#C5FFFF', 'align': 'center', 'font_color': 'black'})
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

			region_name_format = workbook.add_format({'align': 'left', 'font_color': 'black'})
			region_name_format.set_align('vcenter')
			region_name_format.set_border(1)

			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			sum_pay_format.set_border(1)

			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			date_format_italic = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format_italic.set_italic()
			#date_format_italic.set_border(0)

			digital_format = workbook.add_format({'num_format': '#0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '# ### ### ##0', 'align': 'right'})
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
			worksheet[page_num-1].write(1, 0, f'За период: {date_first}', title_name_report)

			row_cnt = 1
			all_cnt=1
			shift_row = 3
			cnt_part = 0

			log.info(f'REPORT {report_code}. LOAD: {stmt_load}')
			cursor.execute(stmt_load)

			log.info(f'REPORT {report_code}. CREATE REPORT')
			cursor.execute(stmt_report, control_month=date_first)

			log.info(f'REPORT: {report_code}. Формируем выходную EXCEL таблицу')
			#cursor.execute(stmt_3)

			records = []
			records = cursor.fetchall()
			#for record in records:
			for record in records:
				col = 1
				worksheet[page_num-1].write(row_cnt+shift_row, 0, all_cnt, digital_format)
				for list_val in record:
					if col in (2,4):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, region_name_format)
					if col in (1,3,5,6):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, digital_format)
					if col in (7,):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, date_format)
					if col in (8,9,10):
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
					worksheet[page_num-1].write(1, 0, f'За период: {date_first}', title_name_report)
					

				if cnt_part > 250000:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			for i in range(page_num):
				# Шифр отчета
				worksheet[i].write(0, 9, report_code, title_name_report)
				worksheet[i].write(1, 9, f'Дата формирования: {now}', date_format_italic)

			workbook.close()
			set_status_report(file_name, 2)
			log.info(f'REPORT: {report_code}. Формирование отчета {file_name} завершено: {now}, Загруено {all_cnt} записей')


def thread_report(file_name: str, date_first: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: date_from: {date_first}')
	threading.Thread(target=do_report, args=(file_name, date_first), daemon=True).start()
	return {"status": 1, "file_path": file_name}


def get_file_full_name(part_name, params):
	if 'date_first' in params:
		trunc_date = datetime.datetime.strptime(params['date_first'], '%Y-%m-%d').replace(day=1)
		str_trunc_date = datetime.datetime.strftime(trunc_date, '%Y-%m-%d')
		return f'{part_name}.{str_trunc_date}.xlsx'


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('minSO_01.xlsx', '01.10.2022','31.10.2022')
