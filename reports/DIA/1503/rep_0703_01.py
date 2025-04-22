from configparser import ConfigParser
import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   model.call_report import set_status_report

# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)

report_name = 'СО после окончания СВпр, в градации по месяцам после даты окончания выплаты'
report_code = '1503.01'

stmt_1 = """
with sum_calc  as(
    select /*+ Parallel(8) full(si)*/
           sicid,
           sum(case when num_month = 1 then sum_pay else 0 end) as sum_m_1,
           sum(case when num_month = 2 then sum_pay else 0 end) sum_m_2,
           sum(case when num_month = 3 then sum_pay else 0 end) sum_m_3,
           sum(case when num_month = 4 then sum_pay else 0 end) sum_m_4,
           sum(case when num_month = 5 then sum_pay else 0 end) sum_m_5,
           sum(case when num_month = 6 then sum_pay else 0 end) sum_m_6,
           sum(case when num_month = 7 then sum_pay else 0 end) sum_m_7,
           sum(case when num_month = 8 then sum_pay else 0 end) sum_m_8,
           sum(case when num_month = 9 then sum_pay else 0 end) sum_m_9,
           sum(case when num_month = 10 then sum_pay else 0 end) sum_m_10,
           sum(case when num_month = 11 then sum_pay else 0 end) sum_m_11,
           sum(case when num_month = 12 then sum_pay else 0 end) sum_m_12
    from (
        select /*+ full(si)*/
        sicid, trunc( months_between(trunc(si.pay_month,'MM'), to_date(:dt_from,'YYYY-MM-DD') )) num_month, si.sum_pay
        from si_member_2 si
        where si.pay_date > to_date(:dt_from,'YYYY-MM-DD')
	    and   si.knp='012'
        and   si.pay_date <= add_months( trunc(to_date(:dt_from,'YYYY-MM-DD'), 'MM'), 12 ) 
    )
    group by sicid
)
select /*+ Parallel(8) */
       ph.rfbn_id, 
       sfa.rfpm_id, 
       --sfa.iin, 
       p.iin,
       case when sfa.sex = 0 then 'Ж' else 'М' end sex, 
       sfa.risk_date, 
       sfa.date_approve,
       sfa.date_stop, 
       ph.sum_pay,
       sfa.ksu,
       sfa.sum_avg,
       sc.sum_m_1, sc.sum_m_2, sc.sum_m_3, sc.sum_m_4,
       sc.sum_m_5, sc.sum_m_6, sc.sum_m_7, sc.sum_m_8,
       sc.sum_m_9, sc.sum_m_10, sc.sum_m_11,sc.sum_m_12
from  payment_history ph, sipr_maket_first_approve_2 sfa, sum_calc sc
      ,person p
where trunc(ph.act_month,'MM') = trunc(to_date(:dt_from,'YYYY-MM-DD'), 'MM')
and   trunc(sfa.date_stop, 'MM') = trunc(to_date(:dt_from,'YYYY-MM-DD'), 'MM')
and   substr(ph.rfpm_id,1,4)='0703'
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
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 14)
	worksheet.set_column(9, 9, 8)
	worksheet.set_column(10, 10, 14)
	worksheet.set_column(11, 11, 14)
	worksheet.set_column(12, 12, 14)
	worksheet.set_column(13, 13, 14)
	worksheet.set_column(14, 14, 14)
	worksheet.set_column(15, 15, 14)
	worksheet.set_column(16, 16, 14)
	worksheet.set_column(17, 17, 14)
	worksheet.set_column(18, 18, 14)
	worksheet.set_column(19, 19, 14)
	worksheet.set_column(20, 20, 14)
	worksheet.set_column(21, 21, 14)
	worksheet.set_column(22, 22, 14)
	worksheet.set_column(23, 23, 14)

	worksheet.merge_range('A3:A4', '№', common_format)
	worksheet.merge_range('B3:B4', 'Код региона', common_format)
	worksheet.merge_range('C3:C4', 'Код выплаты', common_format)
	worksheet.merge_range('D3:D4', 'ИИН получателя', common_format)
	worksheet.merge_range('E3:E4', 'Пол', common_format)
	worksheet.merge_range('F3:F4', 'Дата риска', common_format)
	worksheet.merge_range('G3:G4', 'Дата назначения', common_format)
	worksheet.merge_range('H3:H4', 'Дата окончания', common_format)
	worksheet.merge_range('I3:I4', 'Размер СВ', common_format)
	worksheet.merge_range('J3:J4', 'КСУ', common_format)
	#worksheet.merge_range('K3:K4', 'КУТ', common_format)
	worksheet.merge_range('K3:K4', 'СМД', common_format)
	worksheet.merge_range('L3:W3', 'СО после риска', common_format)
	worksheet.write(3, 11, '1', common_format)
	worksheet.write(3, 12, '2', common_format)
	worksheet.write(3, 13, '3', common_format)
	worksheet.write(3, 14, '4', common_format)
	worksheet.write(3, 15, '5', common_format)
	worksheet.write(3, 16, '6', common_format)
	worksheet.write(3, 17, '7', common_format)
	worksheet.write(3, 18, '8', common_format)
	worksheet.write(3, 19, '9', common_format)
	worksheet.write(3, 20, '10', common_format)
	worksheet.write(3, 21, '11', common_format)
	worksheet.write(3, 22, '12', common_format)


def do_report(file_name: str, date_first: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет {report_code} уже существует: {file_name}')
		return file_name

	s_date = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
	
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
			worksheet.write(1, 0, f'C даты: {date_first}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0
			m_val = [0]

			log.info(f'Выполняем Execute для отчета: {report_code}')
			try:
				cursor.execute(active_stmt, dt_from=date_first)
			except oracledb.DatabaseError as e:
				error, = e.args
				log.error(f"ERROR. REPORT {report_code}. error_code: {error.code}, error: {error.message}\n{stmt_report}")
				set_status_report(file_name, 3)
				return
			finally:
				log.info(f'REPORT: {report_code}. Execute выполнен')
				
			log.info(f'Выполняем FetchAll для отчета: {report_code}')
			records = cursor.fetchall()
			
			#for record in records:
			log.info(f'Для отчета: {report_code} выбираем записи из курсора за период {date_first}')
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (1,2,3):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col == 4:
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col in (5,6,7):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					if col in (8,9,10,11):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
						if col == 8:
							m_val[0] = m_val[0] + int(list_val)
					if col in range(12,24):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				cnt_part += 1
				if cnt_part > 9999:
					log.info(f'В отчет {report_code} загружено {row_cnt} записей')
					cnt_part = 0
				row_cnt += 1

			worksheet.write(row_cnt + shift_row, 8, m_val[0], money_format)

			#worksheet.write(row_cnt+shift_row, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)
			worksheet.write(0, 11, report_code, title_name_report)

			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			worksheet.write(1, 10, f'Дата отчета: {s_date} - {now}', date_format_it)

			workbook.close()
			set_status_report(file_name, 2)

			log.info(f'Формирование отчета {file_name} завершено: {s_date} - {now}. Загружено {row_cnt} записей')


def thread_report(file_name: str, date_first: str):
	import threading
	log.info(f'THREAD REPORT. DATE FOR REPORT: {date_first}, FILE_NAME: {file_name}')
	threading.Thread(target=do_report, args=(file_name, date_first), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    #make_report('0701', '01.10.2022','31.10.2022')
    do_report('01.01.2023')
