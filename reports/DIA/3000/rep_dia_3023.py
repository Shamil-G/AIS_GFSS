from configparser import ConfigParser
import xlsxwriter
import datetime
from   util.logger import log
import oracledb
import os.path
from   model.manage_reports import set_status_report

report_name = 'Стаж участия в СОСС (3023)'
report_code = '3023'

stmt_report = """
with src as (
	select /*+parallel(8)*/
		q.stag_uch,
		sum(case when q.sex = '1' then cnt end) cnt_m,
		sum(case when q.sex = '0' then cnt end) cnt_w,
		sum(case when q.sex = '1' then q.sum24_so end) sum_m,
		sum(case when q.sex = '0' then q.sum24_so end) sum_w
    from
        (select /*+parallel(8)*/
			x.*, p.sex,
			case when x.cnt_so < 13 then 1
				when x.cnt_so < 24 then 2
				when x.cnt_so < 36 then 3
				when x.cnt_so < 48 then 4
				when x.cnt_so < 60 then 5
				when x.cnt_so < 72 then 6
				when x.cnt_so < 84 then 7
				when x.cnt_so < 96 then 8
				when x.cnt_so < 108 then 9
				when x.cnt_so < 120 then 10
				when x.cnt_so < 132 then 11
				when x.cnt_so < 144 then 12
				when x.cnt_so < 156 then 13
				when x.cnt_so < 168 then 14
				when x.cnt_so < 180 then 15
				when x.cnt_so < 192 then 16
				when x.cnt_so < 204 then 17
				when x.cnt_so < 216 then 18      --when x.cnt_so >= 204 then 18
				when x.cnt_so < 228 then 19      --добавил 12.03.2024
				when x.cnt_so < 240 then 20      --добавил 12.03.2024
				when x.cnt_so >= 240 then 21     --добавил 12.03.2024
            end stag_uch
         from person p,
              (select /*+parallel(8)*/ 
					f.sicid,                                -- участник
                    count(unique f.pay_month) cnt_so,      -- стаж участия - от начала и до указанной даты
                    count(unique case when	f.knp = '012' 
											and f.pay_date_gfss >= to_date(:dt_from,'YYYY-MM-DD')
											and f.pay_date_gfss < to_date(:dt_to,'YYYY-MM-DD') + 1
											and f.pay_date >= add_months(to_date(:dt_from,'YYYY-MM-DD'),-1)
											and	f.pay_date < to_date(:dt_to,'YYYY-MM-DD') + 1 
									  then f.sicid 
									  else null 
								 end
					) cnt,
                    sum(case when f.knp = '012' 
									and f.pay_date_gfss >= to_date(:dt_from,'YYYY-MM-DD')
									and f.pay_date_gfss < to_date(:dt_to,'YYYY-MM-DD') + 1
									and f.pay_date >= add_months(to_date(:dt_from,'YYYY-MM-DD'),-1)
									and	f.pay_date < to_date(:dt_to,'YYYY-MM-DD') + 1 
                             then f.sum_pay 
							 else 0 
						end
					) sum24_so       --Суммарные СО по участнику за 24 месяца от указанной даты
               from si_member_2 f
			   where f.pay_date_gfss < to_date(:dt_to,'YYYY-MM-DD') + 1
			   and	 f.pay_date < to_date(:dt_to,'YYYY-MM-DD') + 1 
			   -- and f.pay_date_gfss >= to_date(:dt_from,'YYYY-MM-DD') -- Из-за стажа участия нижний порого указывать нельзя!!!
			   -- and	 f.pay_date >= add_months(to_date(:dt_from,'YYYY-MM-DD'),-1)
               group by f.sicid
              ) x
              where x.sum24_so > 0
              and p.sicid = x.sicid
    ) q
	group by q.stag_uch
)
select 	/*+parallel(8)*/ 
		case
            when stag_uch=1 then 'от 0 до 13'
            when stag_uch=2 then 'от 13 до 24'
            when stag_uch=3 then 'от 24 до 36'
            when stag_uch=4 then 'от 36 до 48'
            when stag_uch=5 then 'от 48 до 60'
            when stag_uch=6 then 'от 60 до 72'
            when stag_uch=7 then 'от 72 до 84'
            when stag_uch=8 then 'от 84 до 96'
            when stag_uch=9 then 'от 96 до 108'
            when stag_uch=10 then 'от 108 до 120'
            when stag_uch=11 then 'от 120 до 132'
            when stag_uch=12 then 'от 132 до 144'
            when stag_uch=13 then 'от 144 до 156'
            when stag_uch=14 then 'от 156 до 168'
            when stag_uch=15 then 'от 168 до 180'
            when stag_uch=16 then 'от 180 до 192'
            when stag_uch=17 then 'от 192 до 204'
            when stag_uch=18 then 'от 204 до 216'    -- when stag_uch=18 then 'свыше 204'
            when stag_uch=19 then 'от 216 до 228'    --добавил 12.03.2024
            when stag_uch=20 then 'от 228 до 240'    --добавил 12.03.2024
            when stag_uch=21 then 'свыше 240'        --добавил 12.03.2024
       end staj_uch,   --"Стаж участия, месяцев",
	   s.cnt_m cnt_m,  --"Кол-во мужчин",
	   s.cnt_w cnt_w,  --"Кол-во женщин",
	   s.sum_m sum_m,  --"Сумма мужчин",
	   s.sum_w sum_w   --"Сумма женщин"
from src s
order by stag_uch
"""


def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 14)
	#worksheet.set_row(3, 48)

	worksheet.set_column(0, 0, 6)
	worksheet.set_column(1, 1, 14)
	worksheet.set_column(2, 2, 12)
	worksheet.set_column(3, 3, 12)
	worksheet.set_column(4, 4, 18)
	worksheet.set_column(5, 5, 18)

	worksheet.write(2,0, '1', common_format)
	worksheet.write(2,1, '2', common_format)
	worksheet.write(2,2, '3', common_format)
	worksheet.write(2,3, '4', common_format)
	worksheet.write(2,4, '5', common_format)
	worksheet.write(2,5, '6', common_format)
	worksheet.write(3,0, '№', common_format)
	worksheet.write(3,1, 'Стаж участия, месяцев', common_format)
	worksheet.write(3,2, 'Кол-во мужчин', common_format)
	worksheet.write(3,3, 'Кол-во женщин', common_format)
	worksheet.write(3,4, 'Сумма мужчин', common_format)
	worksheet.write(3,5, 'Сумма женщин', common_format)


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
			worksheet[page_num-1].write(1, 0, f'За период: {date_first} - {date_second}', title_name_report)

			row_cnt = 1
			all_cnt=1
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
				worksheet[page_num-1].write(row_cnt+shift_row, 0, all_cnt, digital_format)
				for list_val in record:
					if col in (1,2,3,4):
						worksheet[page_num-1].write(row_cnt+shift_row, col, list_val, common_format)
					if col in (4,5):
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
					worksheet[page_num-1].write(1, 0, f'За период: {date_first} - {date_second}', title_name_report)

				if cnt_part > 250000:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			now = datetime.datetime.now()
			stop_time = now.strftime("%H:%M:%S")

			for i in range(page_num):
				# Шифр отчета
				worksheet[i].write(0, 5, report_code, title_report_code)
				worksheet[i].write(1, 5, f'Дата формирования: {now.strftime("%d.%m.%Y ")}({s_date} - {stop_time})', title_format_it)

			workbook.close()
			set_status_report(file_name, 2)

			log.info(f'REPORT: {report_code}. Формирование отчета {file_name} завершено ({s_date} - {stop_time}). Загружено {all_cnt} записей')


def thread_report(file_name: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: date_from: {date_first}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('minSO_01.xlsx', '01.10.2022','31.10.2022')
