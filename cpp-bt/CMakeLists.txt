cmake_minimum_required(VERSION 3.16)
project(cpp_bt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(cpp-bt
  src/main.cpp
  src/candle.cpp
)
target_include_directories(cpp-bt PRIVATE include third_party)

if(MSVC)
  target_compile_options(cpp-bt PRIVATE /O2 /DNDEBUG /W3 /EHsc)
else()
  target_compile_options(cpp-bt PRIVATE -O3 -DNDEBUG -Wall)
endif()
