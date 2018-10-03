del "*.svg"
SET WORK_DIR=%CD%\profs
CHDIR %WORK_DIR%

RD /S /Q "cal"
RD /S /Q "svg"

CHDIR ..

SET WORK_DIR=%CD%\rooms
CHDIR %WORK_DIR%

RD /S /Q "cal"
RD /S /Q "svg"

CHDIR ..

SET WORK_DIR=%CD%\groups
CHDIR %WORK_DIR%

RD /S /Q "cal"
RD /S /Q "svg"

CHDIR ..