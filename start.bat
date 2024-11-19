python -m venv venv
rem . /home/reports/REPORTS_GFSS/venv/bin/activate
call C:\Projects\REPORTS_GFSS\venv\Scripts\activate.bat

python -m pip install --upgrade pip
pip install oracledb
pip install flask
pip install flask_login
pip install redis
pip install flask_session
pip install openpyxl
pip install requests
pip install ldap3
rem pip freeze > requirements.txt
python main_app.py
