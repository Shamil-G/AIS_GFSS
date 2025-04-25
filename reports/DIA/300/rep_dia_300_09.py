from configparser import ConfigParser
# from   db_config import report_db_user, report_db_password, report_db_dsn
import xlsxwriter
import datetime
import oracledb
from   util.logger import log
import os.path
from   model.manage_reports import set_status_report


report_name = 'Сведения о поступивших возвратах излишне зачисленных (выплаченных) сумм социальных выплат'
report_code = '300.09'

#document.ridt_id: 6 - Выплаты из ГФСС, 7 - 10% удержания, 8 - удержания из соц.выплат
#document.status:  0 - Документ сформирован на выплату, 1 - Сформирован платеж, 2 - Платеж на выплате
stmt_drop = "begin execute immediate 'drop table tmp_dia_9v'; exception when others then null; end;"

def get_stmt_1(date_first, date_second):
	return f"""
  create table tmp_dia_9v as 
          select substr(pd.doc_assign, 2, 2) rfbn_id,  
                 pd.doc_date, 
                 pd.doc_nmb, 
                 pd.cipher_id_knp knp,
                 pd.refer, 
                 dl.pay_sum,
                 nvl(dl.period,pd.period) as period, 
                 dl.fm|| ' ' ||dl.nm|| ' ' ||dl.ft as fio, 
                 pd.doc_assign, 
                 pd.rfbk_mfo_pbank,
                 dl.rnn,
                 dl.sicid 
          from  pmpd_pay_doc pd,  
                pmdl_doc_list dl   
          where pd.pay_date=dl.pay_date
          and   pd.mhmh_id=dl.mhmh_id
          and   ( 
                pd.cipher_id_knp in ('028', '047', '092', '097')
                or 
              ( pd.cipher_id_knp = '049'
                and   pd.doc_assign like '%Возврат сумм%'
              )
          )
          and   pd.pay_date >= to_date('{date_first}', 'YYYY-MM-DD') 
          and   trunc(pd.pay_date) <= to_date('{date_second}', 'YYYY-MM-DD') 
          and   dl.pay_date >= to_date('{date_first}', 'YYYY-MM-DD') 
          and   trunc(dl.pay_date) <= to_date('{date_second}', 'YYYY-MM-DD')
          and pd.r_account= 'KZ70125KZT1001300134'
"""

stmt_2 = 'create index IX_tmp_dia_9v_sicid on tmp_dia_9v(sicid)'

stmt_3 = """
  select ' '||coalesce(substr(reg_name,4),'Итого:') reg_name, cnt_all, sum_all, cnt_028, sum_028,
       cnt_047, sum_047, cnt_049, sum_049, cnt_097, sum_097, cnt_092, sum_092
  from (        
		select a.RFBN_ID||'. '||NAME as reg_name,
              sum(cnt_028+cnt_047+cnt_049+cnt_097+cnt_092) cnt_all,
              sum(sum_028+sum_047+sum_049+sum_097+sum_092) sum_all,
              sum(cnt_028) cnt_028, sum(sum_028) sum_028,
              sum(cnt_047) cnt_047, sum(sum_047) sum_047,
              sum(cnt_049) cnt_049, sum(sum_049) sum_049,
              sum(cnt_097) cnt_097, sum(sum_097) sum_097,
              sum(cnt_092) cnt_092, sum(sum_092) sum_092
        from (       
            select case when knp='028' then cnt else 0 end cnt_028,
                   case when knp='028' then sum_pay else 0 end sum_028,
                   case when knp='047' then cnt else 0 end cnt_047,
                   case when knp='047' then sum_pay else 0 end sum_047,
                   case when knp='049' then cnt else 0 end cnt_049,
                   case when knp='049' then sum_pay else 0 end sum_049,
                   case when knp='097' then cnt else 0 end cnt_097,
                   case when knp='097' then sum_pay else 0 end sum_097,
                   case when knp='092' then cnt else 0 end cnt_092,
                   case when knp='092' then sum_pay else 0 end sum_092,
                   substr(rfbn_id,1,2) rfbn_id
            from (       
                  select count(knp) cnt,
                         sum(pay_sum) sum_pay,
                         rfbn_id, 
                         knp
                  from  tmp_dia_9v   
                  group by rfbn_id, knp
                  order by rfbn_id, knp
            )
        ) a, rfbn_branch b
        where a.rfbn_id||'00'=b.RFBN_ID
		group by cube(a.RFBN_ID||'. '||b.NAME)
		order by 1
   )
"""

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

	s_date = datetime.datetime.now().strftime("%H:%M:%S")

	log.info(f'DO REPORT. START {report_code}. DATE_FROM: {date_first}, DATE_TO: {date_second}, FILE_PATH: {file_name}')
	
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

			title_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
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

			#
			worksheet.write(0, 12, report_code, title_report_code)

			now = datetime.datetime.now()
			stop_time = now.strftime("%H:%M:%S")

			worksheet.write(1, 12, f'Дата формирования: {now.strftime("%d.%m.%Y ")}({s_date} - {stop_time})', title_format_it)
			#
			workbook.close()
			set_status_report(file_name, 2)
			
			log.info(f'REPORT: {report_code}. Формирование отчета {file_name} завершено ({s_date} - {stop_time}). Загружено {row_cnt-1} записей')


def thread_report(file_name: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: date_from: {date_first}, date_to: {date_second}')
	threading.Thread(target=do_report, args=(file_name, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('0701_02.xlsx', '01.10.2022','31.10.2022')
