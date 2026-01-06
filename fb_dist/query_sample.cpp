#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>

// Include the generated header (assumes you ran: flatc --cpp xzqh.fbs)
#include "xzqh_generated.h"

// Helper to read the entire file into a byte vector
std::vector<uint8_t> LoadFile(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary | std::ios::ate);
    if (!file) {
        return {};
    }
    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);
    std::vector<uint8_t> buffer(size);
    if (file.read(reinterpret_cast<char*>(buffer.data()), size)) {
        return buffer;
    }
    return {};
}

// Structure to hold the path for printing
struct PathNode {
    std::string name;
    std::string code;
};

// Recursive search function
// Returns true if found (to stop searching if we only want one, 
// but usually names like "朝阳区" are not unique, so we might want to find ALL matches)
void SearchByName(const XZQH::Region* region, const std::string& target_name, std::vector<PathNode>& path, bool& found_at_least_one) {
    if (!region) return;

    // Push current node to path
    std::string current_name = region->name()->str();
    std::string current_code = region->code()->str();
    path.push_back({current_name, current_code});

    // Check if current node matches
    // Simple substring or exact match? Requirement says "Compare name". 
    // Let's do exact match for precision, or partial if user wants. 
    // Let's do exact match for now as it's safer.
    if (current_name == target_name) {
        found_at_least_one = true;
        std::cout << "Found match:\n";
        
        // Print Path: Province -> City -> District
        for (size_t i = 0; i < path.size(); ++i) {
            std::cout << path[i].name;
            if (i < path.size() - 1) std::cout << " -> ";
        }
        std::cout << "\n";

        // Print Code
        std::cout << "Code: " << current_code << "\n";

        // Print Coordinates
        if (region->center()) {
            std::cout << "Coordinates: " << region->center()->longitude() 
                      << ", " << region->center()->latitude() << "\n";
        } else {
            std::cout << "Coordinates: N/A\n";
        }
        std::cout << "--------------------------------------------------\n";
    }

    // Recurse children
    if (region->children()) {
        for (auto child : *region->children()) {
            SearchByName(child, target_name, path, found_at_least_one);
        }
    }

    // Backtrack
    path.pop_back();
}

int main(int argc, char* argv[]) {
    std::string filename = "xzqh.bin";
    
    // Check args for filename override
    if (argc > 1) {
        // If user provided an argument, check if it's the bin file or the search term
        std::string arg1 = argv[1];
        if (arg1.find(".bin") != std::string::npos) {
            filename = arg1;
        }
    }

    std::cout << "Loading " << filename << "..." << std::endl;
    auto buffer = LoadFile(filename);
    if (buffer.empty()) {
        std::cerr << "Error: Could not read " << filename << "\n";
        std::cerr << "Make sure you have generated the .bin file using the python script." << std::endl;
        return 1;
    }

    // Get Access to the root object
    // Verification is optional but recommended
    flatbuffers::Verifier verifier(buffer.data(), buffer.size());
    if (!XZQH::VerifyDataBuffer(verifier)) {
        std::cerr << "Error: Invalid FlatBuffers file." << std::endl;
        return 1;
    }

    auto data = XZQH::GetData(buffer.data());
    
    std::string input_name;
    while (true) {
        std::cout << "\nEnter administrative name to search (or 'q' to quit): ";
        if (!std::getline(std::cin, input_name) || input_name == "q") {
            break;
        }

        if (input_name.empty()) continue;

        bool found = false;
        std::vector<PathNode> path;
        
        // The root of our schema has a 'root' field which is a vector of Regions (Provinces)
        if (data->root()) {
            for (auto province : *data->root()) {
                SearchByName(province, input_name, path, found);
            }
        }

        if (!found) {
            std::cout << "No location found with name: " << input_name << "\n";
        }
    }

    return 0;
}
