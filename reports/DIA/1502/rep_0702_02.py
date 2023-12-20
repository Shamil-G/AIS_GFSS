import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   db_config import report_db_user, report_db_password, report_db_dsn
from   model.call_report import set_status_report


report_name = 'Получатели СВут (0702)'
report_code = '1502.02'

stmt_create = """
select 
      rfbn_id, rfpm_id, 
	  iin, 
	  birthdate,
      sex, 
      age,
      appointdate, date_approve, stopdate, 
      last_pay_sum,  
      ksu, kut, sum_avg, sum_all,
      knp,
      sum(p_month) curr_pay_month,
      sum(all_month) all_pay_month
from (
    select 
      b.rfbn_id, b.rfpm_id, 
	  iin, 
	  birthdate,
      sex, 
      age,
      b.appointdate, b.date_approve, b.stopdate, 
      b.last_pay_sum,  
      b.ksu, b.kut, b.sum_avg, b.sum_all,
      b.knp,
      case when b.pay_month>=to_date('2023-01-01','YYYY-MM-DD') then 1 else 0 end p_month,
      case when b.pay_month is null then 0 else 1 end all_month	  
    from (
        select unique 
          a.rfbn_id, a.rfpm_id, p.rn as iin, p.birthdate,
          case when p.sex=0 then 'Ж' else 'M' end as sex, 
          floor( months_between(a.risk_date, p.birthdate) / 12 ) age,
          a.appointdate, a.date_approve, a.stopdate, 
          a.last_pay_sum,  
          a.ksu, a.kut, a.sum_avg, a.sum_all,
          a.knp,
          si.pay_month
        from (              
          SELECT /*+parallel(4)*/
               unique d.pncd_id,
               FIRST_VALUE(pp.rfbn_id) OVER(PARTITION BY D.PNCD_ID ORDER BY D.PNCP_DATE DESC) rfbn_id,
               FIRST_VALUE(D.rfpm_id) OVER(PARTITION BY D.PNCD_ID ORDER BY D.PNCP_DATE DESC) rfpm_id,
               FIRST_VALUE(pp.appointdate) OVER(PARTITION BY D.PNCD_ID ORDER BY pp.appointdate DESC) appointdate,
               FIRST_VALUE(sipr.risk_date) OVER(PARTITION BY D.PNCD_ID ORDER BY sipr.risk_date DESC) risk_date,
               FIRST_VALUE(sipr.date_approve) OVER(PARTITION BY sipr.iin ORDER BY sipr.date_approve DESC) date_approve,
               FIRST_VALUE(pp.stopdate) OVER(PARTITION BY D.PNCD_ID ORDER BY D.PNCP_DATE DESC) stopdate,
               FIRST_VALUE(case when D.pay_sum>0 then D.pay_sum else d.sum_debt end) OVER(PARTITION BY D.PNCD_ID ORDER BY D.PNCP_DATE DESC) last_pay_sum,
               sipr.kut, sipr.ksu, sipr.sum_avg, sipr.sum_all,
               FIRST_VALUE(D.knp) OVER(PARTITION BY D.PNCD_ID ORDER BY D.PNCP_DATE DESC) KNP
          FROM  PNPD_DOCUMENT D, 
                sipr_maket_first_approve_2 sipr,
                PNPT_PAYMENT PP
          WHERE D.SOURCE_ID = PP.PNPT_ID(+)
          and   d.source_id = sipr.pnpt_id(+)
          AND   coalesce(D.KNP,'000')!='010'
          AND   D.PNCP_DATE BETWEEN to_date(:date_first,'YYYY-MM-DD') AND to_date(:date_second,'YYYY-MM-DD')
          AND   substr(D.RFPM_ID,1,4) = '0702'
          AND   D.RIDT_ID IN (4, 6, 7, 8)
          AND   D.STATUS IN (0, 1, 2, 3, 5, 7)
          AND   D.PNSP_ID > 0
        ) a, person p, si_member_2 si
        where a.pncd_id = si.sicid(+) 
        and   a.pncd_id = p.sicid
		and	  si.knp(+) = '012'
        and   si.pay_date(+) BETWEEN to_date(:date_first,'YYYY-MM-DD') AND to_date(:date_second,'YYYY-MM-DD')  
    ) b
)
group by 
      rfbn_id, rfpm_id, 
	  iin, 
	  birthdate,
      sex, 
      age,
      appointdate, date_approve, stopdate, 
      last_pay_sum,  
      ksu, kut, sum_avg, sum_all,
      knp
order by rfbn_id, rfpm_id, iin
"""

active_stmt = stmt_create

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 28)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 24)
	worksheet.set_row(3, 24)

	worksheet.set_column(0, 0, 9)
	worksheet.set_column(1, 1, 14)
	worksheet.set_column(2, 2, 14)
	worksheet.set_column(3, 3, 14)
	worksheet.set_column(4, 4, 12)
	worksheet.set_column(5, 5, 8)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 12)
	worksheet.set_column(9, 9, 12)
	worksheet.set_column(10, 10, 18)
	worksheet.set_column(11, 11, 8)
	worksheet.set_column(12, 12, 8)
	worksheet.set_column(13, 13, 12)
	worksheet.set_column(14, 14, 21)
	worksheet.set_column(15, 15, 7)
	worksheet.set_column(16, 16, 12)
	worksheet.set_column(17, 17, 12)

	worksheet.merge_range('A3:A4', '№', common_format)
	worksheet.merge_range('B3:B4', 'Код региона', common_format)
	worksheet.merge_range('C3:C4', 'Код выплаты', common_format)
	worksheet.merge_range('D3:D4', 'ИИН получателя', common_format)
	worksheet.merge_range('E3:E4', 'Дата рождения', common_format)	
	worksheet.merge_range('F3:F4', 'Пол', common_format)
	worksheet.merge_range('G3:G4', 'Возраст на дату риска', common_format)
	worksheet.merge_range('H3:H4', 'Дата риска', common_format)
	worksheet.merge_range('I3:I4', 'Дата назначения', common_format)
	worksheet.merge_range('J3:J4', 'Дата окончания', common_format)
	worksheet.merge_range('K3:K4', 'Размер СВ', common_format)
	worksheet.merge_range('L3:L4', 'КСУ', common_format)
	worksheet.merge_range('M3:M4', 'КУТ', common_format)
	worksheet.merge_range('N3:N4', 'СМД', common_format)
	worksheet.merge_range('O3:O4', 'Сумма первой назначенной выплаты', common_format)
	worksheet.merge_range('P3:P4', 'КНП', common_format)
	worksheet.merge_range('Q3:Q4', 'Периодов в выбранном диапазоне', common_format)
	worksheet.merge_range('R3:R4', 'Всего периодов', common_format)

def do_report(file_name: str, date_first: str, date_second: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name
	begin_report = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
	#cx_Oracle.init_oracle_client(lib_dir='c:/instantclient_21_3')
	#cx_Oracle.init_oracle_client(lib_dir='/home/aktuar/instantclient_21_8')
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
			worksheet.write(1, 0, f'За период: {date_first} - {date_second}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0
			m_val = [0]

			log.info(f'{file_name}. Загружаем данные за период {date_first} - {date_second}')
			cursor.execute(active_stmt, date_first=date_first, date_second=date_second)

			records = cursor.fetchall()

			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col in (1,2,3,6,15,16,17):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col in(5,):
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col in (4,7,8,9):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					if col in (10,11,12,13,14):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					# ADD to SUMMARY
					# if col in (9):
					# 	m_val[0] = m_val[0] + list_val
					col += 1
				cnt_part += 1
				if cnt_part > 24999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0
				row_cnt += 1

			# SUMMARY
			# worksheet.write(row_cnt + shift_row, 10, m_val[0], money_format)

			finish_report = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			worksheet.write(1, 15, f'Дата отчета: {begin_report} - {finish_report}', date_format_it)

			workbook.close()
			log.info(f'Формирование отчета {file_name} завершено. {begin_report} - {finish_report}')
			set_status_report(file_name, 2)
			return file_name


def get_file_path(file_name: str, date_first: str, date_second: str):
	full_file_name = f'{file_name}.{report_code}.{date_first}-{date_second}.xlsx'
	return full_file_name


def thread_report(file_name: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: rfpm_id: 0702, date_first: {date_first}, date_second: {date_second}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    #make_report('0701', '01.10.2022','31.10.2022')
    do_report('01.01.2023')
