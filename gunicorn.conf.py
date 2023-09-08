import multiprocessing
from   ais_gfss_parameter import app_name, using

bind = "localhost:5000"
workers = int(multiprocessing.cpu_count()*2) + 1
worker_class = "gevent"
print(f'GUNICORN. change DIRECTORY: {app_name}')
if using.startswith('PROD'):
    chdir = f"/home/ais_gfss/{app_name}"
else:
    chdir = f"C:/Projects/{app_name}"
wsgi_app = "wsgi:app"
loglevel = 'info'
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s"  "%(a)s"'
accesslog = "logs/pdd-gunicorn-access.log"

error_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s"  "%(a)s"'
errorlog = "logs/pdd-gunicorn-error.log"
proc_name = 'REP'
# Перезапуск после N кол-во запросов
max_requests = 0
# Перезапуск, если ответа не было более 60 сек
timeout = 180
# umask or -m 007
umask = 0x007
# Проверка IP адресов, с которых разрешено обрабатывать набор безопасных заголовков
forwarded_allow_ips = '10.51.203.165,10.51.203.167,127.0.0.1,10.15.15.12'
#preload увеличивает производительность - хуже uwsgi!
preload_app = 'True'