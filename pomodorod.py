#!/usr/bin/env python

"""
Pomodoro daemon with JSON-RPC interface and sound notifications.
"""

from datetime import datetime, timedelta

from rpc_api import RPCApi
from pygame import mixer
from time import sleep

class PomodoroMonitor():
    monitor_enabled = False
    is_work_period = False
    period_paused = False
    time_since_current_event_start = None
    notification_acknowledged = False

    break_alert_path = 'deskbell.wav'
    work_alert_path = 'crank.wav'

    def __init__(self, work_time=45, break_time=15):
        self.work_time = work_time
        self.break_time = break_time

    def get_time_left(self):
        delta = int((self.end_time - datetime.now()).total_seconds())
        if delta < 0:
            return 0, 0
        return delta / 60, delta % 60

    def start_break(self):
        self.monitor_enabled = True
        self.is_work_period = False
        self.end_time = datetime.now() + timedelta(minutes = self.break_time)

    def start_work(self):
        self.monitor_enabled = True
        self.is_work_period = True
        self.end_time = datetime.now() + timedelta(minutes = self.work_time)

    def break_work(self):
        self.monitor_enabled = False
        self.end_time = None

    def play_work_alert(self):
        self.play_alert(self.work_alert_path)

    def play_break_alert(self):
        self.play_alert(self.break_alert_path)

    def play_alert(self, alert_path):
        mixer.init()               
        mixer.music.stop()
        mixer.music.load(alert_path)
        mixer.music.play()         

    def run(self):
        #possible_states = ["notifying", "working"]
        self.state = "working"
        while True:
            self.run_once()
            sleep(1)

    def run_once(self):
        if not self.monitor_enabled:
            return
        if self.state == "working": #Daemon checking time from time to time
            now = datetime.now()
            if now >= self.end_time:  #Time out!
                self.is_work_period = not self.is_work_period
                if self.is_work_period:
                    self.start_work()
                else:
                    self.start_break()
                self.notification_acknowledged = False
                self.state = "notifying"
        elif self.state == "notifying": #Daemon is playing sounds - new period has been set already
            if self.notification_acknowledged:
                self.state = "working" #Back to working state
            else:
                if self.is_work_period: 
                    self.play_work_alert()
                else:
                    self.play_break_alert()
                sleep(3)
                
    def attach_api(self, api):
        self.api = api
        self.api.register_function(self.api_get_status, "get_status")
        self.api.register_function(self.api_start_work, "start_work")
        self.api.register_function(self.api_break_work, "break_work")
        #self.api.register_function(self.api_get_status, "pause_work")
        self.api.register_function(self.api_ack_notification, "acknowledge_notification")

    def api_get_status(self):
        status_str = ""
        if self.monitor_enabled:
            if self.period_paused:
                status_str = "Paused, "
            else:
                status_str = "Running, "
            if self.is_work_period:
                status_str += "work"
            else:
                status_str += "break"
            mins, secs = self.get_time_left()
            time_left_str = "{}:{} left".format(mins, secs)
        else:
            status_str = "Not running"
            time_left_str = "0:00 left"
        return [status_str, time_left_str]

    def api_start_work(self):
        self.start_work()

    def api_break_work(self):
        self.break_work()

    def api_ack_notification(self):
        self.notification_acknowledged = True


if __name__ == "__main__":
    monitor = PomodoroMonitor()
    api = RPCApi({"rpc_host":"127.0.0.1", "rpc_port":4515})
    monitor.attach_api(api)
    api.start_thread()
    monitor.run()
