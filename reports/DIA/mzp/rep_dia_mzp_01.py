from   db_config import report_db_user, report_db_password, report_db_dsn
import xlsxwriter
import datetime
from   util.logger import log
import oracledb
from   model.call_report import set_status_report
import os.path

report_name = 'Сведения о поступивших возвратах излишне зачисленных (выплаченных) сумм социальных выплат'
report_code = 'mzp.01'

#document.ridt_id: 6 - Выплаты из ГФСС, 7 - 10% удержания, 8 - удержания из соц.выплат
#document.status:  0 - Документ сформирован на выплату, 1 - Сформирован платеж, 2 - Платеж на выплате
stmt_drop = "begin execute immediate 'drop table tmp_dia_mzp_01'; exception when others then null; end;"

stmt_create_table = """
create table temp_dia_mzp_01
as
select * from (
	Select /*+ PARALLEL(8) */
		m.sicid, m.p_rnn, 
		m.pay_month, 
		sum(m.sum_pay) sum_pay,
		sum(sum_pay * 100 / p.perc / z.mzp) cnt_mzp 
	From si_member_2 m, nnn_perc p, nnn_mzp z
	Where p.mnt(+) = m.pay_month 
	and z.mnt(+) = m.pay_month
	and coalesce(m.type_payer, to_nchar('X')) !='Е' --ЕСП платеж исключить
	and coalesce(m.type_payment, to_nchar('X'))!='О' --Единый платеж исключить
	and m.pay_month = to_date(:p_month,'YYYY-MM-DD')
	GROUP BY m.sicid, m.p_rnn, m.pay_month
)             
where cnt_mzp < 1
"""

def get_stmt_1(date_first, date_second):
	return f"""
SELECT
    nvl(rb1.RFBN_ID, 'нет') rfbn_reg,--"Код области",
    rb1.NAME name_reg,--"Область",
    nvl(rb.RFBN_ID, 'нет') rfbn_area,--"Код района",
    rb.NAME name_area,--"Район",
    p_rnn, --"БИН/ИИН предприятия",
--     sum(case when a.pay_date < '01.05.2022' and knp = '012' then a.pay_sum else 0 end) before_1_m,
    nvl(n.name_ip, n.fio) name_org,--"Наименование предприятия",
    cnt_all,-- "Количество сотрудников",
    COUNT(DISTINCT sicid) sicid-- "Количество сотр МЗП < 1"
FROM tbl_less_mzp m
LEFT JOIN rfrr_id_region r ON r.id = m.p_rnn AND r.typ = 'I'
LEFT JOIN nk_minfin_iin n ON n.iin = m.p_rnn --AND n.priz_ip = 1
LEFT JOIN rfbn_branch_site rb ON rb.RFBN_ID = r.rfbn_id
LEFT JOIN rfbn_branch_site rb1 ON rb1.RFBN_ID = r.rfrg_id || '00'
WHERE m.mzp < 1
--  AND p_rnn = '040940004616'

GROUP BY rb1.RFBN_ID,
    rb1.NAME,
    rb.RFBN_ID,
    rb.NAME,
    p_rnn,
    nvl(n.name_ip, n.fio),
    cnt_all
ORDER BY rb.RFBN_ID, 6
"""

stmt_2 = 'create index IX_tmp_dia_9v_sicid on tmp_dia_9v(sicid)'


def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)
	worksheet.set_row(2, 72)
	worksheet.set_row(3, 48)

	worksheet.set_column(0, 0, 7)
	worksheet.set_column(1, 1, 32)
	worksheet.set_column(2, 2, 14)
	worksheet.set_column(3, 3, 18)
	worksheet.set_column(4, 4, 14)
	worksheet.set_column(5, 5, 18)
	worksheet.set_column(6, 6, 14)
	worksheet.set_column(7, 7, 18)
	worksheet.set_column(8, 8, 14)
	worksheet.set_column(9, 9, 18)
	worksheet.set_column(10, 10, 18)
	worksheet.set_column(11, 11, 18)
	worksheet.set_column(12, 12, 18)
	worksheet.set_column(13, 13, 18)

	worksheet.merge_range('A3:A4', '№', common_format)
	worksheet.merge_range('B3:B4', 'Область', common_format)
	worksheet.merge_range('C3:D3', 'Всего', common_format)
	worksheet.write(3, 2, 'Кол-во получателей (человек)', common_format)
	worksheet.write(3, 3, 'Сумма возвратов (тыс. тенге)', common_format)
	worksheet.merge_range('E3:F3', 'На случай утраты трудоспособности\nКНП=028', common_format)
	worksheet.write(3, 4, 'Кол-во получателей (человек)', common_format)
	worksheet.write(3, 5, 'Сумма возвратов (тыс. тенге)', common_format)
	worksheet.merge_range('G3:H3', 'На случай потери кормильца\nКНП=047', common_format)
	worksheet.write(3, 6, 'Кол-во получателей (человек)', common_format)
	worksheet.write(3, 7, 'Сумма возвратов (тыс. тенге)', common_format)
	worksheet.merge_range('I3:J3', 'На случай потери кормильца\nКНП=049', common_format)
	worksheet.write(3, 8, 'Кол-во получателей (человек)', common_format)
	worksheet.write(3, 9, 'Сумма возвратов (тыс. тенге)', common_format)
	worksheet.merge_range('K3:L3', 'на случай потери дохода в связи с беременностью и родами, усыновлением (удочерением) новорожденного ребенка (детей)\nКНП=097', common_format)
	worksheet.write(3, 10, 'Кол-во получателей (человек)', common_format)
	worksheet.write(3, 11, 'Сумма возвратов (тыс. тенге)', common_format)
	worksheet.merge_range('M3:N3', 'на случай потери дохода в связи с уходом за ребенком по достижении им возраста 1,5 лет\nКНП=092', common_format)
	worksheet.write(3, 12, 'Кол-во получателей (человек)', common_format)
	worksheet.write(3, 13, 'Сумма возвратов (тыс. тенге)', common_format)



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
			sql_sheet.merge_range('A1:I70', f"{get_stmt_1}\n{stmt_2}\n{stmt_3}", merge_format)

			worksheet.activate()
			format_worksheet(worksheet=worksheet, common_format=title_format)

			worksheet.write(0, 0, report_name, title_name_report)
			worksheet.write(1, 0, f'За период: {date_first} - {date_second}', title_name_report)

			row_cnt = 1
			shift_row = 3
			cnt_part = 0

			log.info(f'REPORT. EXECUTE: {stmt_drop}')
			cursor.execute(stmt_drop)
			log.info(f'REPORT. CREATE TABLE.')
			cursor.execute(stmt_create_table)

			stmt_1 = get_stmt_1(date_first, date_second)
			
			log.info(f'REPORT: {report_code}\n----------\tФормируем промежуточную таблицу за период {date_first} : {date_second}')
			#log.info(f'REPORT: {report_code}\n----------\t{stmt_1}')
			cursor.execute(stmt_1)
			log.info(f'REPORT: {report_code}. Создаем индекс')
			cursor.execute(stmt_2)
			log.info(f'REPORT: {report_code}.\n\tФормируем выходную EXCEL таблицу')
			cursor.execute(stmt_3)

			records = cursor.fetchall()
			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col == 1:
						worksheet.write(row_cnt+shift_row, col, list_val, region_name_format)
					if col in (2,4,6,8,10,12):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col in (3,5,7,9,11,13):
						worksheet.write(row_cnt+shift_row, col, list_val, money_format)
					col += 1
				row_cnt += 1
				cnt_part += 1
				if cnt_part > 9999:
					log.info(f'{file_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			log.info(f'REPORT: {report_code}. Удаляем промежуточную таблицу')
			cursor.execute(stmt_drop)

			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			date_format.set_border(0)
			date_format.set_italic()
			worksheet.write(1, 12, f'Дата формирования: {now}', date_format)

			workbook.close()
			set_status_report(file_name, 2)
			log.info(f'REPORT: {report_code}. Формирование отчета {file_name} завершено: {now}')


def thread_report(file_name: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: date_from: {date_first}, date_to: {date_second}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('0701_02.xlsx', '01.10.2022','31.10.2022')
