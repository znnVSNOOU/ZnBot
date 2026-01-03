@echo off
echo 正在升级环境 (安装 ChromaDB + SQLite补丁)...
echo 注意：初次运行会自动下载模型，可能稍慢，请耐心等待。
echo --------------------------------
pip install PyQt5 requests pyinstaller psutil chromadb pysqlite3-binary
echo --------------------------------
echo 安装完成！
pause