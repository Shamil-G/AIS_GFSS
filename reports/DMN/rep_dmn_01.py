import xlsxwriter
import datetime
import os.path
from   util.logger import log
import oracledb
from   db_config import report_db_user, report_db_password, report_db_dsn
from   model.call_report import set_status_report

# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)

report_name = 'Кол-во дел по дням и регионам без доработки'
report_code = 'rep_DMN_01'


stmt_2 = """
with st7with_dat as (
                select 
                        st.sid,
                        st.st2,
                        st.dat,
                        s_brid,
                        p_pc
                from ss_m_sol_st st
                where st2 in (7, 12)
                and trunc(st.dat,'DD') Between to_date(:d1, 'YYYY-MM-DD') And to_date(:d2, 'YYYY-MM-DD')
                and substr(p_pc, 1, 4) = :rfpm_id
),

comm_st as(
select 
        st.sid,
        st.st2,
        st.dat,
        st7.s_brid,
        st7.p_pc,
        sicid,
        z.num
from ss_m_sol_st st, ss_z_doc z, st7with_dat st7
where z.id = st.sid
and st.sid = st7.sid
and st.st2 in (4, 145, 8, 43)
)
,
st_with_8_43 as (
                select 
						sid, p_pc, sicid, num
                from comm_st
                where st2 in (8, 43)
                )
,
WITHOUT_8_43 as (
        select  p.sid, p.p_pc, p.sicid, p.num, 
                dat
        from 
                (
                select sid, p_pc, sicid, num
                from comm_st st
                minus
                select sid, p_pc, sicid, num
                from st_with_8_43
                ) p, comm_st c
        where p.sid=c.sid
        and p.num=c.num
        and st2 in (4, 145)
            ),
cntdays487 as (
                select  count_work_date(trunc(st8.dat,'DD'), trunc(st7.dat, 'DD'))+1 cnt_days,
                        st8.sid, 
                        st7.s_brid,
                        st8.p_pc,
                        st8.sicid,
                        st8.num, rn
                from WITHOUT_8_43 st8, st7with_dat st7, person p
                where st8.sid = st7.sid
                and p.sicid = st8.sicid
                )

select  s_brid,
        sum(cnt_days),
        sum(case when cnt.cnt_days = 1 then cnt.cnt_days else null end) "1 день",
        sum(case when cnt.cnt_days = 2 then cnt.cnt_days else null end) "2 дня",
        sum(case when cnt.cnt_days = 3 then cnt.cnt_days else null end) "3 дня",
        sum(case when cnt.cnt_days = 4 then cnt.cnt_days else null end) "4 дня"
from cntdays487 cnt
group by s_brid
order by 1
"""

active_stmt = stmt_2

def format_worksheet(worksheet, common_format):
	worksheet.set_row(0, 24)
	worksheet.set_row(1, 24)

	worksheet.set_column(0, 0, 7)
	worksheet.set_column(1, 1, 10)
	worksheet.set_column(2, 2, 12)
	worksheet.set_column(3, 3, 14)
	worksheet.set_column(4, 4, 14)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 12)

	worksheet.write(2, 0, '№', common_format)
	worksheet.write(2, 1, 'Код региона', common_format)
	worksheet.write(2, 2, 'общее кол-во дел', common_format)
	worksheet.write(2, 3, '1 день', common_format)
	worksheet.write(2, 4, '2 дня', common_format)
	worksheet.write(2, 5, '3 дня', common_format)
	worksheet.write(2, 6, '4 дня', common_format)


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

			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			sum_pay_format.set_border(1)
			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			date_format.set_align('vcenter')

			digital_format = workbook.add_format({'num_format': '#0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			money_format = workbook.add_format({'num_format': '# ### ##0', 'align': 'right'})
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
					if col in (1, 2):
						worksheet.write(row_cnt+shift_row, col, list_val, common_format)
					if col == 3:
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col == 4:
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col == 5:
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					if col == 6:
						worksheet.write(row_cnt+shift_row, col, list_val, digital_format)
					col += 1
				row_cnt += 1
				cnt_part += 1

			#worksheet.write(row_cnt+1, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)

			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {file_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			set_status_report(file_name, 2)
			return file_name

def get_file_path(file_name: str, srfpm_id: str, date_first: str, date_second: str):
	full_file_name = f'{file_name}.{report_code}.{srfpm_id}.{date_first}-{date_second}.xlsx'
	return full_file_name

def thread_report(file_name: str, srfpm_id: str, date_first: str, date_second: str):
	import threading
	log.info(f'THREAD REPORT. {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} -> {file_name}')
	log.info(f'THREAD REPORT. PARAMS: rfpm_id: 0702, date_first: {date_first}, date_second: {date_second}')
	threading.Thread(target=do_report, args=(file_name, srfpm_id, date_first, date_second), daemon=True).start()
	return {"status": 1, "file_path": file_name}


if __name__ == "__main__":
    log.info(f'Отчет {report_code} запускается.')
    do_report('0701', '01.01.2022','31.10.2022')
