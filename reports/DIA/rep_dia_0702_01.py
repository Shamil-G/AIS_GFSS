from   db_config import report_db_user, report_db_password, report_db_dsn
import xlsxwriter
import datetime
import os.path
from   util.logger import log
from   db.connect import report_db_dsn, report_db_username, report_db_password
import oracledb

# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)

report_name = 'Получатели СВут 0702 за период:'
report_code = 'DIA_0702_01'

stmt_itogo = """
select unique ph.rfbn_id, 
       sfa.rfpm_id, 
       sfa.iin, 
       case when sfa.sex = 0 then 'Ж' else 'М' end sex, 
       sfa.risk_date, 
       sfa.date_approve, 
       ph.sum_pay,
       sfa.ksu,
       sfa.kut,
       sfa.sum_avg
from  payment_history ph, sipr_maket_first_approve_2 sfa
where trunc(ph.act_month,'MM') between :dt_from and :dt_to
and   substr(ph.rfpm_id,1,4)='0702'
and   ph.pnpt_id = sfa.pnpt_id
"""
stmt_2 = """
with sum_calc  as(
select sicid,
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
    select /*+ full(si) */
           si.sicid,
           sum(si.sum_pay) sum_pay,
           months_between(si.pay_date,ph.appointdate) num_month
    from si_member_2 si, payment_history ph
    where si.sicid=ph.pncd_id
    and trunc(ph.act_month,'MM') between :dt_from and :dt_to
    and   substr(ph.rfpm_id,1,4)='0702'
    and   months_between(si.pay_date,ph.appointdate) between 1 and 12
    group by sicid, months_between(si.pay_date,ph.appointdate)
)
  group by sicid
)
select unique ph.rfbn_id, 
       sfa.rfpm_id, 
       sfa.iin, 
       case when sfa.sex = 0 then 'Ж' else 'М' end sex, 
       sfa.risk_date, 
       sfa.date_approve, 
       ph.sum_pay,
       sfa.ksu,
       sfa.kut,
       sfa.sum_avg,
       sc.sum_m_1,
       sc.sum_m_2,
       sc.sum_m_3,
       sc.sum_m_4,
       sc.sum_m_5,
       sc.sum_m_6,
       sc.sum_m_7,
       sc.sum_m_8,
       sc.sum_m_9,
       sc.sum_m_10,
       sc.sum_m_11,
       sc.sum_m_12
from  payment_history ph, sipr_maket_first_approve_2 sfa, sum_calc sc
where trunc(ph.act_month,'MM') between :dt_from and :dt_to
and   substr(ph.rfpm_id,1,4)='0702'
and   ph.pnpt_id = sfa.pnpt_id
and   ph.pncd_id = sc.sicid
"""

stmt_3 = """
with sum_calc  as(
    select /*+ Parallel(4) full(si)*/
           si.sicid,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 1 then si.sum_pay else 0 end) as sum_m_1,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 2 then si.sum_pay else 0 end) sum_m_2,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 3 then si.sum_pay else 0 end) sum_m_3,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 4 then si.sum_pay else 0 end) sum_m_4,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 5 then si.sum_pay else 0 end) sum_m_5,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 6 then si.sum_pay else 0 end) sum_m_6,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 7 then si.sum_pay else 0 end) sum_m_7,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 8 then si.sum_pay else 0 end) sum_m_8,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 9 then si.sum_pay else 0 end) sum_m_9,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 10 then si.sum_pay else 0 end) sum_m_10,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 11 then si.sum_pay else 0 end) sum_m_11,
           sum(case when trunc(months_between(:dt_from,si.pay_date)) = 12 then si.sum_pay else 0 end) sum_m_12
    from si_member_2 si
    where months_between(:dt_from, si.pay_date) between 1 and 12
    and   si.pay_date >= add_months(:dt_from , -12)
    and   si.pay_date < :dt_to
    group by sicid
)
select /*+ parallel(4) */ ph.rfbn_id, 
       sfa.rfpm_id, 
       sfa.iin, 
       case when sfa.sex = 0 then 'Ж' else 'М' end sex, 
       sfa.risk_date, 
       sfa.date_approve, 
       ph.sum_pay,
       sfa.ksu,
       sfa.kut,
       sfa.sum_avg,
       sc.sum_m_1, sc.sum_m_2, sc.sum_m_3, sc.sum_m_4,
       sc.sum_m_5, sc.sum_m_6, sc.sum_m_7, sc.sum_m_8,
       sc.sum_m_9, sc.sum_m_10, sc.sum_m_11,sc.sum_m_12
from  payment_history ph, sipr_maket_first_approve_2 sfa, sum_calc sc
where trunc(ph.act_month,'MM') = :dt_from
and   substr(ph.rfpm_id,1,4)='0702'
and   ph.pnpt_id = sfa.pnpt_id
and   ph.pncd_id = sc.sicid(+)
"""

stmt_4 = """
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
        sicid, trunc(months_between(to_date(:dt_from,'YYYY-MM-DD'), trunc(si.pay_date,'MM'))) num_month, si.sum_pay
        from si_member_2 si
        where trunc(months_between(to_date(:dt_from,'YYYY-MM-DD'), trunc(si.pay_date,'MM'))) between 1 and 12
        and   si.pay_date >= add_months( trunc(to_date(:dt_from,'YYYY-MM-DD'), 'MM') , -12)
        and   si.pay_date < trunc(to_date(:dt_from,'YYYY-MM-DD'),'MM')
    )
    group by sicid
)
select /*+ Parallel(8) */
       ph.rfbn_id, 
       sfa.rfpm_id, 
       --sfa.iin, 
       p.rn,
       case when sfa.sex = 0 then 'Ж' else 'М' end sex, 
       sfa.risk_date, 
       sfa.date_approve,
       sfa.date_stop, 
       ph.sum_pay,
       sfa.ksu,
       sfa.kut,
       sfa.sum_avg,
       sc.sum_m_1, sc.sum_m_2, sc.sum_m_3, sc.sum_m_4,
       sc.sum_m_5, sc.sum_m_6, sc.sum_m_7, sc.sum_m_8,
       sc.sum_m_9, sc.sum_m_10, sc.sum_m_11,sc.sum_m_12
from  payment_history ph, sipr_maket_first_approve_2 sfa, sum_calc sc
      ,person p
where trunc(ph.act_month,'MM') = trunc(to_date(:dt_from,'YYYY-MM-DD'), 'MM')
and   substr(ph.rfpm_id,1,4)='0702'
and   ph.pnpt_id = sfa.pnpt_id(+)
and   ph.pncd_id = sc.sicid(+)
and   ph.pncd_id = p.sicid
"""

active_stmt = stmt_4

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
	worksheet.set_column(8, 8, 18)
	worksheet.set_column(9, 9, 8)
	worksheet.set_column(10, 10, 8)
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
	worksheet.merge_range('K3:K4', 'КУТ', common_format)
	worksheet.merge_range('L3:L4', 'СМД', common_format)
	worksheet.merge_range('M3:X3', 'СО до отчетного периода', common_format)
	worksheet.write(3, 12, '1', common_format)
	worksheet.write(3, 13, '2', common_format)
	worksheet.write(3, 14, '3', common_format)
	worksheet.write(3, 15, '4', common_format)
	worksheet.write(3, 16, '5', common_format)
	worksheet.write(3, 17, '6', common_format)
	worksheet.write(3, 18, '7', common_format)
	worksheet.write(3, 19, '8', common_format)
	worksheet.write(3, 20, '9', common_format)
	worksheet.write(3, 21, '10', common_format)
	worksheet.write(3, 22, '11', common_format)
	worksheet.write(3, 23, '12', common_format)


def do_report(file_name: str, date_from: str):
	print(f'MAKE REPORT started...')
	if os.path.isfile(file_name):
		print(f'Отчет уже существует {file_name}')
		log.info(f'Отчет уже существует {file_name}')
		return file_name
	else:
		#cx_Oracle.init_oracle_client(lib_dir='c:/instantclient_21_3')
		#cx_Oracle.init_oracle_client(lib_dir='/home/aktuar/instantclient_21_8')
		if report_db_dsn:
			dsn = report_db_dsn
			username = report_db_username
			password = report_db_password  
		else:
			dsn="172.16.17.12/gfss"
			username = 'sswh'
			password = 'sswh'
	with oracledb.connect(user=report_db_user, password=report_db_password, dsn=report_db_dsn, encoding="UTF-8") as connection:
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
			worksheet.write(1, 0, f'За период: {date_from}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0
			m_val = [0]

			log.info(f'{file_name}. Загружаем данные за период {date_from}')
			cursor.execute(active_stmt, date_from=date_from)

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
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0
				row_cnt += 1
			#worksheet.write(row_cnt+shift_row, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)

			worksheet.write(row_cnt + shift_row, 8, m_val[0], money_format)
			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {file_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			return file_name


def get_file_path(file_name: str, date_from: str):
	format = '%Y-%m-%d'
	dt = datetime.datetime.strptime(date_from, format)
	dt_format = dt.strftime('%Y-%m-01')
	full_file_name = f'{file_name}.0702_01.{dt_format}.xlsx'
	return full_file_name


def thread_report(file_name: str, date_from: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: rfpm_id: 0702, date_from: {date_from}')
	threading.Thread(target=do_report, args=(file_name, date_from), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    #make_report('0701', '01.10.2022','31.10.2022')
    do_report('01.01.2023')
