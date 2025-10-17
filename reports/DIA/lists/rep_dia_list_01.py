from configparser import ConfigParser
import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   model.manage_reports import set_status_report


report_name = 'Список получателей со статусом '
report_code = 'LST.01'

stmt_1 = """
SELECT /*+parallel(8)*/
    substr(st.brid,1,2) AS region,
    b.name,
    pay.pc,
    p.iin,
    p.lastname||' '||p.firstname||' '||p.middlename as fio,
    sd.risk_date,
    st.dat,
    pay.d_naz,
    pay.nsum,
    sd.sum_all,
    sd.date_calc,
    sd.sum_dop
FROM ss_m_sol_st st, ss_m_sol sol, 
	 ss_m_pay pay, ss_data sd, ss_z_doc z,
     branch b, person p
WHERE st2 = :st_status
and sol.id = st.sid
and sol.id = pay.sid
and sol.id = z.id
and sol.id = sd.sipr_id
and sol.sicid = p.sicid
and substr(st.brid,1,2)||'00'=b.rfbn_id
and z.id_tip = 'NEW'
and st.host != 'SS_TO_EM5'
and st.dat >= to_date(:dt_from,'YYYY-MM-DD')
and st.dat < to_date(:dt_to,'YYYY-MM-DD') + 1
and st.p_pc like '%'||:rfpm_id||'%'
order by 1,3,5
"""

active_stmt = stmt_1

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 28)
	worksheet.set_row(3, 18)

	worksheet.set_column(0, 0, 8)
	worksheet.set_column(1, 1, 32)
	worksheet.set_column(2, 2, 14)
	worksheet.set_column(3, 3, 14)
	worksheet.set_column(4, 4, 42)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 16)
	worksheet.set_column(9, 9, 16)
	worksheet.set_column(10, 10, 12)
	worksheet.set_column(11, 11, 16)

	worksheet.write(3,0, '1', common_format)
	worksheet.write(3,1, '2', common_format)
	worksheet.write(3,2, '3', common_format)
	worksheet.write(3,3, '4', common_format)
	worksheet.write(3,4, '5', common_format)
	worksheet.write(3,5, '6', common_format)
	worksheet.write(3,6, '7', common_format)
	worksheet.write(3,7, '8', common_format)
	worksheet.write(3,8, '9', common_format)
	worksheet.write(3,9, '10', common_format)
	worksheet.write(3,10, '11', common_format)

	worksheet.write(2,0, 'Код региона', common_format)
	worksheet.write(2,1, 'Наименование региона', common_format)
	worksheet.write(2,2, 'Код выплаты', common_format)
	worksheet.write(2,3, 'ИИН', common_format)
	worksheet.write(2,4, 'ФИО', common_format)
	worksheet.write(2,5, 'Дата риска', common_format)
	worksheet.write(2,6, 'Дата назначения', common_format)
	worksheet.write(2,7, 'Дата постановки на выплату', common_format)
	worksheet.write(2,8, 'Назначенный размер', common_format)
	worksheet.write(2,9, 'Сумма выплаты', common_format)
	worksheet.write(2,10, 'Дата расчета', common_format)
	worksheet.write(2,11, 'Доп.сумма', common_format)


def do_report(file_name: str, date_first: str, date_second: str, rfpm_id: str, status: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name

	s_date = datetime.datetime.now().strftime("%H:%M:%S")

	log.info(f'DO REPORT. START {report_code}. DATE_FROM: {date_first}, DATE_TO: {date_second}, FILE_PATH: {file_name}')
	
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

			name_common_format = workbook.add_format({'align': 'left', 'font_color': 'black'})
			name_common_format.set_align('vcenter')
			name_common_format.set_border(1)

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

			worksheet.write(0, 0, f'{report_name}"{status}"', title_name_report)
			worksheet.write(1, 0, f'Период расчёта: с {date_first} по {date_second}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0
			m_val = [0]

			log.info(f'{file_name}. Загружаем данные с {date_first} по {date_second}')
			cursor.execute(active_stmt, dt_from=date_first,dt_to=date_second, st_status=status, rfpm_id=rfpm_id)

			records = cursor.fetchall()
			
			#for record in records:
			for record in records:
				col = 0
				# worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (1,4):
						worksheet.write(row_cnt+shift_row, col, list_val, name_common_format)
					if col in (0,2,3):
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col in (5,6,7,10):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					if col in (8,9,11):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				cnt_part += 1
				if cnt_part > 9999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0
				row_cnt += 1

			# Шифр отчета
			worksheet.write(0, 9, report_code, title_report_code)
			#
			now = datetime.datetime.now()
			stop_time = now.strftime("%H:%M:%S")

			worksheet.write(1, 9, f'Дата формирования: {now.strftime("%d.%m.%Y ")}({s_date} - {stop_time})', title_format_it)
			#
			workbook.close()
			log.info(f'Формирование отчета {file_name} завершено ({s_date} - {stop_time}). Загружено {row_cnt-1} записей')
			set_status_report(file_name, 2)


def thread_report(file_name: str, date_first: str, date_second: str, rfpm_id: str, status: str):
	import threading
	log.info(f'THREAD REPORT. DATE BETWEEN REPORT: {date_first} - {date_second}, FILE_NAME: {file_name}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second, rfpm_id, status), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    #make_report('0701', '01.10.2022','31.10.2022')
    do_report('01.01.2023', '15.01.2023')
