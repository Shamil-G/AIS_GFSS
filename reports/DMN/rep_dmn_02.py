import xlsxwriter
import datetime
import os.path
from   util.logger import log
import oracledb
from   db_config import report_db_user, report_db_password, report_db_dsn
from   model.manage_reports import set_status_report

# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)

report_name = 'Кол-во дел по дням и регионам с доработкой'
report_code = 'DMN.03'


stmt_2 = """
with st7with_dat as (
                select 
                        st.sid,
                        st.st2,
                        first_value(st.dat) over(partition by sid order by dat) dat,
                        s_brid,
                        p_pc
                from ss_m_sol_st st
                where st2 in (7, 12)
                and trunc(st.dat, 'DD') Between to_date(:d1, 'YYYY-MM-DD') And to_date(:d2, 'YYYY-MM-DD')
                and substr(p_pc, 1, 4) = :rfpm_id
)
,
comm_st as(
                select  st.sid,
                        st.st2,
                        st.dat,
                        st7.s_brid,
                        st7.p_pc,
                        z.sicid,
                        z.num
                from ss_m_sol_st st, ss_z_doc z, st7with_dat st7
                where z.id = st.sid
                and st.sid = st7.sid
                and st.st2 in (4, 145, 16, 8, 43, 44, 45)
                and z.id_tip = 'NEW'
                )
                ,
st4_145 as
            (
            select * from
                            (
                            select
                                    st.sid,
                                    st.st2,
                                    first_value(st.dat) over(partition by st.sid, st.num order by st.dat) dat,
                                    row_number() over(partition by st.sid, st.num order by st.dat) row_num,
                                    s_brid,
                                    p_pc,
                                    sicid,
                                    st.num
                            from comm_st st
                            where st2 in (4, 145, 16)
                            )
            where row_num=1
            )
,
st8_43 as (
            select * from
                        (
                        select  st.sid,
                                st.st2,
                                first_value(st.dat) over(partition by st.sid, st.num order by st.dat) dat,
                                row_number() over(partition by st.sid, st.num order by st.dat) row_num,
                                s_brid,
                                p_pc
                        from comm_st st
                        where st2 in (8, 43, 44, 45)
                        )
            where row_num=1
            )
,
cntdays487 as (
                select  count_work_date(trunc(st4.dat,'DD'), trunc(st7.dat, 'DD'))+1 cnt_days,
                        st4.sid,
                        st4.s_brid,
                        st4.p_pc,
                        st4.sicid,
                        st4.num
                from st8_43 st8, st4_145 st4, st7with_dat st7
                where st8.sid = st4.sid
                and st8.sid = st7.sid
                )

        select  substr(s_brid, 1, 2),
				count(num),
                count(case when cnt.cnt_days < 5 then num else null end) before_5,
                count(case when cnt.cnt_days between 5 and 9 then num else null end) in5_9,
                count(case when cnt.cnt_days between 10 and 14 then num else null end) in10_14,
                count(case when cnt.cnt_days between 15 and 19 then num else null end) in15_19,
                count(case when cnt.cnt_days between 20 and 24 then num else null end) in20_24,
                count(case when cnt.cnt_days >= 25 then num else null end) more25
        from cntdays487 cnt
        group by substr(s_brid, 1, 2)
"""

active_stmt = stmt_2

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)

	worksheet.set_column(0, 0, 7)
	worksheet.set_column(1, 1, 10)
	worksheet.set_column(2, 2, 16)
	worksheet.set_column(3, 3, 16)
	worksheet.set_column(4, 4, 16)
	worksheet.set_column(5, 5, 16)
	worksheet.set_column(6, 6, 16)
	worksheet.set_column(7, 7, 16)
	worksheet.set_column(8, 8, 16)

	worksheet.write(2, 0, '№', common_format)
	worksheet.write(2, 1, 'Регион', common_format)
	worksheet.write(2, 2, 'Общее количество', common_format)
	worksheet.write(2, 3, 'до 5 дней', common_format)
	worksheet.write(2, 4, 'от 5 до 9 дней', common_format)
	worksheet.write(2, 5, 'от 10 до 14 дней', common_format)
	worksheet.write(2, 6, 'от 15 до 19 дней', common_format)
	worksheet.write(2, 7, 'от 20 до 24 дней', common_format)
	worksheet.write(2, 8, 'больше 25', common_format)


def do_report(file_name: str, srfpm_id: str, date_first: str, date_second: str):
	if os.path.isfile(file_name):
		log.info(f'Отчет уже существует {file_name}')
		return file_name
	
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

			digital_format = workbook.add_format({'num_format': '#0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '# ### ##0', 'align': 'right'})
			money_format.set_border(1)
			money_format.set_align('vcenter')
			
			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			date_format_it = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format_it.set_align('vcenter')
			date_format_it.set_italic()

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
			worksheet.write(1, 0, f'За период: {date_first} - {date_second}, {srfpm_id}', title_name_report)

			row_cnt = 1
			shift_row = 2
			cnt_part = 0

			cursor = connection.cursor()
			log.info(f'{file_name}. Загружаем данные за период {date_first} : {date_second}, srfpm: {srfpm_id}')
			cursor.execute(active_stmt, rfpm_id=srfpm_id, d1=date_first, d2=date_second)

			records = cursor.fetchall()
			#for record in records:
			for record in records:
				col = 1
				worksheet.write(row_cnt+shift_row, 0, row_cnt, digital_format)
				for list_val in record:
					if col == 1:
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col in (2,3,4,5,6,7,8):
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					col += 1
				row_cnt += 1
				cnt_part += 1

			worksheet.write(row_cnt+2, 2, "=SUM(C4:C"+str(row_cnt+2)+")", digital_format)
			worksheet.write(row_cnt+2, 3, "=SUM(D4:D"+str(row_cnt+2)+")", digital_format)
			worksheet.write(row_cnt+2, 4, "=SUM(E4:E"+str(row_cnt+2)+")", digital_format)
			worksheet.write(row_cnt+2, 5, "=SUM(F4:F"+str(row_cnt+2)+")", digital_format)
			worksheet.write(row_cnt+2, 6, "=SUM(G4:G"+str(row_cnt+2)+")", digital_format)
			worksheet.write(row_cnt+2, 7, "=SUM(H4:H"+str(row_cnt+2)+")", digital_format)
			worksheet.write(row_cnt+2, 8, "=SUM(I4:I"+str(row_cnt+2)+")", digital_format)

			now = datetime.datetime.now().strftime("%d.%m.%Y (%H:%M:%S)")
			worksheet.write(1, 6, f'Дата формирования: {now}', date_format_it)

			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {file_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			set_status_report(file_name, 2)
			return file_name


def thread_report(file_name: str, srfpm_id: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: rfpm_id: {srfpm_id}, date_first: {date_first}, date_second: {date_second}')
	threading.Thread(target=do_report, args=(file_name, srfpm_id, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('0701', '01.01.2022','31.10.2022')
