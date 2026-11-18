cmake_minimum_required(VERSION 3.20)
project(cp_sat_iphone_probe LANGUAGES CXX)
if(NOT EMSCRIPTEN)
  message(FATAL_ERROR "Requires Emscripten via emcmake")
endif()
# Optional source-tree mode builds only cp_sat_probe and its transitive
# dependencies. The normal "all" target also builds CLI apps (sat_runner,
# solve) that depend on Unix signals and fail with Emscripten.
# The original find_package() workflow is retained for already installed builds.
if(DEFINED ORTOOLS_SOURCE_DIR AND NOT ORTOOLS_SOURCE_DIR STREQUAL "")
  if(NOT EXISTS "${ORTOOLS_SOURCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "ORTOOLS_SOURCE_DIR must point at OR-Tools source tree")
  endif()
  add_subdirectory("${ORTOOLS_SOURCE_DIR}" "${CMAKE_CURRENT_BINARY_DIR}/ortools-build" EXCLUDE_FROM_ALL)
else()
  find_package(ortools CONFIG REQUIRED)
endif()
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


# Bounded *dynamic* assignment probe. Keeps the already-proven fixed math
# probe unchanged. This is NOT the 589-shift production roster engine.
add_executable(cp_sat_assignment_bridge cp_sat_assignment_bridge.cc)
target_compile_features(cp_sat_assignment_bridge PRIVATE cxx_std_20)
target_link_libraries(cp_sat_assignment_bridge PRIVATE ortools::ortools)
target_compile_options(cp_sat_assignment_bridge PRIVATE -fexceptions)
set_target_properties(cp_sat_assignment_bridge PROPERTIES SUFFIX ".js")
target_link_options(cp_sat_assignment_bridge PRIVATE
  -O2 -fexceptions -sMODULARIZE=1 -sEXPORT_NAME=createAssignmentModule
  -sSINGLE_FILE=0 -sALLOW_MEMORY_GROWTH=1
  -sENVIRONMENT=web,worker,node -sNO_EXIT_RUNTIME=1 -sASSERTIONS=1
  "-sEXPORTED_FUNCTIONS=['_solve_assignment_v1','_malloc','_free']"
  "-sEXPORTED_RUNTIME_METHODS=['ccall']"
)


# Full-calendar anonymous guard-month-v2 EXPERIMENTAL solver. The original
# fixed probe and assignment-v1 targets remain unchanged.
add_executable(cp_sat_month_bridge cp_sat_month_bridge.cc)
target_compile_features(cp_sat_month_bridge PRIVATE cxx_std_20)
target_link_libraries(cp_sat_month_bridge PRIVATE ortools::ortools)
target_compile_options(cp_sat_month_bridge PRIVATE -fexceptions)
set_target_properties(cp_sat_month_bridge PROPERTIES SUFFIX ".js")
target_link_options(cp_sat_month_bridge PRIVATE
  -O2 -fexceptions -sMODULARIZE=1 -sEXPORT_NAME=createMonthModule
  -sSINGLE_FILE=0 -sALLOW_MEMORY_GROWTH=1
  -sENVIRONMENT=web,worker,node -sNO_EXIT_RUNTIME=1 -sASSERTIONS=1
  "-sEXPORTED_FUNCTIONS=['_solve_guard_month_v2','_malloc','_free']"
  "-sEXPORTED_RUNTIME_METHODS=['ccall']"
)


# Separate two-stage fair-count CP-SAT WASM target (guard-month-fair-v3).
add_executable(cp_sat_month_fair_bridge cp_sat_month_fair_bridge.cc)
target_compile_features(cp_sat_month_fair_bridge PRIVATE cxx_std_20)
target_link_libraries(cp_sat_month_fair_bridge PRIVATE ortools::ortools)
target_compile_options(cp_sat_month_fair_bridge PRIVATE -fexceptions)
set_target_properties(cp_sat_month_fair_bridge PROPERTIES SUFFIX ".js")
target_link_options(cp_sat_month_fair_bridge PRIVATE
  -O2 -fexceptions -sMODULARIZE=1 -sEXPORT_NAME=createMonthFairModule
  -sSINGLE_FILE=0 -sALLOW_MEMORY_GROWTH=1
  -sENVIRONMENT=web,worker,node -sNO_EXIT_RUNTIME=1 -sASSERTIONS=1
  "-sEXPORTED_FUNCTIONS=['_solve_guard_month_fair_v3','_malloc','_free']"
  "-sEXPORTED_RUNTIME_METHODS=['ccall']"
)


# Isolated THREE-STAGE v4 month target. Existing proven v2/v3 binaries
# and browser release pipelines remain untouched.
add_executable(cp_sat_month_hardship_bridge cp_sat_month_hardship_bridge.cc)
target_compile_features(cp_sat_month_hardship_bridge PRIVATE cxx_std_20)
target_link_libraries(cp_sat_month_hardship_bridge PRIVATE ortools::ortools)
target_compile_options(cp_sat_month_hardship_bridge PRIVATE -fexceptions)
set_target_properties(cp_sat_month_hardship_bridge PROPERTIES SUFFIX ".js")
target_link_options(cp_sat_month_hardship_bridge PRIVATE
  -O2 -fexceptions -sMODULARIZE=1 -sEXPORT_NAME=createMonthHardshipModule
  -sSINGLE_FILE=0 -sALLOW_MEMORY_GROWTH=1
  -sENVIRONMENT=web,worker,node -sNO_EXIT_RUNTIME=1 -sASSERTIONS=1
  "-sEXPORTED_FUNCTIONS=['_solve_guard_month_harsh_v4','_malloc','_free']"
  "-sEXPORTED_RUNTIME_METHODS=['ccall']"
)
