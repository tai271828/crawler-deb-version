#!/bin/bash
#
# crontab -e
# 0 2 * * * /home/dev/crontab_daily-script_crawler-deb-version.sh
#
export PATH=$PATH:/home/dev/.local/bin
source /home/dev/sendgrid_var.sh

cd /home/dev/work-my-projects/crawler/crawler-deb-version
git pull
poetry run ./crawler-deb-version.py

