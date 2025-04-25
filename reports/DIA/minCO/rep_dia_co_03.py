from configparser import ConfigParser
import xlsxwriter
import datetime
from   util.logger import log
import oracledb
import os.path
from   model.manage_reports import set_status_report
from   util.trunc_date import get_quarter_number

report_name = 'Уплаченные СО в размере менее 1 МЗП за квартал. Для проведения информационно-разъяснительной работы'
report_code = 'minCO.03'

stmt_report = """
with 
dm as(
  select to_date('01.'||lpad((n_q)*3-2,2,'0')||'.'||n_year,'dd.mm.yyyy') as f_month,
         to_date('01.'||lpad((n_q)*3-1,2,'0')||'.'||n_year,'dd.mm.yyyy') as s_month,
         to_date('01.'||lpad((n_q)*3,2,'0')||'.'||n_year,'dd.mm.yyyy') as t_month,
         n_year
  from (
        select
               ceil(extract(month from to_date(:first_date,'yyyy-mm-dd'))/3) n_q,
               extract(year from to_date(:first_date,'yyyy-mm-dd')) n_year
        from dual
       )
)
, aq_src as (
    SELECT /*+PARALLEL (2)*/ 
           trunc(pay_date, 'MM') pd, 
           sicid, 
           p_rnn, 
           pay_month, 
           SUM(cnt_mzp) sum_mzp, 
           SUM(sum_pay) sp 
    FROM si_member_2, dm
    WHERE pay_date >= dm.f_month
    AND pay_date < add_months(dm.f_month,3) 
    AND pay_month < add_months(dm.f_month,3)
    AND pay_month >= to_date('2013-02-01','yyyy-mm-dd')  -- 1 МЗП с февраля 2013 года
    AND knp in ('012')
    AND p_rnn !='160440007161'
    GROUP BY trunc(pay_date, 'MM'), sicid, p_rnn, pay_month
    HAVING SUM(cnt_mzp) < 1
) 
, aq as (
        SELECT /*+parallel(2)*/ m.pd, m.sicid, m.p_rnn, s.pay_month, SUM(cnt_mzp) sum_mzp  
        FROM aq_src m, si_member_2 s
        WHERE m.p_rnn = s.p_rnn
        AND s.sicid = m.sicid
        AND s.pay_month = m.pay_month
        AND s.knp in ('012')
        GROUP BY m.sicid, m.p_rnn, s.pay_month, m.pd
)
SELECT
      m7.obc,
      m7.obn,
      m7.rc,
      m7.rn,
      m7.p_rnn,
	  m7.nm,
      m7.c,
      m8.c,
      m9.c
FROM 
  ( 
	  SELECT
		  p_rnn,
		  rb1.rfbn_id obc,
		  rb1.name obn,
		  rb.rfbn_id rc,
		  rb.name rn,
		  nvl(n.name_ip, n.fio) nm,
		  COUNT(DISTINCT sicid) c
	  FROM aq m, rfon_organization o, 
		   cato_branch cb, 
		   rfbn_branch_site rb, 
		   rfbn_branch_site rb1,
		   dm
	  where m.p_rnn = o.bin(+)
	  and   substr(rb.rfbn_id,1,4) = cb.rfbn_id(+)
	  and   substr(rb1.rfbn_id,1,4) = substr(cb.rfbn_id,1,2)||'00'  
  
	--   LEFT JOIN rfrr_id_region r ON r.id = m.p_rnn AND r.typ = 'I'
	--   LEFT JOIN nk_minfin_iin n ON n.iin = m.p_rnn 
	--   LEFT JOIN rfbn_branch_site rb ON rb.RFBN_ID = r.rfbn_id
	--   LEFT JOIN rfbn_branch_site rb1 ON rb1.RFBN_ID = r.rfrg_id || '00'
	--   , dm
	  and   m.sum_mzp < 1
	  AND   m.pd = dm.f_month
	  GROUP BY p_rnn, o.nm_ru, rb1.rfbn_id, rb1.name, rb.rfbn_id, rb.name
  ) m7,
  ( SELECT p_rnn, COUNT(DISTINCT sicid) c
    FROM aq m, dm
    WHERE sum_mzp < 1
    AND m.pd = dm.s_month
    GROUP BY p_rnn
  ) m8,
  ( SELECT p_rnn, COUNT(DISTINCT sicid) c
    FROM aq m, dm
    WHERE sum_mzp < 1
    AND m.pd = dm.t_month
    GROUP BY p_rnn
  ) m9
WHERE m7.p_rnn = m8.p_rnn 
AND m8.p_rnn = m9.p_rnn
ORDER BY 1, 3
"""

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 14)
	#worksheet.set_row(3, 48)

	worksheet.set_column(0, 0, 6)
	worksheet.set_column(1, 1, 11)
	worksheet.set_column(2, 2, 42)
	worksheet.set_column(3, 3, 11)
	worksheet.set_column(4, 4, 48)
	worksheet.set_column(5, 5, 16)
	worksheet.set_column(6, 6, 128)
	worksheet.set_column(7, 7, 8)
	worksheet.set_column(8, 8, 8)
	worksheet.set_column(9, 9, 8)

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

	worksheet.write(3,0, '№', common_format)
	worksheet.write(3,1, 'Код области', common_format)
	worksheet.write(3,2, 'Область', common_format)
	worksheet.write(3,3, 'Код района', common_format)
	worksheet.write(3,4, 'Район', common_format)
	worksheet.write(3,5, 'БИН предприятия', common_format)
	worksheet.write(3,6, 'Наименование предприятия', common_format)
	worksheet.write(3,7, '1 месяц', common_format)
	worksheet.write(3,8, '2 месяц', common_format)
	worksheet.write(3,9, '3 месяц', common_format)
	

def do_report(file_name: str, date_first: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}: {date_first}')
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
			title_name_report .set_align('vcenter')
			title_name_report .set_bold()

			title_format_it = workbook.add_format({'align': 'right'})
			title_format_it.set_align('vcenter')
			title_format_it.set_italic()

			common_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
			common_format.set_align('vcenter')
			common_format.set_border(1)

			name_format = workbook.add_format({'align': 'left', 'font_color': 'black'})
			name_format.set_align('vcenter')
			name_format.set_border(1)

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
			sql_sheet.merge_range('A1:I70', f'{stmt_report}', merge_format)

			worksheet.activate()
			format_worksheet(worksheet=worksheet, common_format=title_format)

			worksheet.write(0, 0, report_name, title_name_report)
			worksheet.write(1, 0, f'За квартал: {get_quarter_number(date_first)} ({date_first})', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0

			log.info(f'CREATING REPORT {report_code} ...')
			try:
				cursor.execute(stmt_report,  first_date=date_first)
			except oracledb.DatabaseError as e:
				error, = e.args
				log.error(f"ERROR. REPORT {report_code}. error_code: {error.code}, error: {error.message}\n{stmt_report}")
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
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					# if col in (1,4):
					# 	worksheet.write(row_cnt+shift_row, col, list_val, region_name_format)
					if col in (1,3,5,7,8,9):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col in (2,4,6):
						worksheet.write(row_cnt+shift_row, col, list_val, name_format)
					col += 1
				row_cnt += 1
				cnt_part += 1
				if cnt_part > 9999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			# Шифр отчета
			worksheet.write(0, 9, report_code, title_name_report)

			now = datetime.datetime.now()
			stop_time = now.strftime("%H:%M:%S")

			worksheet.write(1, 9, f'Дата формирования: {now.strftime("%d.%m.%Y ")}({s_date} - {stop_time})', title_format_it)
			#
			workbook.close()
			set_status_report(file_name, 2)
			
			log.info(f'REPORT: {report_code}. Формирование отчета {file_name} завершено ({s_date} - {stop_time}). Загружено {row_cnt-1} записей')

			return file_name



def thread_report(file_name: str, date_first: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS NONE')
	threading.Thread(target=do_report, args=(file_name, date_first), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('minCO_03.xlsx', '01.10.2022')
