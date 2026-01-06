#!/bin/bash

echo "Cleaning WASM build artifacts..."

# Remove generated JS and WASM files
rm -f fb_dist/wasm/xzqh_wasm.js
rm -f fb_dist/wasm/xzqh_wasm.wasm

# Remove Emscripten cache (optional, but ensures clean system libs)
# emcc --clear-cache

echo "Cleanup complete."
