cmake_minimum_required(VERSION 3.20)
project(cp_sat_iphone_probe LANGUAGES CXX)
if(NOT EMSCRIPTEN)
  message(FATAL_ERROR "Requires Emscripten via emcmake")
endif()
find_package(ortools CONFIG REQUIRED)
add_executable(cp_sat_probe cp_sat_probe.cc)
target_compile_features(cp_sat_probe PRIVATE cxx_std_20)
target_link_libraries(cp_sat_probe PRIVATE ortools::ortools)
target_compile_options(cp_sat_probe PRIVATE -fexceptions)
set_target_properties(cp_sat_probe PROPERTIES SUFFIX ".js")
target_link_options(cp_sat_probe PRIVATE
  -O2 -fexceptions -sMODULARIZE=1 -sEXPORT_NAME=createCPSatModule
  -sSINGLE_FILE=0 -sALLOW_MEMORY_GROWTH=1
  -sENVIRONMENT=web,worker,node -sNO_EXIT_RUNTIME=1 -sASSERTIONS=1
  "-sEXPORTED_FUNCTIONS=['_run_cp_sat_probe','_malloc','_free']"
  "-sEXPORTED_RUNTIME_METHODS=['ccall']"
)
