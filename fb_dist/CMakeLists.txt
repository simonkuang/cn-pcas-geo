cmake_minimum_required(VERSION 3.10)
project(XZQH_Query)

set(CMAKE_CXX_STANDARD 11)

# Find FlatBuffers
find_package(Flatbuffers QUIET)

# If not found via standard package, assume header-only usage is fine if flatc generated headers are present.
# However, we usually need the flatbuffers library linked or the include path set.
# For simplicity, if you installed via brew, /usr/local/include should be in path.

# Explicitly include current directory for xzqh_generated.h
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# Add executable
add_executable(query_sample query_sample.cpp)

# If you have the flatbuffers library built, link it. 
# Usually FlatBuffers is header-only for reading unless you use the Verifier or specific util features.
# The Verifier IS used in our code, so we might need to link to flatbuffers library if it's not strictly header-only for those parts.
# (Actually FlatBuffers C++ is largely header-only, verifying logic is in base.h/verifier.h)
# But let's try to link it if found to be safe.
if(Flatbuffers_FOUND)
    target_link_libraries(query_sample PRIVATE flatbuffers::flatbuffers)
else()
    message(STATUS "FlatBuffers package not found via CMake, assuming headers are in system path.")
endif()
