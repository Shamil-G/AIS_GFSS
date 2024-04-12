import xlsxwriter
import datetime
import os.path
import oracledb
from   util.logger import log
from   db_config import report_db_user, report_db_password, report_db_dsn
from   model.manage_reports import set_status_report


report_name = 'Частота уплаты СО за период'
report_code = '320.01'

stmt_1 = """
with 
common_list as ( 
	SELECT /*+parallel(4)*/
			pds.p_account, -- Сколько платежных счетов,столько и организаций
			p.rn as iin,
			sim.type_payer,
			sim.p_rnn,
			nvl(sim.type_payment,'U') type_payment,
			case when sim.p_rnn=p.rn 
				 then 1
				 else 0
			end as boss_ip,
			sim.sicid,
			sim.sum_pay,
			sim.pay_month
	FROM sswh.si_member_2 sim, 
		 sswh.pmpd_pay_doc pds, 
		 sswh.person p
	WHERE SIM.SICID=p.sicid 
	and   sim.mhmh_id=pds.mhmh_id
	and   sim.knp='012'
	and   sim.pay_date_gfss >= to_date(:first_date,'yyyy-mm-dd') 
	and   sim.pay_date_gfss < (to_date(:second_date,'yyyy-mm-dd') + 1)
	and   sim.pay_date > (to_date(:first_date,'yyyy-mm-dd')  - 30)
	and	  sim.pay_date < (to_date(:second_date,'yyyy-mm-dd') + 1)
	and   pds.pay_date > (to_date(:first_date,'yyyy-mm-dd')  - 30)
	and   pds.pay_date < (to_date(:second_date,'yyyy-mm-dd') + 1)
	-- and  sim.sicid=41660
)
, pers_agg_list as
(
	SELECT /*+parallel(4)*/
			unique sicid,
			count(unique p_rnn) cnt_org, 
			count(unique p_account) cnt_account, 
			count(unique type_payment) cnt_type_payment, 
			count(unique pay_month) as cnt_month,
			sum(case when cl.type_payer='Ю' or cl.type_payer = 'Н' then 1 else 0 end) is_ul,
			sum(case when type_payer in ('И','K') then 1 else 0 end) is_ip,
			sum(boss_ip) as cnt_boss_ip,
			sum(sum_pay) as all_sum_pay
	FROM common_list cl
	group by sicid
)
, pers_status as(
	select unique al.sicid, 
			case 
				 when type_payment = 'О' then '6. Объединенный платеж'
				 when cl.type_payer = 'Е' then '5. ЕСП'
				 when al.is_ul>0 and al.is_ip>0 then '1. Смешанные '
				 when al.is_ul>0 then '2. Наемные ЮЛ'
				 when al.is_ip>0 and cnt_boss_ip = 0 then '3. Наемные ИП'
				 when al.is_ip>0 and cnt_boss_ip > 0  then '4. ИП руководитель'
				 else 'UNKNOWN'
			end as tp,
			cnt_org,
			al.cnt_month,
			al.all_sum_pay
	from pers_agg_list al, common_list cl
	where al.sicid=cl.sicid
)
select /*+parallel(4)*/
    tp,
    COUNT(sicid) as "Всего плательщиков СО",
    sum(sl.all_sum_pay) sum_all,
    sum(CASE WHEN cnt_month = 1 THEN 1 ELSE 0 END) mnth_1,
    sum(CASE WHEN cnt_month = 1 THEN sl.all_sum_pay ELSE 0 END) sum_1,
    sum(CASE WHEN cnt_month = 2 THEN 1 ELSE 0 END) mnth_2,
    sum(CASE WHEN cnt_month = 2 THEN sl.all_sum_pay ELSE 0 END) sum_2,
    sum(CASE WHEN cnt_month = 3 THEN 1 ELSE 0 END) mnth_3,
    sum(CASE WHEN cnt_month = 3 THEN sl.all_sum_pay ELSE 0 END) sum_3,
    sum(CASE WHEN cnt_month = 4 THEN 1 ELSE 0 END) mnth_4,
    sum(CASE WHEN cnt_month = 4 THEN sl.all_sum_pay ELSE 0 END) sum_4,
    sum(CASE WHEN cnt_month = 5 THEN 1 ELSE 0 END) mnth_5,
    sum(CASE WHEN cnt_month = 5 THEN sl.all_sum_pay ELSE 0 END) sum_5,
    sum(CASE WHEN cnt_month = 6 THEN 1 ELSE 0 END) mnth_6,
    sum(CASE WHEN cnt_month = 6 THEN sl.all_sum_pay ELSE 0 END) sum_6,
    sum(CASE WHEN cnt_month = 7 THEN 1 ELSE 0 END) mnth_7,
    sum(CASE WHEN cnt_month = 7 THEN sl.all_sum_pay ELSE 0 END) sum_7,
    sum(CASE WHEN cnt_month = 8 THEN 1 ELSE 0 END) mnth_8,
    sum(CASE WHEN cnt_month = 8 THEN sl.all_sum_pay ELSE 0 END) sum_8,
    sum(CASE WHEN cnt_month = 9 THEN 1 ELSE 0 END) mnth_9,
    sum(CASE WHEN cnt_month = 9 THEN sl.all_sum_pay ELSE 0 END) sum_9,
    sum(CASE WHEN cnt_month = 10 THEN 1 ELSE 0 END) mnth_10,
    sum(CASE WHEN cnt_month = 10 THEN sl.all_sum_pay ELSE 0 END) sum_10,
    sum(CASE WHEN cnt_month = 11 THEN 1 ELSE 0 END) mnth_11,
    sum(CASE WHEN cnt_month = 11 THEN sl.all_sum_pay ELSE 0 END) sum_11,
    sum(CASE WHEN cnt_month = 12 THEN 1 ELSE 0 END) mnth_12,
    sum(CASE WHEN cnt_month = 12 THEN sl.all_sum_pay ELSE 0 END) sum_12,
    sum(CASE WHEN cnt_month > 12 THEN 1 ELSE 0 END) mnth_more_12,
    sum(CASE WHEN cnt_month > 12 THEN sl.all_sum_pay ELSE 0 END) sum_more_12
from pers_status sl
group by sl.tp
order by 1
"""

active_stmt = stmt_1

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 26)
	worksheet.set_row(2, 22)
	worksheet.set_row(3, 26)

	worksheet.set_column(0, 0, 5)
	worksheet.set_column(1, 1, 25)
	worksheet.set_column(2, 2, 16)
	worksheet.set_column(3, 3, 20)

	worksheet.merge_range('A3:A4',  '№', common_format)
	worksheet.merge_range('B3:B4',  'Тип плательщика', common_format)
	worksheet.merge_range('C3:C4',  'Кол-во участников', common_format)
	worksheet.merge_range('D3:D4', 'Сумма взносов', common_format)

	worksheet.merge_range('E3:F3', 'Один месяц', common_format)
	worksheet.merge_range('G3:H3', 'Два месяца', common_format)
	worksheet.merge_range('I3:J3', 'Три месяца', common_format)
	worksheet.merge_range('K3:L3', 'Четыре месяца', common_format)
	worksheet.merge_range('O3:P3', 'Пять месяцев', common_format)
	worksheet.merge_range('M3:N3', 'Шесть месяцев', common_format)
	worksheet.merge_range('Q3:R3', 'Семь месяцев', common_format)
	worksheet.merge_range('S3:T3', 'Восемь месяцев', common_format)
	worksheet.merge_range('U3:V3', 'Девять месяцев', common_format)
	worksheet.merge_range('W3:X3', 'Десять месяцев', common_format)
	worksheet.merge_range('Y3:Z3', 'Одиннадцать месяцев', common_format)
	worksheet.merge_range('AA3:AB3', 'Двенадцать месяцев', common_format)
	worksheet.merge_range('AC3:AD3', 'Более 12 месяцев', common_format)

	for i in range(0, 13):
		worksheet.set_column(4+i*2, 4+i*2, 12)
		worksheet.write(3,4+i*2, 'Кoличество', common_format)
		worksheet.set_column(5+i*2, 5+i*2, 18)
		worksheet.write(3,5+i*2, 'Сумма', common_format)


def do_report(file_name: str, date_first: str, date_second: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name

	with oracledb.connect(user=report_db_user, password=report_db_password, dsn=report_db_dsn) as connection:
		with connection.cursor() as cursor:
			workbook = xlsxwriter.Workbook(file_name)

			title_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_color': 'black'})
			title_format.set_align('vcenter')
			title_format.set_border(1)
			title_format.set_text_wrap()
			title_format.set_bold()

			title_name_report = workbook.add_format({'align': 'left', 'font_color': 'black', 'font_size': '13'})
			title_name_report .set_align('vcenter')
			title_name_report .set_bold()

			text_format = workbook.add_format({'align': 'left', 'font_color': 'black'})
			text_format.set_align('vcenter')
			text_format.set_border(1)

			common_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
			common_format.set_align('vcenter')
			common_format.set_border(1)

			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			text_format.set_align('vcenter')
			sum_pay_format.set_border(1)

			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			date_format_it = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'left'})
			date_format_it.set_align('vcenter')
			date_format_it.set_italic()

			digital_format = workbook.add_format({'num_format': '# ### ##0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			digital_right_format = workbook.add_format({'num_format': '# ### ##0', 'align': 'right'})
			digital_right_format.set_border(1)
			digital_right_format.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '# ### ### ### ##0.00', 'align': 'right'})
			money_format.set_align('vcenter')
			money_format.set_border(1)

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
			sql_sheet.merge_range('A1:I69', active_stmt, merge_format)

			worksheet.activate()
			format_worksheet(worksheet=worksheet, common_format=title_format)

			worksheet.write(0, 0, report_name, title_name_report)
			worksheet.write(1, 0, f'Период расчёта: с {date_first} по {date_second}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0
			m_val = [0]

			log.info(f'{file_name}. Загружаем данные с {date_first} по {date_second}')
			cursor.execute(active_stmt, first_date=date_first, second_date=date_second)

			records = cursor.fetchall()
			
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					match col:
						case 1: 
							worksheet.write(row_cnt+shift_row, col, list_val, text_format)
						case 2|4|6|8|10|12|14|16|18|20|22|24|26|28:
							worksheet.write(row_cnt+shift_row, col, list_val, digital_right_format)
						case _:
							worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					# if col == 1:
					# 	worksheet.write(row_cnt+shift_row, col, list_val, text_format)
					# if col in (2,4,6,8,10,12,14,16,18,20,22,24,26):
					# 	worksheet.write(row_cnt+shift_row, col, list_val, digital_right_format)
					# if col in range(3,17):
					# 	worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				cnt_part += 1
				if cnt_part > 9999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0
				row_cnt += 1

			worksheet.write(row_cnt+shift_row, 2, "=SUM(C5:C"+str(row_cnt+3)+")", digital_right_format)
			worksheet.write(row_cnt+shift_row, 3, "=SUM(D5:D"+str(row_cnt+3)+")", sum_pay_format)
			# worksheet.write(row_cnt + shift_row, 3, m_val[0], money_format)
			# Шифр отчета
			worksheet.write(0, 5, report_code, title_name_report)

			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			worksheet.write(1, 5, f'Дата формирования: {now}', date_format_it)

			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {file_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			set_status_report(file_name, 2)
			return file_name


def thread_report(file_name: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. DATE BETWEEN REPORT: {date_first} - {date_second}, FILE_NAME: {file_name}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    #make_report('0701', '01.10.2022','31.10.2022')
    do_report('01.01.2023', '15.01.2023')
