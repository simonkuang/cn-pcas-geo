# CN XZQH Library (WASM + FlatBuffers)

这是一个高性能、极小体积的中国行政区划查询库。基于 **WebAssembly** 和 **Google FlatBuffers** 构建。

## 目录结构

```
cn_xzqh_lib/
├── dist/                  # 核心资源文件 (部署时仅需此目录)
│   ├── xzqh.bin           # 数据文件 (FlatBuffers Binary)
│   ├── xzqh_core.js       # WASM 胶水代码 (Emscripten)
│   └── xzqh_core.wasm     # WASM 核心逻辑
├── xzqh_loader.js         # JS SDK 封装 (提供易用的 API)
└── demo.html              # 示例页面
```

## 快速开始

### 1. 引入文件

在您的 HTML 中引入 SDK 和核心胶水代码：

```html
<!-- 必须先引入胶水代码 -->
<script src="path/to/dist/xzqh_core.js"></script>
<!-- 引入 SDK -->
<script src="path/to/xzqh_loader.js"></script>
```

### 2. 初始化

```javascript
// 初始化库 (指定资源路径)
const db = await XZQH.load({
    dataUrl: 'dist/xzqh.bin',       // 数据文件路径
    wasmUrl: 'dist/xzqh_core.wasm'  // WASM 文件路径
});

console.log("Database Ready!");
```

### 3. 查询数据

**获取所有省份：**
```javascript
const provinces = db.getProvinces();
// -> [{name: "北京市", code: "110000", index: 0}, ...]
```

**获取市列表：**
```javascript
// 传入省份的 index (不是 code)
const cities = db.getCities(0);
// -> [{name: "市辖区", code: "110100", index: 0}, ...]
```

**获取区县列表：**
```javascript
const counties = db.getCounties(0, 0); 
// -> [{name: "东城区", code: "110101", index: 0}, ...]
```

**获取详情（含坐标）：**
```javascript
// 获取 北京市(0) -> 市辖区(0) -> 东城区(0) 的详情
const info = db.getDetail(0, 0, 0);
console.log(info);
/* 输出:
{
  "name": "东城区",
  "code": "110101",
  "lng": 116.416334,
  "lat": 39.928359
}
*/
```

## 为什么选择这个库？

1.  **极速加载 (Zero-copy)**: 数据无需解析 JSON，直接通过 WASM 内存映射读取，初始化几乎瞬间完成。
2.  **体积小**: 二进制数据比 JSON 小 50% 以上。
3.  **跨平台**: 核心数据 `.bin` 文件同样可用于 iOS/Android Native 开发 (使用 C++ SDK)。

## 重新构建

如果您需要修改 C++ 逻辑，请使用根目录下的 `build_release.sh` 脚本重新编译。

```bash
bash ../build_release.sh
```
