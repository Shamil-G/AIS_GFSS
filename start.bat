set VIRTUAL_ENV=C:/Projects/AIS_GFSS/env
rem python3.10 -m venv venv
rem call %VIRTUAL_ENV%/bin/activate
call %VIRTUAL_ENV%/Scripts/activate.bat
pip3.10 install --upgrade pip
rem pip3.10 install flask
python main_app.py