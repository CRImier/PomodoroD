cp . /opt/pomodorod/ -r
cd /opt/pomodorod/

chmod +x pomodorod.py
cp pomodorod.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable pomodorod.service
systemctl start pomodorod.service

