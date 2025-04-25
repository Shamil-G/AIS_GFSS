from configparser import ConfigParser
import xlsxwriter
import datetime
from   util.logger import log
import oracledb
import os.path
from   model.manage_reports import set_status_report

report_name = 'Мониторинг поступления СО от плательщиков, с которыми проведена информационно-разъяснительная работ'
report_code = 'minCO.02'

# 
#document.status:  0 - Документ сформирован на выплату, 1 - Сформирован платеж, 2 - Платеж на выплате
stmt_load = "begin sswh.load_min_so_history.make; end;"

stmt_report = """
  with before_ctrl as(
    select /*+parallel(8)*/ 
           unique cs.bin,
     first_value(ms.ctrl_date) over(partition by ms.p_rnn order by ms.ctrl_date desc) debt_date
    from sswh.min_so_history ms, sswh.ctrl_minso cs
    where ms.p_rnn=cs.bin
    -- and   cs.bin='000640002969'
    and   ms.ctrl_date<=cs.ctrl_date
    and   ms.pay_month>add_months(cs.ctrl_date,-12)
  )
  ,
  after_ctrl as(
    select /*+parallel(8)*/ 
           unique cs.bin,
           first_value(ms.ctrl_date) over(partition by ms.p_rnn order by ms.ctrl_date desc) ctrl_date
    from sswh.min_so_history ms, sswh.ctrl_minso cs
    where ms.p_rnn=cs.bin
    -- and   cs.bin='000640002969'
    and   ms.ctrl_date>cs.ctrl_date
  )
  ,
  src_list as (
     select /*+parallel(8)*/ 
            h.*, p.iin, f.debt_date
            ,cs.rfbn_id, cs.ctrl_date as check_date
     from before_ctrl f, sswh.min_so_history h, person p
    , sswh.ctrl_minso cs
     where h.ctrl_date=f.debt_date
     and   cs.bin=h.p_rnn
     -- and   h.p_rnn='000640002969'
     -- and h.sicid=728535
     and h.p_rnn=f.bin
     and p.sicid=h.sicid
  )
  ,
  success_list as (
  select /*+parallel(8)*/ 
         --f.ctrl_date,
     f.bin, h.sicid, h.pay_month, p.iin as iin
     from before_ctrl f, sswh.min_so_history h, person p
     where h.ctrl_date=f.debt_date
  --        and p.sicid=728535
     and h.p_rnn=f.bin
     and p.sicid=h.sicid
  MINUS
  select /*+parallel(8)*/ 
         --L.ctrl_date,
         L.bin, h.sicid, h.pay_month, p.iin as iin
     from after_ctrl L, sswh.min_so_history h, person p
     where h.ctrl_date=L.ctrl_date
  --        and p.sicid=728535
     and h.p_rnn=L.bin
     and p.sicid=h.sicid
  )
  select a.rfbn_id, bin, cnt_worker, 
		 iin, pay_month, sum_pay, min_so,
		 sum_debt, date_debt, check_date,
		 ctrl_date, 
		 sum(si_sum_pay) all_si_sum_pay,
		 date_oplat
  from (
	  select /*+ parallel(8) */
		 src.rfbn_id,
		 sl.bin,
		 src.cnt_worker,
		 sl.iin,
		 src.pay_month,
		 src.sum_pay,
		 sswh.min_so(src.pay_month) as min_so,
		 (sswh.min_so(src.pay_month)-src.sum_pay) as sum_debt,
		 src.debt_date date_debt,
		 src.check_date,
		 af.ctrl_date,
		 si.sum_pay as si_sum_pay,
		first_value(si.pay_date_gfss) over(partition by sl.iin, sl.bin, src.rfbn_id order by pay_date_gfss) date_oplat
	  from success_list sl
		 , src_list src
		 , after_ctrl af
		 , si_member_2 si
	  where src.p_rnn=sl.bin
	  and   src.pay_month=sl.pay_month
	  and   src.sicid=sl.sicid
	  and   sl.bin=af.bin

	  and   si.sicid(+)=sl.sicid
	  and   si.pay_date>=src.check_date
	  and   si.pay_month(+)=sl.pay_month
	  and   si.p_rnn(+)=sl.bin
  ) a
	group by
		rfbn_id,
		bin,
		cnt_worker,
		iin,
		pay_month,
		sum_pay,
		min_so,
		sum_debt,
		date_debt,
		check_date,
		ctrl_date,
		date_oplat
  order by bin, iin, pay_month desc
  """


def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 14)
	#worksheet.set_row(3, 48)

	worksheet.set_column(0, 0, 8)
	worksheet.set_column(1, 1, 8)
	worksheet.set_column(2, 2, 16)
	worksheet.set_column(3, 3, 14)
	worksheet.set_column(4, 4, 14)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 15)
	worksheet.set_column(9, 9, 15)
	worksheet.set_column(10, 10, 12)
	worksheet.set_column(11, 11, 12)
	worksheet.set_column(12, 12, 12)
	worksheet.set_column(13, 13, 12)

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
	worksheet.write(2,11, '12', common_format)
	worksheet.write(2,12, '13', common_format)
	worksheet.write(2,13, '14', common_format)
	worksheet.write(3,0, '№', common_format)
	worksheet.write(3,1, 'Код района', common_format)
	worksheet.write(3,2, 'БИН/ИИН предприятия', common_format)
	worksheet.write(3,3, 'Общее количество сотрудников', common_format)
	worksheet.write(3,4, 'ИИН сотрудника', common_format)
	worksheet.write(3,5, 'Период платежа', common_format)
	worksheet.write(3,6, 'Сумма платежа', common_format)
	worksheet.write(3,7, 'Мин.СО', common_format)
	worksheet.write(3,8, 'Задолженность', common_format)
	worksheet.write(3,9, 'Дата задолженности', common_format)
	worksheet.write(3,10, 'Дата сверки', common_format)
	worksheet.write(3,11, 'Дата расчета', common_format)
	worksheet.write(3,12, 'Сумма платежа', common_format)
	worksheet.write(3,13, 'Дата погашения', common_format)
	

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

			region_name_format = workbook.add_format({'align': 'left', 'font_color': 'black'})
			region_name_format.set_align('vcenter')
			region_name_format.set_border(1)

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
			worksheet.write(1, 0, f'На дату: {date_first}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0

			log.info(f'REPORT {report_code}. LOAD: {stmt_load}')
			cursor.execute(stmt_load)

			log.info(f'REPORT {report_code}. CREATE REPORT')
			try:
				cursor.execute(stmt_report)
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
					if col in (1,2,3,4):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col in (5,9,10,11,13):
						worksheet.write(row_cnt+shift_row, col, list_val, date_format)
					if col in (6,7,8,12):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				row_cnt += 1
				cnt_part += 1

			# Шифр отчета
			worksheet.write(0, 13, report_code, title_name_report)

			now = datetime.datetime.now()
			stop_time = now.strftime("%H:%M:%S")

			worksheet.write(1, 13, f'Дата формирования: {now.strftime("%d.%m.%Y ")}({s_date} - {stop_time})', title_format_it)
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
    do_report('minSO_02.xlsx', '01.10.2022','31.10.2022')
