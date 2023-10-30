set VIRTUAL_ENV=C:/Projects/AIS_GFSS/venv
rem python -m venv venv
rem call %VIRTUAL_ENV%/bin/activate
call %VIRTUAL_ENV%/Scripts/activate.bat

python -m pip install --upgrade pip
rem pip3.10 uninstall cx_Oracle
rem pip3.10 install oracledb
pip freeze > requirements.txt
rem python main_app.py
