#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update administrative division coordinates using Amap API.
- Prefer batch query for provinces (subdistrict=2)
- Query missing nodes individually using full names
- QPS limit < 30
"""

import json
import time
import urllib.parse
import urllib.request
import argparse
import os
from typing import Dict, Any, List, Optional, Tuple

# Amap API Configuration
AMAP_API_KEY = "4a8be77cc644d042ef16ee0a5e194bfc"
AMAP_API_URL = "https://restapi.amap.com/v3/config/district"
REQUEST_INTERVAL = 0.04  # 40ms interval, QPS=25

class AmapClient:
    """Amap API Client"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.request_count = 0
        self.last_request_time = 0

    def _throttle(self):
        """Rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        self.last_request_time = time.time()

    def query_district(self, keywords: str, subdistrict: int = 1) -> Optional[Dict[str, Any]]:
        """
        Query administrative division.

        Args:
            keywords: Keywords
            subdistrict: Subdistrict level

        Returns:
            JSON data from API, or None on failure.
        """
        self._throttle()
        encoded_keywords = urllib.parse.quote(keywords)
        url = f"{AMAP_API_URL}?keywords={encoded_keywords}&key={self.api_key}&output=JSON&subdistrict={subdistrict}"

        try:
            self.request_count += 1
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data.get('status') == '1' and data.get('infocode') == '10000':
                    return data
                else:
                    return None
        except Exception as e:
            print(f"  X Request exception: {keywords} - {str(e)}")
            return None

def collect_target_nodes(node: Dict[str, Any], targets: List[Dict[str, Any]]):
    """Collect target nodes (Province, Prefecture/City)"""
    # Strategy: Only query Province and Prefecture/City level.
    # subdistrict=1 or 2 will cover lower levels.
    if node.get('level') in ['province', 'prefecture']:
        targets.append(node)
    
    for child in node.get('children', []):
        collect_target_nodes(child, targets)

def process_query_result(target_node: Dict[str, Any], api_data: Dict[str, Any], stats: Dict[str, int]):
    """Process API result and update current node and its children"""
    if not api_data or not api_data.get('districts'):
        stats['fail'] += 1
        return

    # 1. Match current node
    matched_district = None
    target_code = str(target_node.get('code'))
    
    for d in api_data['districts']:
        if str(d.get('adcode')) == target_code:
            matched_district = d
            break
            
    if not matched_district:
        for d in api_data['districts']:
            if d.get('name') == target_node['name']:
                matched_district = d
                break
    
    if not matched_district and len(api_data['districts']) > 0:
        if api_data['districts'][0].get('name') == target_node['name']:
             matched_district = api_data['districts'][0]

    if matched_district:
        # Update current node coordinates
        center_str = matched_district.get('center')
        if center_str:
            try:
                lon, lat = center_str.split(',')
                target_node['center'] = {
                    'longitude': float(lon),
                    'latitude': float(lat)
                }
                stats['updated'] += 1
            except:
                pass
        
        # 2. Update children coordinates
        # Recursively flatten all sub-districts from API to handle intermediate layers (e.g. Beijing -> City Area -> District)
        sub_map = {}
        
        def flatten_districts(districts_list):
            for sub in districts_list:
                s_name = sub.get('name')
                s_center = sub.get('center')
                if s_name and s_center:
                    sub_map[s_name] = s_center
                
                if sub.get('districts'):
                    flatten_districts(sub['districts'])
        
        flatten_districts(matched_district.get('districts', []))
        
        # Iterate over target_node children and try to match
        if 'children' in target_node:
            for child in target_node['children']:
                child_name = child['name']
                # Try exact match first, then stripped match (for names like "仙桃市*")
                clean_name = child_name.strip('*')
                
                target_center = sub_map.get(child_name) or sub_map.get(clean_name)
                
                if target_center:
                    try:
                        lon, lat = target_center.split(',')
                        child['center'] = {
                            'longitude': float(lon),
                            'latitude': float(lat)
                        }
                        stats['updated_children'] += 1
                    except:
                        pass
        stats['success'] += 1
    else:
        stats['fail'] += 1
        print(f"  ! Failed to match API data: {target_node['name']} ({target_node['code']})")

def find_missing_nodes(node: Dict[str, Any], path: List[str], missing_list: List[Tuple[Dict[str, Any], str]]):
    """Find nodes missing coordinates"""
    current_path = path + [node['name']]
    
    if 'center' not in node:
        missing_list.append((node, "".join(current_path)))
    
    for child in node.get('children', []):
        find_missing_nodes(child, current_path, missing_list)

def main():
    parser = argparse.ArgumentParser(description="Update administrative division coordinates using Amap API.")
    parser.add_argument("--force", action="store_true", help="Force reload from original tree file (clean slate).")
    args = parser.parse_args()

    print("=" * 60)
    print("Update Admin Divisions Coordinates via Amap API")
    if args.force:
        print("RED: Force reset mode enabled. Reloading from original tree.")
    print("Strategy: Traverse Province/Prefecture nodes, use subdistrict=1/2 to cover lower levels.")
    print("=" * 60)

    # 1. Load Data
    input_file = 'xzqh_with_amap_coordinates.json'
    original_file = 'xzqh_2023_tree.json'
    output_file = 'xzqh_with_amap_coordinates.json'
    
    loaded_file = None
    
    if args.force and os.path.exists(original_file):
        loaded_file = original_file
        print(f"\n[1/5] (Force) Loading original file {loaded_file}...")
    elif os.path.exists(input_file):
        loaded_file = input_file
        print(f"\n[1/5] Loading existing file {loaded_file}...")
    elif os.path.exists(original_file):
        loaded_file = original_file
        print(f"\n[1/5] Loading original file {loaded_file} (existing not found)...")
    else:
        print("X Error: Data file not found (xzqh_with_amap_coordinates.json or xzqh_2023_tree.json)")
        return

    with open(loaded_file, 'r', encoding='utf-8') as f:
        xzqh_data = json.load(f)
            
    print(f"  V Loaded, total {len(xzqh_data)} provincial divisions")

    # 2. Collect targets
    print("\n[2/5] Analyzing structure, collecting targets...")
    target_nodes = []
    for node in xzqh_data:
        collect_target_nodes(node, target_nodes)
    print(f"  V Collected {len(target_nodes)} targets (Province + Prefecture)")

    # 3. Execute Query
    print(f"\n[3/5] Starting batch query ({len(target_nodes)} requests)...")
    client = AmapClient(AMAP_API_KEY)
    stats = {'success': 0, 'fail': 0, 'updated': 0, 'updated_children': 0}
    
    total = len(target_nodes)
    for idx, node in enumerate(target_nodes, 1):
        if idx % 20 == 0 or idx == total:
            print(f"\r  ...Progress: {idx}/{total} | Success: {stats['success']} | Node Upd: {stats['updated']} | Child Upd: {stats['updated_children']}", end='', flush=True)
        
        # Core Query
        # Use subdistrict=2 for Province to penetrate municipality virtual layers
        # Use subdistrict=1 for Prefecture
        sub_level = 2 if node.get('level') == 'province' else 1
        result = client.query_district(node['name'], subdistrict=sub_level)
        process_query_result(node, result, stats)
        
    print(f"\n  V Query phase completed")

    # 4. Check Missing (Report only)
    print(f"\n[4/5] Verifying coverage...")
    missing_nodes: List[Tuple[Dict[str, Any], str]] = []
    for node in xzqh_data:
        find_missing_nodes(node, [], missing_nodes)
    
    if len(missing_nodes) == 0:
        print("  V All nodes have coordinates!")
    else:
        print(f"  ! Warning: {len(missing_nodes)} nodes are still missing coordinates.")
        if len(missing_nodes) < 10:
            for node, name in missing_nodes:
                print(f"    - Missing: {name} ({node['code']})")
        else:
            print("    (Showing first 5 missing)")
            for i in range(5):
                print(f"    - Missing: {missing_nodes[i][1]} ({missing_nodes[i][0]['code']})")

    # 5. Cleanup and Save
    print(f"\n[5/5] Cleaning up and Saving to {output_file}...")
    
    def clean_empty_children(nodes: List[Dict[str, Any]]):
        """Recursively remove empty 'children' lists."""
        for node in nodes:
            if 'children' in node:
                if not node['children']:
                    del node['children']
                else:
                    clean_empty_children(node['children'])

    clean_empty_children(xzqh_data)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(xzqh_data, f, ensure_ascii=False, indent=2)
        
    print(f"  V Save completed!")

if __name__ == '__main__':
    main()
