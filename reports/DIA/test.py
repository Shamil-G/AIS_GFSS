#func_name = "c:\\Projects\\AIS_GFSS\\reports\\DIA\\rep_dia_0702_01.py"
#func_name = "rep_dia_0702_01.py"

#from test_2 import make_report
#my_dict = {"func1": make_report}
#func_name = my_dict["func1"]
#print(f'{type(my_dict["func1"])} : {type(func_name)}')

my_dict_2 = {"func1": 'test_2' }
module_func2 = __import__(my_dict_2['func1'])
dir(module_func2)
print(f'-------- MODULE_FUNC2: {type(module_func2)} -------')
module_func2.make_report("0702","01.03.2023")
#eval(my_dict['func1'], {"rfpm_id":"0702","date_from":"01.03.2023"})

