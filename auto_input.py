#!/usr/bin/env python
# encoding: utf-8
"""
@author:     idhyt
@copyright:  2015 idhyt. All rights reserved.
@contact:
@date:       2015.08.18
@description:
"""
import os
import re
import json
import time

from common.logger.Logger import Logger
import auto_click


class AutoInput():
    def __init__(self, device):
        self.__device = device

        self.payloads = json.load(open("\\".join([os.path.split(os.path.realpath(__file__))[0], "payloads.json"])))
        self.edit_text_class_name = "android.widget.EditText"
        self.input_delay = 0.5

    @staticmethod
    def is_match_rule(attr_content, rule):
        if isinstance(rule, list) and not not attr_content:
            for r in rule:
                if re.findall(r, attr_content):
                    return True

        return False

    # ignore input payload, like QQ search, if ignore, return True
    def is_ignore_input_payload(self, attr_content):
        if self.is_match_rule(attr_content, self.payloads["ignore"]):
            return True
        return False

    # get nodes which class name equal android.widget.EditText
    def get_edit_text_nodes(self, nodes):
        edit_text_nodes = []
        if isinstance(nodes, list):
            for node in nodes:
                if node.hasAttribute("class") and node.getAttribute("class") == self.edit_text_class_name \
                        and node.hasAttribute("focusable") and node.getAttribute("focusable") == "true":
                    edit_text_nodes.append(node)
        return edit_text_nodes

    # get test payload by node tag
    def get_payload(self, node):
        text_attr_content, desc_attr_content = "", ""
        if node.hasAttribute("text"):
            text_attr_content = node.getAttribute("text")
        if node.hasAttribute("content-desc"):
            desc_attr_content = node.getAttribute("content-desc")

        # ignore input payload
        if self.is_ignore_input_payload(text_attr_content) \
                or self.is_ignore_input_payload(desc_attr_content):
            return None

        # phone number?
        if self.is_match_rule(text_attr_content, self.payloads["phone"]["tag"]) \
                or self.is_match_rule(desc_attr_content, self.payloads["phone"]["tag"]):
            return self.payloads["phone"]["payload"]

        # password?
        if node.hasAttribute("password"):
            pwd_attr = node.getAttribute("password")
            if pwd_attr == "true":
                return self.payloads["password"]["payload"]

        # verify code?
        if self.is_match_rule(text_attr_content, self.payloads["verify_code"]["tag"]) \
                or self.is_match_rule(desc_attr_content, self.payloads["verify_code"]["tag"]):
            return self.payloads["verify_code"]["payload"]

        return self.payloads["default"]

    # input payload, like find password, change phone number and so on.
    def input_payload(self, edit_text_nodes):
        if isinstance(edit_text_nodes, list):
            for index, edit_text_node in enumerate(edit_text_nodes):
                input_text = self.get_payload(edit_text_node)
                if input_text is not None:
                    self.__device(className="android.widget.EditText",
                                  focusable="true")[index].set_text(input_text)
                    time.sleep(self.input_delay)
        return True

    # simulate input password and other text
    def simulate_input_text(self):
        try:
            xml_content = self.__device.dump()
            nodes = auto_click.AutoClick.get_nodes(xml_content)
            if nodes is not None:
                edit_text_nodes = self.get_edit_text_nodes(nodes)
                self.input_payload(edit_text_nodes)
            return True
        except:
            Logger.WriteException()
            return False

if __name__ == "__main__":
    from common.uiautomator import device as d
    auto_input_ = AutoInput(d)
    auto_input_.simulate_input_text()
