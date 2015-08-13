#!/usr/bin/env python
# encoding: utf-8
"""
@author:     idhyt
@copyright:  2015 idhyt. All rights reserved.
@contact:
@date:       2015.07.30
@description:
"""
import re
import hashlib
import xml.dom.minidom
from common.uiautomator import device

from common.logger.Logger import Logger

import sys
reload(sys)
sys.setdefaultencoding("utf-8")


def output_log(log_string, is_print=False, is_write=False):
    if is_print is True:
        print str(log_string)
    if is_write is True:
        Logger.Write(log_string)


class ClickEventQueue():
    def __init__(self):
        self.clicked_bounds = []
        self.un_clicked_bounds = []
        self.xml_content_hash = []

    # bound = {"deep": 3, "bound": [(111, 111), (222, 222), (333, 333)]}
    def get_un_clicked_bound(self):
        try:
            return self.un_clicked_bounds.pop()
        except:
            Logger.WriteException()
            return None

    def add_un_clicked_bound(self, bound):
        self.un_clicked_bounds.insert(0, bound)

    def add_clicked_bound(self, bound):
        self.clicked_bounds.append(bound)

    def get_clicked_count(self):
        return len(self.clicked_bounds)

    def un_clicked_is_empty(self):
        return len(self.un_clicked_bounds) == 0

    def add_xml_content_hash(self, hash_value):
        self.xml_content_hash.append(hash_value)

    def xml_content_hash_exist(self, hash_value):
        return hash_value in self.xml_content_hash


class AutoClick():
    def __init__(self, adb_shell, package_name, main_activity_name):
        self.__adb_shell = adb_shell
        self.__package_name = package_name
        self.__main_activity_name = main_activity_name

        self.device = device
        self.nodes = None
        self.init_click_deep = 1
        self.stop_deep = 4

        self.point_pattern = re.compile(r"^\[(\d+),(\d+)\]\[(\d+),(\d+)\]", re.IGNORECASE)
        self._click_event_queue = None
        # init click event queue
        self.__init_click_event_queue()

    # get first screen click bound
    def __init_click_event_queue(self):
        self._click_event_queue = ClickEventQueue()

        xml_content = self.get_dump_xml()
        xml_content_hash = self.get_xml_content_hash(xml_content)
        self._click_event_queue.add_xml_content_hash(xml_content_hash)

        nodes = self.get_nodes(xml_content)
        click_able_nodes = self.get_click_able_nodes(nodes)
        for click_able_node in click_able_nodes:
            click_point = self.get_click_point(click_able_node["bounds"])
            if click_point is not None:
                self._click_event_queue.add_un_clicked_bound({"deep": self.init_click_deep,
                                                              "bounds": [click_point]})
            # save package name
            if self.__package_name is None:
                self.set_package_name(click_able_node["package"])

    def set_package_name(self, package_name):
        self.__package_name = package_name

    def get_dump_xml(self):
        return self.device.dump()

    def get_nodes(self, dump_xml, tag_name="node"):
        try:
            dom = xml.dom.minidom.parseString(dump_xml)
            root = dom.documentElement
            return root.getElementsByTagName(tag_name)
        except:
            Logger.WriteException()
            return None

    def get_click_able_nodes(self, nodes):
        click_able_nodes = []
        if nodes is not None and isinstance(nodes, list):
            for node in nodes:
                if node.hasAttribute("clickable") and node.getAttribute("clickable") == "true":
                    node_package = node.getAttribute("package")
                    node_bound = node.getAttribute("bounds")
                    click_able_nodes.append({"package": node_package, "bounds": node_bound})
        return click_able_nodes

    def get_click_point(self, click_bound):
        result = self.point_pattern.findall(click_bound)
        if len(result) > 0 and len(result[0]) == 4:
            x = int(result[0][0]) + (int(result[0][2]) - int(result[0][0]))/2
            y = int(result[0][1]) + (int(result[0][3]) - int(result[0][1]))/2
            return x, y
        return None

    # get xml content hash value
    def get_xml_content_hash(self, xml_content, hash_size=100000):
        if len(xml_content) > 256:
            xml_content_prefix, xml_content_suffix = xml_content[:256], xml_content[-256:]
        else:
            xml_content_prefix, xml_content_suffix = xml_content, xml_content
        xml_content_prefix_hash = hash(hashlib.new("md5", xml_content_prefix).hexdigest()) % (hash_size-1)
        xml_content_suffix_hash = hash(hashlib.new("md5", xml_content_suffix).hexdigest()) % (hash_size-1)
        xml_content_hash = hash(
            hashlib.new("md5", str(xml_content_prefix_hash + xml_content_suffix_hash)).hexdigest()
        ) % (hash_size-1)
        return xml_content_hash

    def get_current_ui_info(self):
        package_name = None
        xml_content = self.get_dump_xml()
        nodes = self.get_nodes(xml_content)
        for node in nodes:
            if node.hasAttribute("package"):
                package_name = node.getAttribute("package")
                break
        return package_name, xml_content

    def start_main_activity(self):
        self.__adb_shell.run_activity(self.__package_name, self.__main_activity_name)

    def verify_current_package(self):
        current_package_name, current_xml_content = self.get_current_ui_info()
        if current_package_name != self.__package_name:
            return False
        return True

    def verify_click_bound(self, click_deep, click_points):
        # if click deep greater than stop deep or not equal click point numbers, maybe some where error and ignore it
        if click_deep > self.stop_deep | click_deep != len(click_points):
            return False
        return True

    def click_points_event(self, click_points):
        for click_point in click_points:
            x, y = click_point[0], click_point[1]
            self.device.click(x, y)
            self.device.wait.update()

    def back_to_main_activity(self, click_deep):
        for i in range(click_deep, 0, -1):
            self.device.press.back()
            self.device.wait.update()

    def update_new_bounds_to_queue(self, xml_content, origin_click_deep, origin_click_points):
        nodes = self.get_nodes(xml_content)
        click_able_nodes = self.get_click_able_nodes(nodes)
        for click_able_node in click_able_nodes:
            # if jump other app then ignore it and restart first screen
            if click_able_node["package"] == self.__package_name:
                # get the new xml click point and add queue
                new_click_point = self.get_click_point(click_able_node["bounds"])
                if new_click_point is not None:
                    new_click_bounds = origin_click_points[:]
                    new_click_bounds.append(new_click_point)
                    self._click_event_queue.add_un_clicked_bound({"deep": origin_click_deep + 1,
                                                                  "bounds": new_click_bounds})

    def click_event_begin(self, stop_click_count=1000):
        while self._click_event_queue.un_clicked_is_empty() is False \
                and self._click_event_queue.get_clicked_count > stop_click_count:
            try:
                # ensure current ui is target app ui
                if self.verify_current_package() is False:
                    self.start_main_activity()

                # get click bound
                un_clicked_bound = self._click_event_queue.get_un_clicked_bound()
                if un_clicked_bound is None:
                    continue
                output_log("[*] pop out one click event on %s" % un_clicked_bound["bounds"], is_print=True)

                # add the bound into clicked bounds queue
                self._click_event_queue.add_clicked_bound(un_clicked_bound)

                click_deep, click_points = un_clicked_bound["deep"], un_clicked_bound["bounds"]

                # check click deep
                if self.verify_click_bound(click_deep, click_points) is False:
                    continue

                # click event
                self.click_points_event(click_points)

                # check new ui is target app ui or not, if not, then ignore it
                current_package_name, current_xml_content = self.get_current_ui_info()
                if current_package_name != self.__package_name:
                    self.start_main_activity()
                    continue

                # get new xml content, if it is exist, back to main and ignore it
                xml_content_hash = self.get_xml_content_hash(current_xml_content)
                if self._click_event_queue.xml_content_hash_exist(xml_content_hash) is True:
                    self.back_to_main_activity(click_deep)
                    continue

                # if the new xml is not exist then get all click bound and save it
                self._click_event_queue.add_xml_content_hash(xml_content_hash)
                self.update_new_bounds_to_queue(current_xml_content, click_deep, click_points)

                # go back the first screen
                self.back_to_main_activity(click_deep)
            except:
                Logger.WriteException()

        return True


def auto_click_work(adb_shell, package_name, main_activity_name):
    auto_click = AutoClick(adb_shell, package_name, main_activity_name)
    auto_click.click_event_begin()


if __name__ == "__main__":
    # auto_click_work(None, None, None)
    # ----- test code -----
    from common.adb.adb_base import create_adb_shell
    test_adb_shell = create_adb_shell(r"D:\develop\android-sdk\platform-tools\adb.exe", "192.168.56.101", 5555)
    test_adb_shell.restart_server()
    test_adb_shell.connect()
    auto_click_work(test_adb_shell, "com.tencent.mobileqq", ".activity.SplashActivity")
    # ----- end -----