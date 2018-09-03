#/usr/bin/bash



WORK_DIR="profs"
if [ ! -d "$WORK_DIR/cal" ]; then
  mkdir "$WORK_DIR/cal"
fi
if [ ! -d "$WORK_DIR/svg" ]; then
  mkdir "$WORK_DIR/svg"
fi
if [ ! -d "$WORK_DIR/xls" ]; then
  mkdir "$WORK_DIR/xls"
fi
if [ ! -d "$WORK_DIR/xlsx" ]; then
  mkdir "$WORK_DIR/xlsx"
fi
sh ./convert_xls.sh "$WORK_DIR"
cd "$WORK_DIR"
find -maxdepth 1 -type f -name "*.xls" | xargs -I {} -n 1 mv {} xls/
find -maxdepth 1 -type f -name "*.xlsx" | xargs -I {} -n 1 mv {} xlsx/
cd ../
python xlsx2cal.py "$WORK_DIR"
python parse2svg.py "$WORK_DIR" "$WORK_DIR/svg" profs total

#exit 0



WORK_DIR="rooms"
if [ ! -d "$WORK_DIR/cal" ]; then
  mkdir "$WORK_DIR/cal"
fi
if [ ! -d "$WORK_DIR/svg" ]; then
  mkdir "$WORK_DIR/svg"
fi
if [ ! -d "$WORK_DIR/xls" ]; then
  mkdir "$WORK_DIR/xls"
fi
if [ ! -d "$WORK_DIR/xlsx" ]; then
  mkdir "$WORK_DIR/xlsx"
fi
sh ./convert_xls.sh "$WORK_DIR"
cd "$WORK_DIR"
find -maxdepth 1 -type f -name "*.xls" | xargs -I {} -n 1 mv {} xls/
find -maxdepth 1 -type f -name "*.xlsx" | xargs -I {} -n 1 mv {} xlsx/
cd ../
python xlsx2cal.py "$WORK_DIR"
python parse2svg.py "$WORK_DIR" "$WORK_DIR/svg" rooms




WORK_DIR="groups"
if [ ! -d "$WORK_DIR/cal" ]; then
  mkdir "$WORK_DIR/cal"
fi
if [ ! -d "$WORK_DIR/svg" ]; then
  mkdir "$WORK_DIR/svg"
fi
if [ ! -d "$WORK_DIR/xls" ]; then
  mkdir "$WORK_DIR/xls"
fi
if [ ! -d "$WORK_DIR/xlsx" ]; then
  mkdir "$WORK_DIR/xlsx"
fi
sh ./convert_xls.sh "$WORK_DIR"
cd "$WORK_DIR"
find -maxdepth 1 -type f -name "*.xls" | xargs -I {} -n 1 mv {} xls/
find -maxdepth 1 -type f -name "*.xlsx" | xargs -I {} -n 1 mv {} xlsx/
cd ../
python xlsx2cal.py "$WORK_DIR"
python parse2svg.py "$WORK_DIR" "$WORK_DIR/svg" groups
