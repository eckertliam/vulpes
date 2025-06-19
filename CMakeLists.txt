cmake_minimum_required(VERSION 3.26)

project(vulpes
    VERSION 0.1.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(src)

option(VULPES_BUILD_TESTS "Build doctest-based unit tests" ON)

if(VULPES_BUILD_TESTS)
    enable_testing()

    include(FetchContent)
    FetchContent_Declare(
        doctest
        GIT_REPOSITORY https://github.com/doctest/doctest.git
        GIT_TAG        v2.4.12
    )
    FetchContent_MakeAvailable(doctest)

    file(GLOB TEST_SOURCES CONFIGURE_DEPENDS tests/*.cpp)

    add_executable(vulpes_tests ${TEST_SOURCES})
    target_link_libraries(vulpes_tests PRIVATE vulpes_core doctest::doctest)

    add_test(NAME all COMMAND vulpes_tests)
endif()
