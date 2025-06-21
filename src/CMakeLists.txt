add_library(vulpes_frontend STATIC
    frontend/lexer.cpp
    frontend/token.cpp)

target_include_directories(vulpes_frontend PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_library(vulpes_vm STATIC
    vm/opcode.cpp)

add_executable(vulpes main.cpp)

target_link_libraries(vulpes PRIVATE vulpes_frontend)