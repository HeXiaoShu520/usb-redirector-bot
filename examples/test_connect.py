#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pywinauto.application import Application

try:
    app = Application(backend="uia").connect(path="usbredirector.exe")
    windows = app.windows()

    print(f"找到 {len(windows)} 个窗口")
    for win in windows:
        title = win.window_text()
        print(f"\n窗口标题: {title}")

        tree_items = win.descendants(control_type="TreeItem")
        print(f"设备数量: {len(tree_items)}")
        for i, item in enumerate(tree_items):
            print(f"  {i+1}. {item.window_text()}")

except Exception as e:
    print(f"错误: {e}")
