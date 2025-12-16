#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行政区划数据处理脚本
功能：
1. 去掉空的 children 字段
2. 从 region.json 匹配地理中心坐标
3. 输出到新文件
"""

import json
from typing import Dict, Any, Optional


def build_region_center_map(region_data: Dict[str, Any], center_map: Dict[str, Dict[str, float]]) -> None:
    """
    递归构建区域名称到中心坐标的映射

    Args:
        region_data: region.json 中的区域数据
        center_map: 输出的映射字典 {name: {longitude, latitude}}
    """
    name = region_data.get('name')
    center = region_data.get('center')

    # 如果有名称和中心坐标，加入映射
    if name and center:
        center_map[name] = center

    # 递归处理下级区域
    districts = region_data.get('districts', [])
    for district in districts:
        build_region_center_map(district, center_map)


def process_xzqh_node(node: Dict[str, Any], center_map: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    递归处理 xzqh 节点

    Args:
        node: xzqh 中的节点
        center_map: 区域名称到中心坐标的映射

    Returns:
        处理后的节点
    """
    result = {
        'code': node['code'],
        'name': node['name'],
        'level': node['level']
    }

    # 尝试从 region 数据中查找中心坐标
    name = node['name']
    if name in center_map:
        result['center'] = center_map[name]

    # 处理 children
    children = node.get('children', [])
    if children:  # 只有非空数组才处理
        processed_children = [process_xzqh_node(child, center_map) for child in children]
        result['children'] = processed_children
    # 空数组不添加 children 字段

    return result


def main():
    """主函数"""
    print("开始加载数据文件...")

    # 加载 xzqh 数据
    print("加载 xzqh_2023_tree.json...")
    with open('xzqh_2023_tree.json', 'r', encoding='utf-8') as f:
        xzqh_data = json.load(f)
    print(f"  加载完成，共 {len(xzqh_data)} 个省级行政区")

    # 加载 region 数据
    print("加载 region.json...")
    with open('region.json', 'r', encoding='utf-8') as f:
        region_data = json.load(f)
    print("  加载完成")

    # 构建区域名称到中心坐标的映射
    print("构建区域坐标映射...")
    center_map: Dict[str, Dict[str, float]] = {}
    build_region_center_map(region_data, center_map)
    print(f"  映射完成，共 {len(center_map)} 个区域有坐标数据")

    # 处理 xzqh 数据
    print("处理 xzqh 数据...")
    result_data = [process_xzqh_node(node, center_map) for node in xzqh_data]

    # 统计匹配情况
    total_count = 0
    matched_count = 0

    def count_nodes(node: Dict[str, Any]) -> None:
        nonlocal total_count, matched_count
        total_count += 1
        if 'center' in node:
            matched_count += 1
        for child in node.get('children', []):
            count_nodes(child)

    for node in result_data:
        count_nodes(node)

    print(f"  处理完成，共 {total_count} 个行政区划，匹配到坐标 {matched_count} 个 ({matched_count/total_count*100:.1f}%)")

    # 输出到新文件
    output_file = 'xzqh_result.json'
    print(f"输出结果到 {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 处理完成！结果已保存到 {output_file}")


if __name__ == '__main__':
    main()
