#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pywinauto import Desktop
import time

try:
    desktop = Desktop(backend="uia")
    window = desktop.window(title="USB Redirector") # 试用版有后缀 - Evaluation version
    window.set_focus()
    print("找到 USB Redirector 窗口\n")

    print("=== USB 设备列表 ===")

    # 获取所有的 TreeItem (在界面左侧/中间的设备树)
    tree_items = window.descendants(control_type="TreeItem")

    if not tree_items:
        print("没有找到任何设备列表项。")
    else:
        for i, item in enumerate(tree_items):
            text = item.window_text()
            if text:
                print(f"[{i}] {text}")

except Exception as e:
    print(f"错误: {e}")
