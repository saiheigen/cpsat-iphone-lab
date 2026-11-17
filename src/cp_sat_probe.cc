// Synthetic test only: genuine Google OR-Tools CP-SAT, no duty roster data.
#include <sstream>
#include <string>
#include <exception>
#include "ortools/sat/cp_model.h"
#include "ortools/sat/cp_model_solver.h"
#include "ortools/sat/sat_parameters.pb.h"
#include "ortools/util/sorted_interval_list.h"
#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define KEEP EMSCRIPTEN_KEEPALIVE
#else
#define KEEP
#endif
using operations_research::Domain;
using operations_research::sat::CpModelBuilder;
using operations_research::sat::CpSolverResponse;
using operations_research::sat::CpSolverStatus;
using operations_research::sat::IntVar;
using operations_research::sat::Model;
using operations_research::sat::NewSatParameters;
using operations_research::sat::SatParameters;
using operations_research::sat::SolutionIntegerValue;
using operations_research::sat::SolveCpModel;
static std::string last_result;
extern "C" KEEP const char* run_cp_sat_probe() {
  try {
    CpModelBuilder model;
    const IntVar desks = model.NewIntVar(Domain(0, 4)).WithName("desks");
    const IntVar tables = model.NewIntVar(Domain(0, 3)).WithName("tables");
    model.AddLessOrEqual(3 * desks + 4 * tables, 12);
    model.Maximize(20 * desks + 30 * tables);
    SatParameters parameters;
    parameters.set_num_search_workers(1);
    parameters.set_max_time_in_seconds(10.0);
    Model sat_model;
    sat_model.Add(NewSatParameters(parameters));
    const CpSolverResponse result = SolveCpModel(model.Build(), &sat_model);
    const int status = result.status();
    const char* name = (status == CpSolverStatus::OPTIMAL) ? "OPTIMAL" :
                       (status == CpSolverStatus::FEASIBLE) ? "FEASIBLE" :
                       (status == CpSolverStatus::INFEASIBLE) ? "INFEASIBLE" : "UNKNOWN";
    std::ostringstream ss;
    ss << "{\"engine\":\"Google OR-Tools CP-SAT\",\"status\":\"" << name << "\"";
    if (status == CpSolverStatus::OPTIMAL || status == CpSolverStatus::FEASIBLE) {
      ss << ",\"desks\":" << SolutionIntegerValue(result, desks)
         << ",\"tables\":" << SolutionIntegerValue(result, tables)
         << ",\"profit\":" << result.objective_value();
    }
    ss << "}";
    last_result = ss.str();
  } catch (const std::exception&) {
    last_result = "{\"engine\":\"Google OR-Tools CP-SAT\",\"status\":\"ERROR\"}";
  }
  return last_result.c_str();
}
