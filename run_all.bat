SET WORK_DIR=%CD%\profs
CHDIR %WORK_DIR%

IF NOT EXIST "%CD%\cal" MKDIR "%CD%\cal"
IF NOT EXIST "%CD%\svg" MKDIR "%CD%\svg"
IF NOT EXIST "%CD%\xls" MKDIR "%CD%\xls"
IF NOT EXIST "%CD%\xlsx" MKDIR "%CD%\xlsx"

CHDIR ..

c:\python27\python.exe xlsx2cal.py "%WORK_DIR%"
c:\python27\python.exe parse2svg.py "%WORK_DIR%" "%WORK_DIR%\svg" profs


SET WORK_DIR=%CD%\rooms
CHDIR %WORK_DIR%

IF NOT EXIST "%CD%\cal" MKDIR "%CD%\cal"
IF NOT EXIST "%CD%\svg" MKDIR "%CD%\svg"
IF NOT EXIST "%CD%\xls" MKDIR "%CD%\xls"
IF NOT EXIST "%CD%\xlsx" MKDIR "%CD%\xlsx"

CHDIR ..

c:\python27\python.exe xlsx2cal.py "%WORK_DIR%"
c:\python27\python.exe parse2svg.py "%WORK_DIR%" "%WORK_DIR%\svg" rooms


SET WORK_DIR=%CD%\groups
CHDIR %WORK_DIR%

IF NOT EXIST "%CD%\cal" MKDIR "%CD%\cal"
IF NOT EXIST "%CD%\svg" MKDIR "%CD%\svg"
IF NOT EXIST "%CD%\xls" MKDIR "%CD%\xls"
IF NOT EXIST "%CD%\xlsx" MKDIR "%CD%\xlsx"

CHDIR ..

c:\python27\python.exe xlsx2cal.py "%WORK_DIR%"
c:\python27\python.exe parse2svg.py "%WORK_DIR%" "%WORK_DIR%\svg" groups

set /p DUMMY=Hit ENTER to continue...
