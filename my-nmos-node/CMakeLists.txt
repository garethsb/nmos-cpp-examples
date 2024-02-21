cmake_minimum_required(VERSION 3.17 FATAL_ERROR)

project(my-nmos-node)

# location of additional CMake modules
list(APPEND CMAKE_MODULE_PATH
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake
    )

# Find and use nmos-cpp from its installed location or as a subdirectory
set(USE_ADD_SUBDIRECTORY OFF CACHE BOOL "Use add_subdirectory() rather than find_package()")
if(NOT USE_ADD_SUBDIRECTORY)
    message(STATUS "Using find_package(nmos-cpp)")

    # Using find_package() will require nmos-cpp and its dependencies (Boost, cpprestsdk, etc.)
    # to be installed and discoverable via a config-file package or find-module
    # Conan is one way of achieving this...
    find_package(nmos-cpp REQUIRED)
else()
    set(NMOS_CPP_DIRECTORY "../../nmos-cpp/Development" CACHE STRING "Path to nmos-cpp/Development directory")

    message(STATUS "Using add_subdirectory(${NMOS_CPP_DIRECTORY})")
    add_subdirectory(${NMOS_CPP_DIRECTORY} build-nmos-cpp EXCLUDE_FROM_ALL)
endif()

# my-nmos-node executable

set(MY_NMOS_NODE_SOURCES
    main.cpp
    node_implementation.cpp
    )
set(MY_NMOS_NODE_HEADERS
    node_implementation.h
    )

add_executable(
    my-nmos-node
    ${MY_NMOS_NODE_SOURCES}
    ${MY_NMOS_NODE_HEADERS}
    config.json
    )

source_group("Source Files" FILES ${MY_NMOS_NODE_SOURCES})
source_group("Header Files" FILES ${MY_NMOS_NODE_HEADERS})

target_link_libraries(
    my-nmos-node
    nmos-cpp::compile-settings
    nmos-cpp::nmos-cpp
    )
