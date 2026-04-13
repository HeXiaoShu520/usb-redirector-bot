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
    print("找到 USB Redirector 窗口")

    # 1. 查找并右键点击指定的设备（这里你需要输入它的完整名称）
    # 注意：这里改成了全量匹配，所以如果你测试，必须填写完整的节点字符串
    target_device = "Vector - USB Human Interface - Device\nDevice is plugged into 1-14 USB port"
    all_items = window.descendants(control_type="TreeItem")
    matched_items = [item for item in all_items if item.window_text() and item.window_text() == target_device]

    if not matched_items:
        print(f"未找到设备: {target_device}")
        sys.exit(1)

    device_item = matched_items[-1] # 取最后一个匹配项
    device_item.click_input() # 先左键选中
    time.sleep(0.3)
    device_item.right_click_input()
    print("已右键点击 Vector 设备，等待菜单弹出...")
    time.sleep(1.0) # 等待菜单渲染

    # 2. 在全桌面范围内查找弹出的菜单
    print("\n=== 正在捕获右键菜单 ===")

    # 方法 A: 查找类名为 #32768 (Windows 标准右键菜单类名) 或者类型为 Menu 的顶层窗口
    menu_found = False
    for top_win in desktop.windows():
        class_name = top_win.class_name()
        # Windows标准菜单类名通常是 #32768，或者 UIA 中识别为 Menu
        if class_name == '#32768' or 'menu' in class_name.lower() or 'popup' in class_name.lower():
            print(f"-> 成功抓取到弹出窗口 (类名: {class_name})")

            menu_items = top_win.descendants(control_type="MenuItem")
            for i, item in enumerate(menu_items):
                text = item.window_text()
                if text: # 过滤掉空项
                    status = "可用" if item.is_enabled() else "灰色/不可用"
                    print(f"  [{i}] {text} - 状态: {status}")

            menu_found = True

            # 如果找到我们想要的断开按钮，直接演示怎么点击
            for item in menu_items:
                if "Disconnect" in item.window_text():
                    print(f"\n*注：如果以后要断开，只需调用: item.click_input()*")
                    break

    if not menu_found:
        print("未能在桌面上捕获到弹出的右键菜单。")

except Exception as e:
    print(f"错误: {e}")
