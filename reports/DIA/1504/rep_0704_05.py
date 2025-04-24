from configparser import ConfigParser
# from   db_config import report_db_user, report_db_password, report_db_dsn
import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   model.call_report import set_status_report

# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)

report_name = 'Получатели СВбр с назначенными выплатами более 3 млн. тенге'
report_code = '1504.3M'

stmt_create = """
with init_date as (
   select trunc(to_date(:date_first,'YYYY-mm-dd'),'YYYY') first_date, 3000000 as threshold from dual
)
, list_date as(
     select first_date,
            add_months(first_date, 36) last_date,
            threshold
     from init_date
)
select substr(s.rfbn_id,1,2),
       b.NAME,
       trunc(s.date_approve,'DD') dapprove,
       s.sum_all,
       p.iin,
       p.lastname||' '||p.firstname||' '||p.middlename
from sipr_maket_first_approve_2 s,
     person p,
     rfbn_branch b,
	 list_date ld
where s.date_approve>=ld.first_date
and s.date_approve<ld.last_date
and s.sum_all>=ld.threshold
and s.sicid = p.sicid
and substr(s.rfbn_id,1,2)=substr(b.RFBN_ID,1,2)
and substr(b.RFBN_ID,3)='00'
order by 1,3
"""

active_stmt = stmt_create

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 28)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 24)
	worksheet.set_row(3, 24)

	worksheet.set_column(0, 0, 9)
	worksheet.set_column(1, 1, 8)
	worksheet.set_column(2, 2, 32)
	worksheet.set_column(3, 3, 12)
	worksheet.set_column(4, 4, 16)
	worksheet.set_column(5, 5, 16)
	worksheet.set_column(6, 6, 48)

	worksheet.merge_range('A3:A4', '№', common_format)
	worksheet.merge_range('B3:B4', 'Код региона', common_format)
	worksheet.merge_range('C3:C4', 'Наименование региона', common_format)
	worksheet.merge_range('D3:D4', 'Дата назначения', common_format)
	worksheet.merge_range('E3:E4', 'Назначенная сумма', common_format)
	worksheet.merge_range('F3:F4', 'ИИН получателя', common_format)
	worksheet.merge_range('G3:G4', 'ФИО', common_format)


def do_report(file_name: str, date_first: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name

	s_date = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S")

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

			name_format = workbook.add_format({'align': 'left', 'font_color': 'black'})
			name_format.set_align('vcenter')
			name_format.set_border(1)

			name_format_r = workbook.add_format({'align': 'right', 'font_color': 'black'})
			name_format_r.set_align('vcenter')
			name_format_r.set_bold()

			common_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
			common_format.set_align('vcenter')
			common_format.set_border(1)

			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			sum_pay_format.set_border(1)

			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			name_format_r_it = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'right'})
			name_format_r_it.set_align('vcenter')
			name_format_r_it.set_italic()

			digital_format = workbook.add_format({'num_format': '# ### ##0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format_center = workbook.add_format({'num_format': '# ### ##0.00', 'align': 'center'})
			money_format_center.set_border(1)
			money_format_center.set_align('vcenter')

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
			sql_sheet.merge_range('A1:I30', active_stmt, merge_format)

			worksheet.activate()
			format_worksheet(worksheet=worksheet, common_format=title_format)

			worksheet.write(0, 0, report_name, title_name_report)
			worksheet.write(1, 0, f'За период с:  {date_first}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0

			log.info(f'{file_name}. Загружаем данные за период с {date_first}')
			cursor.execute(active_stmt, date_first=date_first)

			records = cursor.fetchall()

			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (2,6):
						worksheet.write(row_cnt+shift_row, col, list_val, name_format)
					if col == 3:
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					if col == 4:
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					if col in (1,5):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					col += 1
				cnt_part += 1
				row_cnt += 1
			#
			worksheet.write(0, 6, report_code, name_format_r)

			now_time = datetime.datetime.now().strftime("%H:%M:%S)")
			stop_time = now.strftime("%H:%M:%S")

			worksheet.write(1, 6, f'Дата формирования: {s_date} - {now_time}', name_format_r_it)

			workbook.close()
			set_status_report(file_name, 2)

			log.info(f'Формирование отчета {file_name} завершено: {s_date} - {now_time}. Загружено {row_cnt} записей')


def thread_report(file_name: str, date_first: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: rfpm_id: 0702, date_first: {date_first}')
	threading.Thread(target=do_report, args=(file_name, date_first), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    #make_report('0701', '01.10.2022','31.10.2022')
    do_report('01.01.2023')
