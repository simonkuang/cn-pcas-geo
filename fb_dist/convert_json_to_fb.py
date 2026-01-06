import json
import os
import sys

# Ensure the flatbuffers library is available
try:
    import flatbuffers
except ImportError:
    print("Error: 'flatbuffers' python library is not installed.")
    print("Please install it using: pip install flatbuffers")
    sys.exit(1)

# Ensure the generated XZQH module is available
# This assumes the user has run: flatc --python xzqh.fbs
sys.path.append(os.getcwd()) 

try:
    import XZQH.Data
    import XZQH.Region
    import XZQH.Level
    import XZQH.Coordinate
except ImportError:
    print("Error: Generated FlatBuffers code not found.")
    print("Please run: flatc --python xzqh.fbs")
    sys.exit(1)

def map_level(level_str):
    level_str = level_str.lower()
    if level_str == "province":
        return XZQH.Level.Level.Province
    elif level_str == "prefecture":
        return XZQH.Level.Level.Prefecture
    elif level_str == "county":
        return XZQH.Level.Level.County
    # Default fallback, though data seems clean
    return XZQH.Level.Level.Province

def create_region(builder, node):
    # 1. Recursively create children first (Bottom-Up)
    child_offsets = []
    if "children" in node and node["children"]:
        for child in node["children"]:
            child_offsets.append(create_region(builder, child))
    
    # 2. Create Children Vector if any
    children_vector = None
    if child_offsets:
        XZQH.Region.RegionStartChildrenVector(builder, len(child_offsets))
        # Prepend in reverse order
        for offset in reversed(child_offsets):
            builder.PrependUOffsetTRelative(offset)
        children_vector = builder.EndVector()

    # 3. Create Strings
    code_str = builder.CreateString(str(node.get("code", "")))
    name_str = builder.CreateString(node.get("name", ""))

    # 4. Start Region Table
    XZQH.Region.RegionStart(builder)
    
    XZQH.Region.RegionAddCode(builder, code_str)
    XZQH.Region.RegionAddName(builder, name_str)
    
    # Level
    level_val = map_level(node.get("level", ""))
    XZQH.Region.RegionAddLevel(builder, level_val)
    
    # Center (Struct)
    # Structs are inline, so we usually use the CreateCoordinate method generated 
    # if it's a helper, or we pass the struct fields directly to a builder method 
    # depending on generated code style.
    # For Structs, FlatBuffers Python typically provides a method like:
    # RegionAddCenter(builder, longitude, latitude) -> Wait, no.
    # It usually requires creating the struct manually inline during table construction?
    # Actually, for Structs, we typically call builder.PrependStructSlot or specific generated method.
    # Let's check typical generated code pattern for Structs.
    # It usually is: XZQH.Region.RegionAddCenter(builder, XZQH.Coordinate.CreateCoordinate(builder, lng, lat))
    
    center_data = node.get("center", {})
    lng = float(center_data.get("longitude", 0.0))
    lat = float(center_data.get("latitude", 0.0))
    
    # CreateCoordinate is a helper function in the Generated Coordinate.py typically
    # But wait, CreateCoordinate returns an offset? No, Structs are value types.
    # In Python, we usually call CreateCoordinate(builder, lng, lat) and it returns an offset 
    # representing where the struct was written in the buffer (prepended).
    center_offset = XZQH.Coordinate.CreateCoordinate(builder, lng, lat)
    XZQH.Region.RegionAddCenter(builder, center_offset)

    if children_vector:
        XZQH.Region.RegionAddChildren(builder, children_vector)

    return XZQH.Region.RegionEnd(builder)

def main():
    json_path = os.path.join(os.path.dirname(__file__), "..", "xzqh_with_amap_coordinates.json")
    output_path = "xzqh.bin"

    if not os.path.exists(json_path):
        print(f"Error: JSON file not found at {json_path}")
        sys.exit(1)

    print(f"Reading {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    builder = flatbuffers.Builder(1024)

    # The root of JSON is a List of Regions (Provinces)
    # But our Schema Root is "Data" which contains "root: [Region]"
    
    # 1. Create all root regions
    root_offsets = []
    for item in data:
        root_offsets.append(create_region(builder, item))
    
    # 2. Create the Vector for Data.root
    XZQH.Data.DataStartRootVector(builder, len(root_offsets))
    for offset in reversed(root_offsets):
        builder.PrependUOffsetTRelative(offset)
    root_vector = builder.EndVector()

    # 3. Create Data Table
    XZQH.Data.DataStart(builder)
    XZQH.Data.DataAddRoot(builder, root_vector)
    final_data = XZQH.Data.DataEnd(builder)

    builder.Finish(final_data)

    buf = builder.Output()
    
    print(f"Writing {len(buf)} bytes to {output_path}...")
    with open(output_path, "wb") as f:
        f.write(buf)
    
    print("Done.")

if __name__ == "__main__":
    main()
