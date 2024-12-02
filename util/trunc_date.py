import calendar
import datetime

def first_day(input_date: str):
	try:
		first_date = datetime.datetime.strptime(input_date, '%Y-%m-%d').replace(day=1)
	except ValueError:
		first_date = datetime.datetime.strptime(input_date, '%d.%m.%Y').replace(day=1)
	return datetime.datetime.strftime(first_date, '%Y-%m-%d')


def last_day(input_date: str):
	try:
		last_date = datetime.datetime.strptime(input_date, '%Y-%m-%d')
	except ValueError:
		last_date = datetime.datetime.strptime(input_date, '%d.%m.%Y')
	last_date = last_date.replace(day=calendar.monthrange(last_date.year, last_date.month)[1])
	return datetime.datetime.strftime(last_date, '%Y-%m-%d')


def trunc_year(input_date: str):
	try:
		trunc_date = datetime.datetime.strptime(input_date, '%Y-%m-%d').replace(day=1, month=1)
	except ValueError:
		trunc_date = datetime.datetime.strptime(input_date, '%d.%m.%Y').replace(day=1, month=1)
	return datetime.datetime.strftime(trunc_date, '%Y-%m-%d')

def get_year(input_date: str):
	try:
		trunc_date = datetime.datetime.strptime(input_date, '%Y-%m-%d').replace(day=1, month=1)
	except ValueError:
		trunc_date = datetime.datetime.strptime(input_date, '%d.%m.%Y').replace(day=1, month=1)
	return datetime.datetime.strftime(trunc_date, '%Y')


def get_quarter_number(input_date: str):
	try:
		src_date = datetime.datetime.strptime(input_date, '%Y-%m-%d')
	except ValueError:
		src_date = datetime.datetime.strptime(input_date, '%d.%m.%Y')
	
	Q_number = (int(src_date.strftime('%m'))+2)//3
	return Q_number


if __name__ == "__main__":
	test_date_1 = '11.01.2024'
	# test_date_2 = '11.02.2024'
	# test_date_3 = '11.03.2024'
	# test_date_4 = '11.04.2024'
	test_date_5 = '11.05.2024'
	# test_date_6 = '11.06.2024'
	# test_date_7 = '2024-07-15'
	test_date_8 = '2024-08-15'
	# test_date_9 = '2024-09-15'
	# test_date_10 = '2024-10-15'
	# test_date_11 = '2024-11-15'
	test_date_12 = '2024-12-15'
	print(f'Квартал : {get_current_quarter_number(test_date_1)}')
	# print(f'Квартал : {get_current_quarter_number(test_date_2)}')
	# print(f'Квартал : {get_current_quarter_number(test_date_3)}')

	# print(f'Квартал : {get_current_quarter_number(test_date_4)}')
	print(f'Квартал : {get_current_quarter_number(test_date_5)}')
	# print(f'Квартал : {get_current_quarter_number(test_date_6)}')

	# print(f'Квартал : {get_current_quarter_number(test_date_7)}')
	print(f'Квартал : {get_current_quarter_number(test_date_8)}')
	# print(f'Квартал : {get_current_quarter_number(test_date_9)}')
	
	# print(f'Квартал : {get_current_quarter_number(test_date_10)}')
	# print(f'Квартал : {get_current_quarter_number(test_date_11)}')
	print(f'Квартал : {get_current_quarter_number(test_date_12)}')
