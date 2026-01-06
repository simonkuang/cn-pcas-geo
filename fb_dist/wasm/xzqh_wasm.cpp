#include <emscripten/bind.h>
#include <string>
#include <vector>
#include <sstream>
#include <iomanip>
#include "../xzqh_generated.h"

using namespace emscripten;

class XZQHWrapper {
public:
    XZQHWrapper(uintptr_t data_ptr, size_t size) {
        buffer_ptr_ = reinterpret_cast<uint8_t*>(data_ptr);
        data_ = XZQH::GetData(buffer_ptr_);
    }

    std::string getProvinces() {
        if (!data_ || !data_->root()) return "[]";
        
        std::stringstream ss;
        ss << "[";
        auto regions = data_->root();
        for (flatbuffers::uoffset_t i = 0; i < regions->size(); ++i) {
            if (i > 0) ss << ",";
            auto region = regions->Get(i);
            ss << "{\"name\":\"" << region->name()->str() 
               << "\",\"index\":" << i 
               << ",\"code\":\"" << region->code()->str() << "\"}";
        }
        ss << "]";
        return ss.str();
    }

    std::string getCities(int province_idx) {
        if (!data_ || !data_->root()) return "[]";
        if (province_idx < 0 || province_idx >= (int)data_->root()->size()) return "[]";

        auto province = data_->root()->Get(province_idx);
        if (!province->children()) return "[]";

        std::stringstream ss;
        ss << "[";
        auto cities = province->children();
        for (flatbuffers::uoffset_t i = 0; i < cities->size(); ++i) {
            if (i > 0) ss << ",";
            auto city = cities->Get(i);
            ss << "{\"name\":\"" << city->name()->str() 
               << "\",\"index\":" << i 
               << ",\"code\":\"" << city->code()->str() << "\"}";
        }
        ss << "]";
        return ss.str();
    }

    std::string getCounties(int province_idx, int city_idx) {
        if (!data_ || !data_->root()) return "[]";
        if (province_idx < 0 || province_idx >= (int)data_->root()->size()) return "[]";

        auto province = data_->root()->Get(province_idx);
        if (!province->children()) return "[]";
        if (city_idx < 0 || city_idx >= (int)province->children()->size()) return "[]";

        auto city = province->children()->Get(city_idx);
        if (!city->children()) return "[]";

        std::stringstream ss;
        ss << "[";
        auto counties = city->children();
        for (flatbuffers::uoffset_t i = 0; i < counties->size(); ++i) {
            if (i > 0) ss << ",";
            auto county = counties->Get(i);
            ss << "{\"name\":\"" << county->name()->str() 
               << "\",\"index\":" << i 
               << ",\"code\":\"" << county->code()->str() << "\"}";
        }
        ss << "]";
        return ss.str();
    }

    std::string getRegionInfo(int province_idx, int city_idx, int county_idx) {
        const XZQH::Region* target = nullptr;
        
        if (!data_ || !data_->root()) return "{}";
        
        if (province_idx >= 0 && province_idx < (int)data_->root()->size()) {
            target = data_->root()->Get(province_idx);
            
            if (city_idx >= 0 && target->children() && city_idx < (int)target->children()->size()) {
                target = target->children()->Get(city_idx);
                
                if (county_idx >= 0 && target->children() && county_idx < (int)target->children()->size()) {
                    target = target->children()->Get(county_idx);
                }
            }
        }

        if (!target) return "{}";

        std::stringstream ss;
        ss << "{";
        ss << "\"name\":\"" << target->name()->str() << "\",";
        ss << "\"code\":\"" << target->code()->str() << "\",";
        if (target->center()) {
            ss << "\"lng\":" << std::fixed << std::setprecision(6) << target->center()->longitude() << ",";
            ss << "\"lat\":" << std::fixed << std::setprecision(6) << target->center()->latitude();
        } else {
            ss << "\"lng\":null,\"lat\":null";
        }
        ss << "}";
        return ss.str();
    }

private:
    const uint8_t* buffer_ptr_;
    const XZQH::Data* data_;
};

EMSCRIPTEN_BINDINGS(my_module) {
    class_<XZQHWrapper>("XZQHWrapper")
        .constructor<uintptr_t, size_t>()
        .function("getProvinces", &XZQHWrapper::getProvinces)
        .function("getCities", &XZQHWrapper::getCities)
        .function("getCounties", &XZQHWrapper::getCounties)
        .function("getRegionInfo", &XZQHWrapper::getRegionInfo);
}
