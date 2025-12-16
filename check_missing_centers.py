#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查缺失坐标的行政区"""

import json


def find_missing_centers(node, path=""):
    """递归查找缺失中心坐标的节点"""
    missing = []
    current_path = f"{path}/{node['name']}" if path else node['name']

    if 'center' not in node:
        missing.append({
            'path': current_path,
            'code': node['code'],
            'name': node['name'],
            'level': node['level']
        })

    for child in node.get('children', []):
        missing.extend(find_missing_centers(child, current_path))

    return missing


def main():
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else 'xzqh_result.json'

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"检查文件: {filename}\n")

    all_missing = []
    for node in data:
        all_missing.extend(find_missing_centers(node))

    print(f"共发现 {len(all_missing)} 个行政区缺失坐标数据：\n")

    for item in all_missing:
        print(f"  [{item['level']:8}] {item['code']} - {item['name']}")
        print(f"               路径: {item['path']}")
        print()


if __name__ == '__main__':
    main()
