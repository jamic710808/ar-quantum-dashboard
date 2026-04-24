@echo off
chcp 65001 > nul
echo 正在建立 V5.7 與 index.html...
copy "AR 量子智慧戰情室 V5.6_AI.html" "AR 量子智慧戰情室 V5.7_AI.html" /Y
copy "AR 量子智慧戰情室 V5.6_AI.html" "index.html" /Y
echo.
echo 完成！已建立：
echo   AR 量子智慧戰情室 V5.7_AI.html
echo   index.html  (Vercel 部署用)
echo.
pause
