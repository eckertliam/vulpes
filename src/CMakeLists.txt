add_library(vulpes_frontend STATIC
    frontend/location.cpp
    frontend/lexer.cpp
    frontend/token.cpp)

target_include_directories(vulpes_frontend PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_library(vulpes_vm STATIC
    vm/instruction.cpp
    vm/machine.cpp
    vm/function.cpp
    vm/call_frame.cpp
    vm/object/base.cpp
    vm/object/integer.cpp
    vm/arena.cpp)

target_include_directories(vulpes_vm PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(vulpes main.cpp)

target_link_libraries(vulpes PUBLIC vulpes_frontend vulpes_vm)

add_executable(vulpes_tests 
    tests/test_vm.cpp)

target_link_libraries(vulpes_tests PRIVATE vulpes_vm Catch2::Catch2WithMain)

# Include Catch2 module and discover tests
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
include(Catch)
catch_discover_tests(vulpes_tests)