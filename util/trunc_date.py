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
