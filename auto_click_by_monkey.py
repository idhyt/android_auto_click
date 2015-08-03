#!/usr/bin/env python
# encoding: utf-8
"""
@author:     idhyt
@copyright:  2015 idhyt. All rights reserved.
@contact:
@date:       2015年07月07日
@description:
"""
from common.logger.Logger import Logger


class SimulateClick():
    def __init__(self):
        self.__adb_shell = None
        self.__start_activity = []
        self.__monkey = "adb shell monkey -p"
        self.__package_name = ""
        self.__seed = "-s 470"
        self.__delay = "--throttle 500"
        self.__pct_event = "--pct-touch 50"
        self.__ignore_event = "--ignore-crashes " \
                              "--ignore-timeouts " \
                              "--ignore-security-exceptions " \
                              "--ignore-native-crashes " \
                              "--monitor-native-crashes"
        self.__log_level = "-v"
        self.__event_count = "500"

    def set_adb_shell(self, adb_shell):
        self.__adb_shell = adb_shell

    def set_start_activity(self, activity):
        if isinstance(activity, list):
            self.__start_activity = activity

    def set_package_name(self, package_name):
        self.__package_name = package_name

    def set_seed(self, seed):
        self.__seed = " ".join(["-s", str(seed)])

    def set_delay(self, millisecond):
        self.__delay = " ".join(["--throttle", str(millisecond)])

    def set_pct_event(self, pct_event):
        self.__pct_event = pct_event

    def set_ignore_event(self, ignore_event):
        self.__ignore_event = ignore_event

    def set_log_level(self, log_level):
        self.__log_level = log_level

    def set_event_count(self, event_count):
        self.__event_count = event_count

    def get_click_event_command(self):
        """eg:
        monkey_command = "monkey -p com.android.mms " \
                         "-s 470 --throttle 500 --pct-touch 90 " \
                         "--ignore-crashes --ignore-timeouts --ignore-security-exceptions " \
                         "--ignore-native-crashes --monitor-native-crashes -v -v -v 15000"
        """
        click_event_command = " ".join([self.__monkey,
                                        self.__package_name,
                                        self.__seed,
                                        self.__delay,
                                        self.__pct_event,
                                        self.__ignore_event,
                                        self.__log_level,
                                        self.__event_count])
        return click_event_command

    def get_start_activity_command(self, activity):
        start_activity = "/".join([self.__package_name, activity])
        start_activity_command = " ".join(["adb shell am start -n", start_activity])
        return start_activity_command

    # 随机点击事件函数
    def random_click(self):
        if self.__adb_shell is None:
            return False
        click_event_command = self.get_click_event_command()
        # print click_event_command
        Logger.Write(click_event_command)
        for activity in self.__start_activity:
            # start_activity_command = self.get_start_activity_command(activity)
            # print start_activity_command
            # Logger.Write(start_activity_command)
            # 启动activity
            self.__adb_shell.run_activity(self.__package_name, activity)
            # 启动点击命令
            self.__adb_shell.run_cmd(click_event_command)


def click_begin(package_name, activity_list, adb_shell):
    simulate_click = SimulateClick()
    simulate_click.set_package_name(package_name)
    simulate_click.set_start_activity(activity_list)
    simulate_click.set_adb_shell(adb_shell)
    simulate_click.random_click()

if __name__ == '__main__':
    activities = ["com.vkoov8135.login.LoginActivity",
                  "com.vkoov8135.YaloeActivity"]
    click_begin("com.yaloe8135", activities)