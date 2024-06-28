set VIRTUAL_ENV=C:/Projects/AIS_GFSS/venv
rem python -m venv venv
rem call %VIRTUAL_ENV%/bin/activate
call %VIRTUAL_ENV%/Scripts/activate.bat

python -m pip install --upgrade pip
pip install oracledb
pip install flask
pip install flask_login
pip install redis
pip install flask_session
pip install openpyxl
pip install requests
rem pip freeze > requirements.txt
python main_app.py
