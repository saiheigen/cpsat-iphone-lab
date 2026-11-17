// Experimental C++/WASM dynamic assignment: synthetic and bounded ONLY.
// Caller must construct and independently check ALL duty restrictions;
// this engine only knows eligibility, conflicts, and fixed slots.
#include <exception>
#include <sstream>
#include <string>
#include <stdexcept>
#include <vector>
#include <utility>
#include "ortools/sat/cp_model.h"
#include "ortools/sat/cp_model_solver.h"
#include "ortools/sat/sat_parameters.pb.h"
#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define KEEP EMSCRIPTEN_KEEPALIVE
#else
#define KEEP
#endif
using operations_research::sat::CpModelBuilder;
using operations_research::sat::BoolVar;
using operations_research::sat::LinearExpr;
using operations_research::sat::Model;
using operations_research::sat::SatParameters;
using operations_research::sat::NewSatParameters;
using operations_research::sat::SolveCpModel;
using operations_research::sat::SolutionBooleanValue;
using operations_research::sat::CpSolverStatus;

namespace {
std::string last_result;
const char* invalid = "{\"status\":\"INVALID_INPUT\"}";

std::vector<int> split_integers(const std::string& raw, char separator) {
  std::vector<int> out;
  if (raw.empty()) return out;
  std::istringstream ss(raw);
  std::string part;
  while (std::getline(ss, part, separator)) {
    if (part.empty()) throw std::invalid_argument("empty integer");
    std::size_t consumed=0;
    const int v = std::stoi(part, &consumed);
    if (consumed != part.size()) throw std::invalid_argument("bad integer");
    out.push_back(v);
  }
  if (raw.back()==separator) throw std::invalid_argument("trailing delimiter");
  return out;
}

std::vector<std::pair<int,int>> parse_conflicts(const std::string& raw,
                                                 int shifts) {
  std::vector<std::pair<int,int>> pairs;
  if (raw.empty()) return pairs;
  std::istringstream ss(raw);
  std::string token;
  while (std::getline(ss, token, ';')) {
    const auto x = split_integers(token, ':');
    if (x.size()!=2 || x[0]<0 || x[1]<0 || x[0]>=shifts ||
        x[1]>=shifts || x[0]>=x[1]) {
      throw std::invalid_argument("invalid conflict edge");
    }
    pairs.emplace_back(x[0],x[1]);
    if (pairs.size()>1024) throw std::invalid_argument("too many conflicts");
  }
  if (raw.back()==';') throw std::invalid_argument("trailing conflict");
  return pairs;
}

std::string solve_payload(const std::string& raw) {
  if (raw.size()>16000) return invalid;
  std::istringstream in(raw);
  std::string version, dimensions, eligibility, conflict, pin, extra;
  if (!std::getline(in,version) || version!="assignment-v1" ||
      !std::getline(in,dimensions) || !std::getline(in,eligibility) ||
      !std::getline(in,conflict) || !std::getline(in,pin)) {
    return invalid;
  }
  if (std::getline(in,extra) && !extra.empty()) return invalid;
  int shifts=0, people=0;
  std::string trailing;
  std::istringstream dims(dimensions);
  if (!(dims>>shifts>>people) || dims>>trailing ||
      shifts<1 || shifts>64 || people<1 || people>24 ||
      shifts*people>1536 ||
      eligibility.size()!=static_cast<std::size_t>(shifts*people)) {
    return invalid;
  }
  for(char c:eligibility) if(c!='0'&&c!='1') return invalid;
  const auto pins=split_integers(pin,',');
  if(pins.size()!=static_cast<std::size_t>(shifts)) return invalid;
  const auto conflicts=parse_conflicts(conflict,shifts);
  CpModelBuilder model;
  std::vector<std::vector<BoolVar>> vars(shifts);
  std::vector<std::vector<bool>> exists(shifts,std::vector<bool>(people,false));
  LinearExpr total;
  for(int s=0;s<shifts;++s){
    LinearExpr slot;
    for(int p=0;p<people;++p){
      if(eligibility[s*people+p]!='1') continue;
      BoolVar v=model.NewBoolVar();
      vars[s].push_back(v);
      exists[s][p]=true;
      slot+=v;
      total+=v;
    }
    model.AddLessOrEqual(slot,1);
    const int fixed=pins[s];
    if(fixed<-2 || fixed>=people) return invalid;
    if(fixed==-1) model.AddEquality(slot,0);
    if(fixed>=0){
      if(!exists[s][fixed]) return invalid;
      int k=0;
      for(int p=0;p<fixed;++p) if(exists[s][p]) ++k;
      model.AddEquality(vars[s][k],1);
    }
  }
  for(auto [a,b]: conflicts){
    int ia=0,ib=0;
    for(int p=0;p<people;++p){
      const bool ha=exists[a][p], hb=exists[b][p];
      if(ha&&hb) model.AddLessOrEqual(vars[a][ia]+vars[b][ib],1);
      if(ha) ++ia;
      if(hb) ++ib;
    }
  }
  model.Maximize(total);
  SatParameters params;
  params.set_num_search_workers(1);
  params.set_max_time_in_seconds(3.0);
  Model sat_model;
  sat_model.Add(NewSatParameters(params));
  const auto res=SolveCpModel(model.Build(),&sat_model);
  const auto status=res.status();
  const char* name=(status==CpSolverStatus::OPTIMAL)?"OPTIMAL":
                   (status==CpSolverStatus::FEASIBLE)?"FEASIBLE":
                   (status==CpSolverStatus::INFEASIBLE)?"INFEASIBLE":"UNKNOWN";
  std::ostringstream out;
  out<<"{\"status\":\""<<name<<"\"";
  if(status==CpSolverStatus::OPTIMAL || status==CpSolverStatus::FEASIBLE){
    out<<",\"assignments\":[";
    int filled=0;
    for(int s=0;s<shifts;++s){
      if(s) out<<',';
      int who=-1, i=0;
      for(int p=0;p<people;++p){
        if(!exists[s][p]) continue;
        if(SolutionBooleanValue(res,vars[s][i++])){
          if(who>=0) throw std::runtime_error("duplicate duty assignment");
          who=p; ++filled;
        }
      }
      out<<who;
    }
    out<<"],\"filled\":"<<filled<<",\"missing\":"<<(shifts-filled);
  }
  out<<'}';
  return out.str();
}
} // namespace

extern "C" KEEP const char* solve_assignment_v1(const char* payload) {
  try{
    if(!payload) return invalid;
    last_result=solve_payload(std::string(payload));
  }catch(const std::exception&){
    last_result=invalid;
  }
  return last_result.c_str();
}
