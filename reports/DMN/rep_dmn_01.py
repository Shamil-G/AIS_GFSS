# Получатели назначенных выплат и их СО до назначения выплаты
import xlsxwriter
import datetime
import os.path
from logger import log
import cx_Oracle


report_name = 'DMN_01'

stmt = """
select  BIN, IIN,
       --sicid,
		last_rfpm_id,
		last_appointdate,
		last_approvedate,
		last_pay_month,
		case when last_pay_month is not null and cnt_ext=0 and cnt_self>0 then 1 else 0 end cnt_self,
		case when last_pay_month is not null and cnt_ext>0 and cnt_self>0 then 1 else 0 end mix,
		case when last_pay_month is not null and cnt_ext>0 and cnt_self=0 then 1 else 0 end cnt_ext
from         
(
	select BIN, 
		   IIN,
		sicid, 
		last_rfpm_id, 
		last_appointdate, 
		last_approvedate, 
		(case when months_between(last_appointdate,last_pay_month) <= cnt_month then a.last_pay_month else null end) last_pay_month,
		(select count(si2.sicid) 
			from si_member_2 si2
			where si2.sicid=a.sicid
			and   si2.pay_month=a.last_pay_month
			and   si2.p_rnn=IIN
		) cnt_self,
		(select count(si3.sicid) 
			from si_member_2 si3
			where si3.sicid=a.sicid
			and si3.pay_month=a.last_pay_month
			and   si3.p_rnn!=IIN
		) cnt_ext
	from (
		select  unique first_value(si.p_rnn) over(partition by si.sicid order by si.pay_month desc) BIN,
			p.rn IIN,
			si.sicid, 
			first_value(pt.rfpm_id) over(partition by si.sicid order by si.pay_month desc) last_rfpm_id,
			first_value(appointdate) over(partition by si.sicid order by si.pay_month desc) last_appointdate,
			first_value(pt.approvedate) over(partition by si.sicid order by si.pay_month desc) last_approvedate,
			first_value(si.pay_month) over(partition by si.sicid order by si.pay_month desc) last_pay_month,
			case when substr(rfpm_id,1,4)='0704' then 12 else 24 end cnt_month
		from si_member_2 si,
			pnpt_payment pt,
			person p
		where pt.pncd_id = si.sicid
		and   si.sicid = p.sicid
		and substr(pt.rfpm_id,1,4) = :p1
		and pt.approvedate between :d1 and :d2
		and pt.appointdate <= pt.approvedate
		and si.pay_date < pt.approvedate
        and si.pay_month < pt.appointdate
		and si.pay_month >= case when substr(pt.rfpm_id,1,4)='0704' then add_months(trunc(pt.appointdate,'MM'), -12) else add_months(trunc(pt.appointdate,'MM'), -24) end
		and si.pay_date >= case when substr(pt.rfpm_id,1,4)='0704' then add_months(trunc(pt.appointdate,'MM'), -12) else add_months(trunc(pt.appointdate,'MM'), -24) end
	) a
) b
"""


stmt_1 = """
select  BIN, IIN,
       --sicid,
		last_rfpm_id,
		last_risk_date,
		last_approvedate,
		last_pay_month,
		case when last_pay_month is not null and cnt_ext=0 and cnt_self>0 then 1 else 0 end cnt_self,
		case when last_pay_month is not null and cnt_ext>0 and cnt_self>0 then 1 else 0 end mix,
		case when last_pay_month is not null and cnt_ext>0 and cnt_self=0 then 1 else 0 end cnt_ext
from         
(
	select BIN, 
		   IIN,
		sicid, 
		last_rfpm_id, 
		last_risk_date, 
		last_approvedate, 
		(case when months_between(last_risk_date,last_pay_month) <= cnt_month then a.last_pay_month else null end) last_pay_month,
		(select count(si2.sicid) 
			from si_member_2 si2
			where si2.sicid=a.sicid
			and   si2.pay_month=a.last_pay_month
			and   si2.p_rnn=IIN
		) cnt_self,
		(select count(si3.sicid) 
			from si_member_2 si3
			where si3.sicid=a.sicid
			and si3.pay_month=a.last_pay_month
			and   si3.p_rnn!=IIN
		) cnt_ext
	from (
		select unique 
		 first_value(si.p_rnn) over(partition by si.sicid order by si.pay_month desc) BIN,
		  p.rn IIN,
		  sol.sicid,
		  first_value(pay.pc) over(partition by d.sicp_id order by d.RISK_DATE desc) last_rfpm_id,
		  first_value(d.RISK_DATE) over(partition by sol.sicid order by d.RISK_DATE desc) last_risk_date,
		  first_value(sol.z_date) over(partition by sol.sicid order by d.RISK_DATE desc) last_z_date,
		  first_value(sol.d_resh) over(partition by sol.sicid order by d.RISK_DATE desc) last_approvedate,
		  first_value(si.pay_month) over(partition by sol.sicid order by si.pay_month desc) last_pay_month,
		  case when substr(pay.pc,1,4)='0704' then 12 else 24 end cnt_month
		from si_member_2 si,
			ss_m_sol sol, -- Здесь дата решения, назначения, заявления
			ss_m_pay pay, -- Здесь код выплаты
			ss_data d, -- Здесь дата риска
			person p
		where sol.sicid = p.sicid
		and sol.id = d.sipr_id
		and sol.sicid = p.sicid
		and sol.sicid = si.sicid
		and sol.id = pay.sid
		and substr(pay.pc,1,4) = :P1
		and sol.d_resh between  :D1  and :D2
		and si.pay_date < sol.z_date -- Дата заявления
		and si.pay_month < trunc(sol.Z_DATE,'MM')
		and si.pay_month >= case when substr(pay.pc,1,4)='0704' then add_months(trunc(D.RISK_DATE,'MM'), -12) else add_months(trunc(D.RISK_DATE,'MM'), -24) end
		and si.pay_date >= case when substr(pay.pc,1,4)='0704' then add_months(trunc(D.RISK_DATE,'MM'), -12) else add_months(trunc(D.RISK_DATE,'MM'), -24) end
	) a
) b
"""


stmt_2 = """
select  BIN, IIN,
       --sicid,
		last_rfpm_id,
		last_risk_date,
		last_approvedate,
		last_pay_month,
		case when last_pay_month is not null and cnt_ext=0 and cnt_self>0 then 1 else 0 end cnt_self,
		case when last_pay_month is not null and cnt_ext>0 and cnt_self>0 then 1 else 0 end mix,
		case when last_pay_month is not null and cnt_ext>0 and cnt_self=0 then 1 else 0 end cnt_ext
from         
(
	select BIN, 
		   IIN,
		sicid, 
		last_rfpm_id, 
		last_risk_date, 
		last_approvedate, 
		(case when months_between(last_risk_date,last_pay_month) <= cnt_month then a.last_pay_month else null end) last_pay_month,
		(select count(si2.sicid) 
			from si_member_2 si2
			where si2.sicid=a.sicid
			and   si2.pay_month=a.last_pay_month
			and   si2.p_rnn=IIN
		) cnt_self,
		(select count(si3.sicid) 
			from si_member_2 si3
			where si3.sicid=a.sicid
			and si3.pay_month=a.last_pay_month
			and   si3.p_rnn!=IIN
		) cnt_ext
	from (
		select unique 
			   first_value(si.p_rnn) over(partition by si.sicid order by si.pay_month desc) BIN,
			   p.rn IIN,
			   si.sicid,
			   first_value(m.rfpm_id) over(partition by m.sicp_id order by m.risk_date desc) last_rfpm_id,
			   first_value(m.RISK_DATE) over(partition by m.sicp_id order by m.RISK_DATE desc) last_risk_date,
			   first_value(m.date_address) over(partition by m.sicp_id order by m.RISK_DATE desc) last_date_address,
			   first_value(m.date_approve) over(partition by m.sicp_id order by m.RISK_DATE desc) last_approvedate,
			   first_value(si.pay_month) over(partition by m.sicp_id order by si.pay_month desc) last_pay_month,
			   case when substr(m.rfpm_id,1,4)='0704' then 12 else 24 end cnt_month
		from si_member_2 si, sipr_maket_first_approve m, person p
		where m.sicp_id = p.sicid
		and   m.sicp_id = si.sicid
		and substr(m.rfpm_id,1,4) = :P1
		and m.date_approve between :D1 and :D2
		and si.pay_date < m.date_address -- Дата заявления, обращения
		and si.pay_month < trunc(m.date_address,'MM')
		and si.pay_month < trunc(m.RISK_DATE,'MM')
		and si.pay_month >= case when substr(m.rfpm_id,1,4)='0704' then add_months(trunc(m.RISK_DATE,'MM'), -12) else add_months(trunc(m.RISK_DATE,'MM'), -24) end
		and si.pay_date >= case when substr(m.rfpm_id,1,4)='0704' then add_months(trunc(m.RISK_DATE,'MM'), -12) else add_months(trunc(m.RISK_DATE,'MM'), -24) end
	) a
) b
"""


def format_worksheet(worksheet, common_format):
	worksheet.set_column(0, 0, 7)
	worksheet.set_column(1, 1, 14)
	worksheet.set_column(2, 2, 14)
	worksheet.set_column(3, 3, 12)
	worksheet.set_column(4, 4, 12)
	worksheet.set_column(5, 5, 12)
	worksheet.set_column(6, 6, 12)
	worksheet.set_column(7, 7, 12)
	worksheet.set_column(8, 8, 14)
	worksheet.set_column(9, 9, 14)

	worksheet.write(0, 0, '№', common_format)
	worksheet.write(0, 1, 'БИН', common_format)
	worksheet.write(0, 2, 'ИИН', common_format)
	worksheet.write(0, 3, 'Код выплаты', common_format)
	worksheet.write(0, 4, 'Дата риска', common_format)
	worksheet.write(0, 5, 'Дата назначения', common_format)
	worksheet.write(0, 6, 'Месяц посл. платежа', common_format)
	worksheet.write(0, 7, 'СО за себя', common_format)
	worksheet.write(0, 8, 'СО смешанное', common_format)
	worksheet.write(0, 9, 'СО от работодателя', common_format)


def make_report(rfpm_id: str, date_from: str, date_to: str):
	file_name = f'{report_name}_{rfpm_id}_{date_from}_{date_to}.xlsx'
	file_path = f'{file_name}'

	if os.path.isfile(file_path):
		return file_name
	else:
		cx_Oracle.init_oracle_client(lib_dir='c:/Shamil//instantclient_21_3')
		#cx_Oracle.init_oracle_client(lib_dir='/home/aktuar/instantclient_21_8')
		with cx_Oracle.connect(user='sswh', password='sswh', dsn="172.16.17.12/gfss", encoding="UTF-8") as connection:
			workbook = xlsxwriter.Workbook(file_path)

			common_format = workbook.add_format({'align': 'center', 'font_color': 'black'})
			common_format.set_align('vcenter')
			common_format.set_text_wrap()
			common_format.set_border(1)
			common_format.set_bold()
			sum_pay_format = workbook.add_format({'num_format': '#,###,##0.00', 'font_color': 'black', 'align': 'vcenter'})
			sum_pay_format.set_border(1)
			date_format = workbook.add_format({'num_format': 'd.mm.yyyy', 'align': 'center'})
			date_format.set_border(1)
			digital_format = workbook.add_format({'num_format': '# ### ##0', 'align': 'center'})
			digital_format.set_border(1)
			digital_format.set_align('vcenter')

			now = datetime.datetime.now()
			log.info(f'Начало формирования {report_name}: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			worksheet = workbook.add_worksheet('Список')
			format_worksheet(worksheet=worksheet, common_format=common_format)

			row_cnt = 0
			cnt_part = 0

			cursor = connection.cursor()
			cursor.execute(stmt, [rfpm_id, date_from, date_to])
			records = cursor.fetchall()
			#for record in records:
			for record in records:
				col = 0
				worksheet.write(row_cnt+1, col, row_cnt, digital_format)
				for list_val in record:
					if col in (0,6,7,8):
						worksheet.write(row_cnt+1, col+1, list_val, digital_format)
					if col in (1,2):
						worksheet.write(row_cnt+1, col+1, list_val, common_format)
					if col in (3,4,5):
						worksheet.write(row_cnt+1, col+1, list_val, date_format)
					col += 1
				row_cnt += 1
				cnt_part += 1
				if cnt_part > 999:
					log.info(f'{report_name}. LOADED {row_cnt} records.')
					cnt_part = 0

			#worksheet.write(row+1, 3, "=SUM(D2:D"+str(row_cnt+1)+")", sum_pay_format)

			workbook.close()
			now = datetime.datetime.now()
			log.info(f'Формирование отчета {report_name} завершено: {now.strftime("%d-%m-%Y %H:%M:%S")}')
			return file_name


if __name__ == "__main__":
    log.info(f'Отчет {report_name} запускается.')
    make_report('0703', '01.10.2022','31.10.2022')
