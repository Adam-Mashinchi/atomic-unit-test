@echo off
cd %~dp0
python -V
IF ERRORLEVEL == 9009 (
python
echo Please install Python then try again!
cmd /k
) ELSE (
python -m venv .\venv
call ".\venv\Scripts\activate.bat"
pip install -r requirements.txt
@echo on
python atomic-unit-test.py --atomics atomic_tests\TDR_2021 --verbose
cmd /k
)