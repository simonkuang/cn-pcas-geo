#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用高德地图API更新行政区划坐标
- 使用省级查询 + subdistrict=2 获取三级数据
- QPS限制 <30（实际控制在25）
- 智能匹配行政区划代码
"""

import json
import time
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional


# 高德地图API配置
AMAP_API_KEY = "4a8be77cc644d042ef16ee0a5e194bfc"
AMAP_API_URL = "https://restapi.amap.com/v3/config/district"
REQUEST_INTERVAL = 0.04  # 40ms间隔，QPS=25


class AmapClient:
    """高德地图API客户端"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.request_count = 0
        self.last_request_time = 0

    def _throttle(self):
        """限流控制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        self.last_request_time = time.time()

    def query_district(self, keywords: str, subdistrict: int = 2) -> Optional[Dict[str, Any]]:
        """
        查询行政区划

        Args:
            keywords: 关键字（建议使用省或市名称）
            subdistrict: 下级层级（0=不返回下级，1=返回下一级，2=返回下两级，3=返回下三级）

        Returns:
            API返回的JSON数据，失败返回None
        """
        self._throttle()

        # URL编码
        encoded_keywords = urllib.parse.quote(keywords)

        # 构建请求URL
        url = f"{AMAP_API_URL}?keywords={encoded_keywords}&key={self.api_key}&output=JSON&subdistrict={subdistrict}"

        try:
            self.request_count += 1
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                if data.get('status') == '1' and data.get('infocode') == '10000':
                    return data
                else:
                    print(f"  ⚠️  查询失败: {keywords} - {data.get('info')}")
                    return None

        except Exception as e:
            print(f"  ❌ 请求异常: {keywords} - {str(e)}")
            return None


def build_amap_index(districts: List[Dict[str, Any]], index: Dict[str, Dict[str, Any]]):
    """
    递归构建行政区划代码索引

    Args:
        districts: 高德地图返回的districts数组
        index: 输出索引 {adcode: {name, center, level}}
    """
    for district in districts:
        adcode = district.get('adcode')
        name = district.get('name')
        center_str = district.get('center')
        level = district.get('level')

        # 解析中心坐标 "经度,纬度"
        if adcode and center_str:
            try:
                lon, lat = center_str.split(',')
                index[adcode] = {
                    'name': name,
                    'center': {
                        'longitude': float(lon),
                        'latitude': float(lat)
                    },
                    'level': level
                }
            except (ValueError, AttributeError):
                pass

        # 递归处理下级行政区
        sub_districts = district.get('districts', [])
        if sub_districts:
            build_amap_index(sub_districts, index)


def process_xzqh_node(node: Dict[str, Any], amap_index: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    递归处理xzqh节点，填充坐标

    Args:
        node: xzqh节点
        amap_index: 高德地图数据索引

    Returns:
        处理后的节点
    """
    result = {
        'code': node['code'],
        'name': node['name'],
        'level': node['level']
    }

    # 从高德地图数据中查找坐标
    code = node['code']
    if code in amap_index:
        result['center'] = amap_index[code]['center']

    # 处理children
    children = node.get('children', [])
    if children:
        processed_children = [process_xzqh_node(child, amap_index) for child in children]
        result['children'] = processed_children

    return result


def main():
    """主函数"""
    print("=" * 60)
    print("使用高德地图API更新行政区划坐标")
    print("=" * 60)

    # 1. 加载xzqh数据
    print("\n[1/5] 加载 xzqh_2023_tree.json...")
    with open('xzqh_2023_tree.json', 'r', encoding='utf-8') as f:
        xzqh_data = json.load(f)
    print(f"  ✓ 加载完成，共 {len(xzqh_data)} 个省级行政区")

    # 2. 初始化高德地图客户端
    print("\n[2/5] 初始化高德地图API客户端...")
    client = AmapClient(AMAP_API_KEY)
    print(f"  ✓ 初始化完成，QPS限制: {1/REQUEST_INTERVAL:.1f}")

    # 3. 查询所有省级行政区数据
    print("\n[3/5] 查询高德地图数据...")
    amap_index: Dict[str, Dict[str, Any]] = {}

    total_provinces = len(xzqh_data)
    for idx, province in enumerate(xzqh_data, 1):
        province_name = province['name']
        print(f"  [{idx:2d}/{total_provinces}] 查询: {province_name} ...")

        # 使用省名查询，subdistrict=2获取省、市、县三级数据
        result = client.query_district(province_name, subdistrict=2)

        if result and result.get('districts'):
            # 构建索引
            build_amap_index(result['districts'], amap_index)
            print(f"         ✓ 成功，当前索引: {len(amap_index)} 个行政区")
        else:
            print(f"         ✗ 查询失败")

    print(f"\n  ✓ 查询完成！")
    print(f"    - 总请求数: {client.request_count}")
    print(f"    - 索引数据: {len(amap_index)} 个行政区")

    # 4. 更新xzqh数据
    print("\n[4/5] 更新 xzqh 数据...")
    result_data = [process_xzqh_node(node, amap_index) for node in xzqh_data]

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

    print(f"  ✓ 更新完成")
    print(f"    - 总行政区: {total_count}")
    print(f"    - 已匹配: {matched_count} ({matched_count/total_count*100:.1f}%)")
    print(f"    - 未匹配: {total_count - matched_count}")

    # 5. 保存结果
    output_file = 'xzqh_with_amap_coordinates.json'
    print(f"\n[5/5] 保存结果到 {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"  ✓ 保存完成！")
    print("\n" + "=" * 60)
    print("✅ 所有任务完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
