# FlatBuffers Data Generation

本目录包含将 `xzqh_with_amap_coordinates.json` 转换为 FlatBuffers 二进制数据 (`xzqh.bin`) 的所有资源。

## 为什么要用 FlatBuffers?
- **极小体积**: 去除了 JSON 中的 Key 字符串和冗余结构。
- **极快加载**: 在 C++ / WASM 中支持 Zero-copy (零拷贝)，直接映射内存即可使用，无需解析。
- **跨平台**: 生成的 Schema 支持 C++, Java, Kotlin, Swift, Dart, TS/JS 等。

## 目录结构
- `xzqh.fbs`: FlatBuffers Schema 定义文件。
- `convert_json_to_fb.py`: Python 转换脚本。

## 快速开始

### 1. 安装 FlatBuffers Compiler (flatc)

**macOS:**
```bash
brew install flatbuffers
```

**Linux / Windows:**
请访问 [FlatBuffers Releases](https://github.com/google/flatbuffers/releases) 下载对应平台的 `flatc`。

### 2. 安装 Python 依赖
```bash
pip install flatbuffers
```

### 3. 生成代码并运行转换
在终端中进入本目录 (`fb_dist`) 并运行以下命令：

```bash
# 1. 使用 flatc 生成 Python 绑定代码 (用于转换脚本)
flatc --python xzqh.fbs

# 2. 使用 flatc 生成 C++ 头文件 (用于您的 C++ 项目)
flatc --cpp xzqh.fbs

# 3. 运行转换脚本生成 .bin 数据
python3 convert_json_to_fb.py
```

执行成功后，您将在当前目录下看到 `xzqh.bin`。

## 如何在 C++ 中使用

1. **生成头文件**：
   ```bash
   flatc --cpp xzqh.fbs
   ```

2. **编译并运行示例程序**：
   我们提供了一个交互式的查询程序 `query_sample.cpp`。

   **方法 A: 使用 g++ 直接编译**
   ```bash
   # 确保已安装 flatbuffers (brew install flatbuffers)
   g++ -std=c++11 query_sample.cpp -o query_sample -lflatbuffers
   
   # 运行 (确保目录下有 xzqh.bin)
   ./query_sample
   ```

   **方法 B: 使用 CMake**
   ```bash
   mkdir build && cd build
   cmake ..
   make
   ./query_sample
   ```

3. **代码集成示例**：
   将 `xzqh_generated.h` 复制到您的项目中，并参考 `query_sample.cpp` 中的 `LoadFile` 和 `SearchByName` 函数实现数据加载与查找。
