#/usr/bin/bash
cd "$1"
FILES="*.xls"
for f in $FILES
do
  # extension="${f##*.}"
  filename="${f%.xls}"
  echo "Converting $f"
  #`pandoc $f -t docx -o $filename.doc`
  soffice --convert-to "xlsx" "$filename.xls"
  # uncomment this line to delete the source file.
  #mv "$filename" "$PREFIX/xls/$f"
done
cd ../
