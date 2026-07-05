@echo off
REM clip_bot daily cronjob — queue.txt ke naye videos process + post karta hai
REM Windows Task Scheduler isko roz chalayega. Log: data\daily.log
cd /d c:\xampp\htdocs\pr\clip_bot
echo ===== RUN %date% %time% ===== >> data\daily.log
python src\pipeline.py --queue --post >> data\daily.log 2>&1
