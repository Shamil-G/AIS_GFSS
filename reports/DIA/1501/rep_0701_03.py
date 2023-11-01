from   db_config import report_db_user, report_db_password, report_db_dsn
import xlsxwriter
import datetime
import oracledb
from   util.logger import log
import os.path
from   model.manage_reports import set_status_report

# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)
# Принят ДИА 14.02.2023

report_name = 'Списочный состав получателей 0701, с ребенком до 3 лет'
report_code = '1501.03'

#document.ridt_id: 6 - Выплаты из ГФСС, 7 - 10% удержания, 8 - удержания из соц.выплат
#document.status:  0 - Документ сформирован на выплату, 1 - Сформирован платеж, 2 - Платеж на выплате
stmt_1 = """
      select last_rfbn_id, last_rfpm_id, last_R_IIN, DEP_IIN, sex, 
	  	 last_appoint_date, last_approve_date, last_stop_date, last_sum_pay
	  from (
      select unique
            first_value(doc.rfbn_id) over(partition by pd.sicid order by doc.pncp_date desc) last_rfbn_id,
            first_value(doc.rfpm_id) over(partition by pd.sicid order by doc.pncp_date desc) last_rfpm_id,
            first_value(p1.rn) over(partition by pd.sicid order by pt.approvedate desc) last_R_IIN,
            p2.rn DEP_IIN,
			case when p2.sex = '0' then 'Ж' when p2.sex = '1' then 'М' else 'N' end as sex, 
			p2.birthdate, 
            first_value(pt.appointdate) over(partition by pd.sicid order by pt.approvedate desc) last_appoint_date,
            first_value(pt.approvedate) over(partition by pd.sicid order by pt.approvedate desc) last_approve_date,
            first_value(pt.stopdate) over(partition by pd.sicid order by pt.approvedate desc) last_stop_date,
            first_value(pt.sum_pay) over(partition by pd.sicid order by pt.approvedate desc) last_sum_pay
      from pnpt_payment pt,
          pnpd_document doc,
          pnpd_payment_dependant pd,
          person p1,
          person p2
      where pt.pnpt_id=doc.source_id
      and doc.pncd_id=p1.sicid
      and pt.pnpt_id=pd.pnpt_id(+)
      and pd.sicid=p2.sicid(+)
      and substr(pt.rfpm_id,1,4) = '0701'
      and doc.pncp_date Between to_date(:dt_from,'yyyy-mm-dd') And to_date(:dt_to,'yyyy-mm-dd')
      and doc.ridt_id in (6,7,8)
	  and doc.status in (0,1,2)
	  and months_between(pt.appointdate, p2.birthdate)<36
	  and pt.appointdate > p2.birthdate
	  ) a
	  where months_between(last_appoint_date, a.birthdate)<36
	  and last_appoint_date > a.birthdate
"""

active_stmt = stmt_1

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)

	worksheet.set_column(0, 0, 7)
	worksheet.set_column(1, 1, 10)
	worksheet.set_column(2, 2, 12)
	worksheet.set_column(3, 3, 14)
	worksheet.set_column(4, 4, 14)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 12)
	worksheet.set_column(9, 9, 14)

	worksheet.write(2, 0, '№', common_format)
	worksheet.write(2, 1, 'Код региона', common_format)
	worksheet.write(2, 2, 'Код выплаты', common_format)
	worksheet.write(2, 3, 'ИИН получателя', common_format)
	worksheet.write(2, 4, 'ИИН иждивенца', common_format)
	worksheet.write(2, 5, 'Пол иждивенца', common_format)
	worksheet.write(2, 6, 'Дата риска', common_format)
	worksheet.write(2, 7, 'Дата назначения', common_format)
	worksheet.write(2, 8, 'Дата окончания', common_format)
	worksheet.write(2, 9, 'Размер СВ', common_format)


def do_report(file_name: str, date_first: str, date_second: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name
	log.info(f'DO REPORT. START {report_code}. DATE_FROM: {date_first}, FILE_PATH: {file_name}')
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

			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			sum_pay_format.set_border(1)
			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			digital_format = workbook.add_format({'num_format': '#0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '# ### ### ##0', 'align': 'right'})
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

			log.info(f'FILE NAME: {file_name}.\nЗагружаем данные за период {date_first} : {date_second}')
			cursor.execute(active_stmt, dt_from=date_first, dt_to=date_second)

			records = cursor.fetchall()
			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (1,2,3,4,5):
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col in (6,7,8):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					if col == 9:
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				row_cnt += 1
				cnt_part += 1
				if cnt_part > 9999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			#worksheet.write(row_cnt+1, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)

			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {file_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			set_status_report(file_name, 2)


def get_file_path(file_name: str, date_first: str, date_second: str):
	full_file_name = f'{file_name}.0701_03.{date_first}_{date_second}.xlsx'
	return full_file_name


def thread_report(file_name: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: date_from: {date_first}, date_to: {date_second}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('0701_02.xlsx', '01.10.2022','31.10.2022')
