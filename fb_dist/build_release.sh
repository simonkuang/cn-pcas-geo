#!/bin/bash

# Build Script for Release
# Output: dist/xzqh_core.js and dist/xzqh_core.wasm

echo "Building WASM Core..."

# Check environment
if ! command -v emcc &> /dev/null
then
    echo "Error: emcc not found."
    exit 1
fi

OUTPUT_JS="fb_dist/cn_xzqh_lib/dist/xzqh_core.js"

emcc fb_dist/wasm/xzqh_wasm.cpp \
    -I fb_dist \
    -I/opt/homebrew/include \
    -L/opt/homebrew/lib \
    --bind \
    -s WASM=1 \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s MODULARIZE=1 \
    -s EXPORT_NAME='createXZQH' \
    -s "EXPORTED_FUNCTIONS=['_malloc']" \
    -s "EXPORTED_RUNTIME_METHODS=['HEAPU8']" \
    -O3 \
    -o "$OUTPUT_JS"

echo "Build Success: $OUTPUT_JS"

