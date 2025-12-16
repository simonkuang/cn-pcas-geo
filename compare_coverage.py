#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比两个数据文件的坐标覆盖率"""

import json


def count_coverage(data):
    """统计坐标覆盖率"""
    total = 0
    covered = 0

    def count_node(node):
        nonlocal total, covered
        total += 1
        if 'center' in node:
            covered += 1
        for child in node.get('children', []):
            count_node(child)

    for node in data:
        count_node(node)

    return total, covered


def main():
    # 加载原始数据（从region.json匹配）
    print("=" * 70)
    print("行政区划坐标数据对比报告")
    print("=" * 70)

    with open('xzqh_result.json', 'r', encoding='utf-8') as f:
        old_data = json.load(f)

    # 加载新数据（从高德地图API获取）
    with open('xzqh_with_amap_coordinates.json', 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    # 统计覆盖率
    old_total, old_covered = count_coverage(old_data)
    new_total, new_covered = count_coverage(new_data)

    print(f"\n📊 数据对比:\n")
    print(f"  {'数据源':<30} {'总数':>8} {'已覆盖':>8} {'覆盖率':>10}")
    print(f"  {'-' * 60}")
    print(f"  {'region.json (原始匹配)':<30} {old_total:>8} {old_covered:>8} {old_covered/old_total*100:>9.2f}%")
    print(f"  {'高德地图 API (新)':<30} {new_total:>8} {new_covered:>8} {new_covered/new_total*100:>9.2f}%")
    print(f"  {'-' * 60}")
    print(f"  {'改进':<30} {new_total-old_total:>8} {new_covered-old_covered:>8} {(new_covered/new_total - old_covered/old_total)*100:>+9.2f}%")

    print(f"\n✅ 改进效果:")
    print(f"  - 新增覆盖: {new_covered - old_covered} 个行政区")
    print(f"  - 覆盖率提升: {(new_covered/new_total - old_covered/old_total)*100:.2f}%")
    print(f"  - 未覆盖: {new_total - new_covered} 个行政区 ({(new_total-new_covered)/new_total*100:.3f}%)")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
