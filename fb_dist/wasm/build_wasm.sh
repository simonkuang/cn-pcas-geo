#!/bin/bash

# Check if emcc is available
if ! command -v emcc &> /dev/null
then
    echo "Error: emcc (Emscripten Compiler) could not be found."
    echo "Please activate Emscripten environment:"
    echo "  source /path/to/emsdk/emsdk_env.sh"
    exit 1
fi

echo "Compiling C++ to WASM..."

# Emscripten Compilation Command
# -s MODULARIZE=1 : Wraps everything in a function
# -s EXPORT_NAME='createXZQH' : The name of the function
# -s EXPORTED_RUNTIME_METHODS=['HEAPU8'] : explicitly export the memory view so we can write data into it from JS

emcc xzqh_wasm.cpp \
    -I.. \
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
    -o xzqh_wasm.js

echo "Build complete."
echo "Now serve the directory via HTTP (WASM requires correct MIME types):"
echo "  python3 -m http.server"
