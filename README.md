# 中国行政区划的经纬度坐标信息

中国行政区划数据来自于[中国政府网](https://www.mca.gov.cn/n156/n186/index.html)，而地理坐标信息来自于高德地区开放平台的[行政区划查询接口](https://lbs.amap.com/api/webservice/guide/api/district)。

代码是 ChatGPT 5.2 和 Claude Code 写的。我只负责审核，以及提供 api key。

行政区划截至日期是 2023 年；行政区划对应的经纬度坐标截至 2025 年 12 月 16 日。

**PS：** 如果只需要含数据本身，请下载这个文件 [xzqh_with_amap_coordinates.json](./xzqh_with_amap_coordinates.json)。

---

# 行政区划坐标数据处理工具

## 📁 数据文件

### 输入文件
- **`xzqh_2023_tree.json`** - 原始行政区划树状结构数据（3,209个行政区）
- **`region.json`** - 备用地理数据源（3,561个区域，覆盖率96.39%）

### 输出文件
- **`xzqh_result.json`** - 使用 region.json 匹配的结果（96.39%覆盖率）
- **`xzqh_with_amap_coordinates.json`** - 使用高德地图API的最终结果（99.94%覆盖率）✨ **推荐使用**

## 🛠 处理脚本

### 1. `process_xzqh.py` - 基础处理脚本
使用 region.json 匹配坐标数据

**功能：**
- 去除空的 children 字段
- 从 region.json 匹配地理中心坐标
- 生成 `xzqh_result.json`

**使用：**
```bash
python3 process_xzqh.py
```

**结果：**
- 覆盖率：96.39%（3,093/3,209）
- 未匹配：116个行政区

---

### 2. `update_coordinates_from_amap.py` - 高德地图API增强脚本 ⭐
使用高德地图API获取最新、最全的坐标数据

**功能：**
- 调用高德地图行政区划API
- 自动限流控制（QPS < 30）
- 按省级查询，subdistrict=2 获取三级数据
- 智能匹配行政区划代码
- 生成 `xzqh_with_amap_coordinates.json`

**使用：**
```bash
python3 update_coordinates_from_amap.py
```

**结果：**
- 覆盖率：99.94%（3,207/3,209）
- 未匹配：仅2个行政区（重庆市江北区、渝北区）
- API请求：34次（每省1次）
- 执行时间：约2秒

**API配置：**
```python
AMAP_API_KEY = "4a8be77cc644d042ef16ee0a5e194bfc"
AMAP_API_URL = "https://restapi.amap.com/v3/config/district"
REQUEST_INTERVAL = 0.04  # 40ms间隔，QPS=25
```

---

### 3. `check_missing_centers.py` - 坐标缺失检查工具
检查并列出缺失坐标的行政区

**使用：**
```bash
# 检查默认文件
python3 check_missing_centers.py

# 检查指定文件
python3 check_missing_centers.py xzqh_with_amap_coordinates.json
```

---

### 4. `compare_coverage.py` - 数据对比报告
对比不同数据源的覆盖率

**使用：**
```bash
python3 compare_coverage.py
```

**输出示例：**
```
📊 数据对比:
  数据源                                  总数      已覆盖        覆盖率
  ------------------------------------------------------------
  region.json (原始匹配)                 3209     3093     96.39%
  高德地图 API (新)                       3209     3207     99.94%
  ------------------------------------------------------------
  改进                                    0      114     +3.55%
```

---

## 📊 数据质量对比

| 数据源 | 覆盖率 | 未匹配数量 | 数据时效性 |
|--------|--------|-----------|-----------|
| region.json | 96.39% | 116个 | 静态数据 |
| **高德地图API** | **99.94%** | **2个** | **实时更新** ✨ |

**改进效果：**
- ✅ 新增覆盖 114 个行政区
- ✅ 覆盖率提升 3.55%
- ✅ 仅剩 2 个未覆盖（重庆市江北区、渝北区）

---

## 🎯 推荐使用

**最终数据文件：** `xzqh_with_amap_coordinates.json`

**数据结构：**
```json
{
  "code": "110000",
  "name": "北京市",
  "level": "province",
  "center": {
    "longitude": 116.407387,
    "latitude": 39.904179
  },
  "children": [...]
}
```

**特点：**
- ✅ 空 children 已清理
- ✅ 99.94% 坐标覆盖率
- ✅ 高德地图权威数据
- ✅ 经纬度精度高

---

## 🔧 高德地图API参考

**接口地址：**
```
https://restapi.amap.com/v3/config/district
```

**参数：**
- `keywords`: 查询关键字（省/市名称）
- `key`: API密钥
- `output`: 输出格式（JSON）
- `subdistrict`: 子级层数（0-3）

**示例：**
```bash
curl "https://restapi.amap.com/v3/config/district?\
keywords=北京市&\
key=4a8be77cc644d042ef16ee0a5e194bfc&\
output=JSON&\
subdistrict=2"
```

**限制：**
- QPS < 30（建议控制在25以下）
- 免费额度：每日30万次

---

## 📝 未匹配行政区说明

### 高德地图API数据（仅2个）
1. **重庆市江北区** (500105)
2. **重庆市渝北区** (500112)

*这两个区在高德地图数据库中暂无数据，可能与重庆直辖市的特殊行政区划结构有关。*

---

## 🚀 快速开始

```bash
# 1. 使用高德地图API更新所有坐标（推荐）
python3 update_coordinates_from_amap.py

# 2. 检查结果
python3 check_missing_centers.py xzqh_with_amap_coordinates.json

# 3. 查看对比报告
python3 compare_coverage.py
```

---

**创建日期：** 2025-12-16
**数据来源：** 高德地图开放平台 API
**覆盖率：** 99.94%
