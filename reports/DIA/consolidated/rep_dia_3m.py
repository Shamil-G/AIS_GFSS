from configparser import ConfigParser
import xlsxwriter
import datetime
from   util.logger import log
import oracledb
import os.path
from   model.manage_reports import set_status_report
from   util.trunc_date import get_year

report_name = 'Сведения о СВбр, назначенный размер которых составил  3 млн. тенге и более в разрезе регионов'
report_code = '3M'

#document.status:  0 - Документ сформирован на выплату, 1 - Сформирован платеж, 2 - Платеж на выплате

stmt_report = """
with init_date as (
   select trunc(to_date(:date_first,'YYYY-mm-dd'),'YYYY') f_date, 3000000 as threshold from dual
)
, list_date as(
     select f_date,
            add_months(f_date, 12) s_date, 
            add_months(f_date, 24) t_date,
            threshold
     from init_date
)
select substr(a.rfbn_id,1,2),
       b.NAME,
       cnt_fy_thr,
       sum_fy_thr,
       cnt_fy_all,
       sum_fy_all,
       case when cnt_fy_all is not null then round(cnt_fy_thr*100/cnt_fy_all,2) else 0 end cnt_proc_fy,
       case when sum_fy_all is not null then round(sum_fy_thr*100/sum_fy_all,2) else 0 end sum_proc_fy,
       case when cnt_fy_thr !=0 then round(sum_fy_thr*100/cnt_fy_thr,2) else 0 end sum_fy_thr_avg,
       case when cnt_fy_all !=0 then round(sum_fy_all*100/cnt_fy_all,2) else 0 end sum_fy_avg,

       cnt_sy_thr,
       sum_sy_thr,
       cnt_sy_all,
       sum_sy_all,
       case when cnt_sy_all !=0 then round(cnt_sy_thr*100/cnt_sy_all,2) else 0 end cnt_proc_sy,
       case when sum_sy_all !=0 then round(sum_sy_thr*100/sum_sy_all,2) else 0 end sum_proc_sy,
       case when cnt_sy_thr !=0 then round(sum_sy_thr*100/cnt_sy_thr,2) else 0 end sum_sy_thr_avg,
       case when cnt_sy_all !=0 then round(sum_sy_all*100/cnt_sy_all,2) else 0 end sum_sy_avg,

       cnt_ty_thr,
       sum_ty_thr,
       cnt_ty_all,
       sum_ty_all,
       case when cnt_ty_all !=0 then round(cnt_ty_thr*100/cnt_ty_all,2) else 0 end cnt_proc_ty,
       case when sum_ty_all !=0 then round(sum_ty_thr*100/sum_ty_all,2) else 0 end sum_proc_ty,
       case when cnt_ty_thr !=0 then round(sum_ty_thr*100/cnt_ty_thr,2) else 0 end sum_ty_thr_avg,
       case when cnt_ty_all !=0 then round(sum_ty_all*100/cnt_ty_all,2) else 0 end sum_ty_avg
	   
	   --, ld.f_date,
       --ld.s_date,
       --ld.t_date,
       --ld.threshold
       
from (
        select /*+parallel(8)*/ 
               substr(s.rfbn_id,1,2) rfbn_id,
               sum( case when trunc(s.date_approve,'YYYY')=ld.f_date and s.sum_all>=3000000 then 1 else 0 end) cnt_fy_thr,
               sum( case when trunc(s.date_approve,'YYYY')=ld.f_date then 1 else 0 end) cnt_fy_all,
               sum( case when trunc(s.date_approve,'YYYY')=ld.f_date and s.sum_all>=3000000 then s.sum_all else 0 end) sum_fy_thr,
               sum( case when trunc(s.date_approve,'YYYY')=ld.f_date then s.sum_all else 0 end) sum_fy_all,

               sum( case when trunc(s.date_approve,'YYYY')=ld.s_date and s.sum_all>=3000000 then 1 else 0 end) cnt_sy_thr,
               sum( case when trunc(s.date_approve,'YYYY')=ld.s_date then 1 else 0 end) cnt_sy_all,
               sum( case when trunc(s.date_approve,'YYYY')=ld.s_date and s.sum_all>=3000000 then s.sum_all else 0 end) sum_sy_thr,
               sum( case when trunc(s.date_approve,'YYYY')=ld.s_date then s.sum_all else 0 end) sum_sy_all,
               
               sum( case when trunc(s.date_approve,'YYYY')=ld.t_date and s.sum_all>=3000000 then 1 else 0 end) cnt_ty_thr,
               sum( case when trunc(s.date_approve,'YYYY')=ld.t_date then 1 else 0 end) cnt_ty_all,
               sum( case when trunc(s.date_approve,'YYYY')=ld.t_date and s.sum_all>=3000000 then s.sum_all else 0 end) sum_ty_thr,
               sum( case when trunc(s.date_approve,'YYYY')=ld.t_date then s.sum_all else 0 end) sum_ty_all
               
        from sipr_maket_first_approve_2 s, list_date ld
        where s.date_approve>=ld.f_date
        and   s.date_approve<add_months(ld.t_date,12)+1
        group by substr(s.rfbn_id,1,2)
) a, rfbn_branch b, list_date ld
where substr(a.rfbn_id,1,2)=substr(b.RFBN_ID,1,2)
and substr(b.RFBN_ID,3,2)='00'
order by 1
"""

def format_worksheet(worksheet, common_format, first_year: int):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 20)
	worksheet.set_row(4, 14)

	worksheet.set_column(0, 0, 8)
	worksheet.set_column(1, 1, 30)

	# Номера столбцов
	for num in range(26):
		worksheet.write(4,num, num+1, common_format)

	worksheet.merge_range('A3:A4', 'Код региона', common_format)
	worksheet.merge_range('B3:B4', 'Наименование региона', common_format)
	worksheet.merge_range('C3:J3', f'Год {first_year}', common_format)
	worksheet.merge_range('K3:R3', f'Год {first_year+1}', common_format)
	worksheet.merge_range('S3:Z3', f'Год {first_year+2}', common_format)

	step = 8
	first_col = 2
	for num_year in range(1,4):
		worksheet.set_column((num_year-1)*step + first_col, (num_year-1)*step + first_col, 12)
		worksheet.write(3,(num_year-1)*step + first_col, 'кол-во получателей с назначением более 3 млн тенге (человек)', common_format)

		worksheet.set_column((num_year-1)*step + first_col + 1, (num_year-1)*step + first_col + 1, 18)
		worksheet.write(3,(num_year-1)*step + first_col + 1, 'общая сумма выплат получателям с назначением более 3 млн (тенге)', common_format)

		worksheet.set_column((num_year-1)*step + first_col + 2, (num_year-1)*step + first_col + 2, 12)
		worksheet.write(3,(num_year-1)*step + first_col + 2, 'кол-во получателей всего (человек)', common_format)

		worksheet.set_column((num_year-1)*step + first_col + 3, (num_year-1)*step + first_col + 3, 18)
		worksheet.write(3,(num_year-1)*step + first_col + 3, 'общая сумма выплат (тенге)', common_format)

		worksheet.set_column((num_year-1)*step + first_col + 4, (num_year-1)*step + first_col + 4, 12)
		worksheet.write(3,(num_year-1)*step + first_col + 4, 'доля получателей выплат с назначением более 3 млн (процент)', common_format)

		worksheet.set_column((num_year-1)*step + first_col + 5, (num_year-1)*step + first_col + 5, 12)
		worksheet.write(3,(num_year-1)*step + first_col + 5, 'доля выплат на получателей с назначением более 3 млн (процент)', common_format)

		worksheet.set_column((num_year-1)*step + first_col + 6, (num_year-1)*step + first_col + 6, 16)
		worksheet.write(3,(num_year-1)*step + first_col + 6, 'средняя выплата на получателей с назначением более 3 млн', common_format)

		worksheet.set_column((num_year-1)*step + first_col + 7, (num_year-1)*step + first_col + 7, 16)
		worksheet.write(3,(num_year-1)*step + first_col + 7, 'средняя выплата на на всех', common_format)
	

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

			title_report_code = workbook.add_format({'align': 'right', 'font_size': '14'})
			title_report_code.set_align('vcenter')
			title_report_code.set_bold()

			common_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
			common_format.set_align('vcenter')
			common_format.set_border(1)

			region_name_format = workbook.add_format({'align': 'left', 'font_color': 'black'})
			region_name_format.set_align('vcenter')
			region_name_format.set_border(1)

			category_name_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
			category_name_format.set_align('vcenter')
			category_name_format.set_border(1)

			category_name_format_1 = workbook.add_format({'align': 'left', 'font_color': 'black'})
			category_name_format_1.set_border(1)
			category_name_format_1.set_bg_color('#FFF8DC')	  # Желтенький
			category_name_format_2 = workbook.add_format({'align': 'left', 'font_color': 'black'})
			category_name_format_2.set_bg_color('#DAFBC5')	  # Зелененький
			category_name_format_3 = workbook.add_format({'align': 'left', 'font_color': 'black'})
			category_name_format_3.set_bg_color('#FDFEE5')	  # Желтенький
			category_name_format_4 = workbook.add_format({'align': 'left', 'font_color': 'black'})
			category_name_format_4.set_bg_color('#EBE6FF')	  #  Светло-голубой
			category_name_format_5 = workbook.add_format({'align': 'left', 'font_color': 'black'})
			category_name_format_5.set_bg_color('#FFFFE0')	  # Слегка желтенький
			category_name_format_6 = workbook.add_format({'align': 'left', 'font_color': 'black'})
			category_name_format_6.set_bg_color('#FFE1E1')	  # Розовый
			category_name_format_7 = workbook.add_format({'align': 'left', 'font_color': 'black'})
			category_name_format_7.set_bg_color('#E0F7FF')    # Голубой
			category_name_format_1.set_border(1)
			category_name_format_2.set_border(1)
			category_name_format_3.set_border(1)
			category_name_format_4.set_border(1)
			category_name_format_5.set_border(1)
			category_name_format_6.set_border(1)
			category_name_format_7.set_border(1)

			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			sum_pay_format.set_border(1)

			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			number_format = workbook.add_format({'num_format': '# ### ### ##0', 'align': 'center'})
			number_format.set_border(1)
			number_format.set_align('vcenter')

			digital_format = workbook.add_format({'num_format': '# ### ### ##0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '### ### ### ### ##0.00', 'align': 'right'})
			money_format.set_border(1)
			money_format.set_align('vcenter')

			percent_format = workbook.add_format({'num_format': '### ##0.00', 'align': 'center'})
			percent_format.set_border(1)
			percent_format.set_align('vcenter')

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
			sql_sheet.merge_range('A1:I145', f'{stmt_report}', merge_format)

			worksheet.activate()
			format_worksheet(worksheet=worksheet, common_format=title_format, first_year=int(get_year(date_first)))

			worksheet.write(0, 0, report_name, title_name_report)
			worksheet.write(1, 0, f'За период: {get_year(date_first)} - {int(get_year(date_first))+2}', title_name_report)

			cursor = connection.cursor()
			log.info(f'{file_name}. Загружаем данные за период {date_first} : {int(get_year(date_first))+2}')

			try:
				cursor.execute(stmt_report, date_first=date_first)
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
			row_cnt = 1
			shift_row = 4
			num_rec = 0
			#for record in records:
			for record in records:
				col = 0
				for list_val in record:
					if col == 0:
						# COLOR
						# match(num_rec):
						# 	case 0: worksheet.write(row_cnt+shift_row, col, list_val, category_name_format_1)
						# 	case 1: worksheet.write(row_cnt+shift_row, col, list_val, category_name_format_2)
						# 	case 2: worksheet.write(row_cnt+shift_row, col, list_val, category_name_format_3)
						# 	case 3: worksheet.write(row_cnt+shift_row, col, list_val, category_name_format_4)
						# 	case 4: worksheet.write(row_cnt+shift_row, col, list_val, category_name_format_5)
						# 	case 5: worksheet.write(row_cnt+shift_row, col, list_val, category_name_format_6)
						# 	case 6: worksheet.write(row_cnt+shift_row, col, list_val, category_name_format_7)
						# 	case _: worksheet.write(row_cnt+shift_row, col, list_val, category_name_format)
						worksheet.write(row_cnt+shift_row, col, list_val, category_name_format)
						num_rec = num_rec+1
					elif col == 1:
						worksheet.write(row_cnt+shift_row, col, list_val, region_name_format)
					elif col in (2,4,10,12,18,20):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					elif col in (6,7,14,15,22,23):
						worksheet.write(row_cnt+shift_row, col, list_val, percent_format)
					else:
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)

					col += 1
				row_cnt += 1

			# Шифр отчета
			worksheet.write(0, 13, report_code, title_report_code)
			
			now = datetime.datetime.now()
			stop_time = now.strftime("%H:%M:%S")

			worksheet.write(1, 13, f'Дата формирования: {now.strftime("%d.%m.%Y ")}({s_date} - {stop_time})', title_format_it)
			#
			workbook.close()
			set_status_report(file_name, 2)
			log.info(f'REPORT: {report_code}. Формирование отчета {file_name} завершено ({s_date} - {stop_time}). Строк в отчете: {row_cnt-1}')


def thread_report(file_name: str, date_first: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS NONE')
	threading.Thread(target=do_report, args=(file_name, date_first), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('minSO_02.xlsx', '01.10.2022','31.10.2022')
