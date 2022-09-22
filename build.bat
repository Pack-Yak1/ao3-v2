pyinstaller src\main.py ^
--paths src ^
--noconfirm ^
--name "AO3 Tools" ^
--add-data src\schema\schema.sql;schema ^
--add-data src\config\default.json;config ^
--add-binary src\fonts\NotoSerifJP-Regular.otf;fonts