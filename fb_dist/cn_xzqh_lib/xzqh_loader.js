/**
 * CN XZQH (China Administrative Divisions) SDK
 * 
 * Wraps the Emscripten/WASM module to provide a clean, promise-based API.
 */
class XZQH {
    /**
     * Initialize the library.
     * @param {Object} options Configuration options
     * @param {string} options.dataUrl Path to 'xzqh.bin'. Default: './dist/xzqh.bin'
     * @param {string} options.wasmUrl Path to 'xzqh_core.wasm'. Default: './dist/xzqh_core.wasm'
     * @returns {Promise<XZQHInstance>} The initialized database instance
     */
    static async load(options = {}) {
        const dataUrl = options.dataUrl || './dist/xzqh.bin';
        const wasmUrl = options.wasmUrl || './dist/xzqh_core.wasm';

        // Ensure the glue code (createXZQH) is loaded.
        if (typeof createXZQH === 'undefined') {
            throw new Error("XZQH Core (xzqh_core.js) is not loaded. Please include it via <script> tag.");
        }

        console.log(`[XZQH] Initializing...`);
        console.log(`[XZQH] Loading WASM from: ${wasmUrl}`);
        console.log(`[XZQH] Loading Data from: ${dataUrl}`);

        // 1. Initialize WASM Module
        const module = await createXZQH({
            locateFile: (path) => {
                if (path.endsWith('.wasm')) return wasmUrl;
                return path;
            }
        });

        // 2. Fetch Binary Data
        const response = await fetch(dataUrl);
        if (!response.ok) throw new Error(`Failed to fetch data: ${response.statusText}`);
        const buffer = await response.arrayBuffer();
        const data = new Uint8Array(buffer);

        // 3. Allocate Memory in WASM Heap
        if (typeof module._malloc !== 'function') {
            throw new Error("WASM malloc missing. Build might be corrupt.");
        }
        const ptr = module._malloc(data.length);

        // 4. Copy Data to Heap
        // Safe access to memory view
        let heapU8 = module.HEAPU8;
        if (!heapU8) {
            // Fallback strategies for different Emscripten versions/optimizations
            if (module.buffer) heapU8 = new Uint8Array(module.buffer);
            else if (module.wasmMemory) heapU8 = new Uint8Array(module.wasmMemory.buffer);
            else throw new Error("Critical: Cannot access WASM memory.");
        }
        heapU8.set(data, ptr);

        console.log(`[XZQH] Ready. Loaded ${data.length} bytes.`);
        return new XZQHInstance(module, ptr, data.length);
    }
}

class XZQHInstance {
    constructor(module, ptr, size) {
        this.module = module;
        this.ptr = ptr;
        this.size = size;
        this.native = new module.XZQHWrapper(ptr, size);
    }

    /**
     * Get all provinces.
     * @returns {Array<{name: string, code: string, index: number}>}
     */
    getProvinces() {
        const json = this.native.getProvinces();
        return JSON.parse(json);
    }

    /**
     * Get cities for a province.
     * @param {number} provinceIndex The index returned in the province object (NOT the code)
     * @returns {Array<{name: string, code: string, index: number}>}
     */
    getCities(provinceIndex) {
        const json = this.native.getCities(provinceIndex);
        return JSON.parse(json);
    }

    /**
     * Get counties for a city.
     * @param {number} provinceIndex 
     * @param {number} cityIndex The index returned in the city object
     * @returns {Array<{name: string, code: string, index: number}>}
     */
    getCounties(provinceIndex, cityIndex) {
        const json = this.native.getCounties(provinceIndex, cityIndex);
        return JSON.parse(json);
    }

    /**
     * Get detailed info (including coordinates) for a node.
     * @param {number} provinceIndex 
     * @param {number} cityIndex 
     * @param {number} countyIndex 
     * @returns {{name: string, code: string, lng: number|null, lat: number|null}}
     */
    getDetail(provinceIndex, cityIndex = -1, countyIndex = -1) {
        const json = this.native.getRegionInfo(provinceIndex, cityIndex, countyIndex);
        return JSON.parse(json);
    }

    /**
     * Clean up memory.
     * Should be called when the component is destroyed (SPA) or app exits.
     */
    destroy() {
        if (this.native && this.native.delete) {
            this.native.delete();
        }
        if (this.module && this.module._free) {
            this.module._free(this.ptr);
        }
        this.native = null;
        this.module = null;
    }
}

// Export for module systems (ESM/CommonJS) or Browser Global
if (typeof module !== 'undefined' && module.exports) {
    module.exports = XZQH;
} else {
    window.XZQH = XZQH;
}
