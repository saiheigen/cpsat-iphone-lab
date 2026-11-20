#include <tuple>
// EXPERIMENTAL full-calendar THREE-stage CP-SAT WASM with protected hardship.
// Stage 1 protects validated input fill and skips search at the fill upper
// bound. Stage 2 locks achieved fill and minimizes
// total absolute difference from per-person soft integer targets.
// Stage 3 fixes occupied shift positions AND stage-2 achieved L1 count deviation,
// then minimizes normalized night/noon and officer long-hours exposure.
// Cross-month credits/meal credits/weights are already reduced into local
// targets BEFORE serialization. No operational roster certification. Availability/history must be compiled locally
// into an anonymous eligibility matrix BEFORE invoking this module.
//
// guard-month-v2 is *not* assignment-v1. Two duty pools are solved
// separately, each must include every calendar shift; NO chunking.
// Single-threaded, bounded model with strict validation and time limit.
#include <algorithm>
#include <array>
#include <cstdlib>
#include <exception>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
#include "ortools/sat/cp_model.h"
#include "ortools/sat/cp_model_checker.h"
#include "ortools/sat/cp_model_solver.h"
#include "ortools/sat/sat_parameters.pb.h"
#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define KEEP EMSCRIPTEN_KEEPALIVE
#else
#define KEEP
#endif

using operations_research::sat::BoolVar;
using operations_research::sat::CpModelBuilder;
using operations_research::sat::CpSolverResponse;
using operations_research::sat::CpSolverStatus;
using operations_research::sat::IntVar;
using operations_research::sat::LinearExpr;
using operations_research::sat::Model;
using operations_research::sat::NewSatParameters;
using operations_research::sat::SatParameters;
using operations_research::sat::SolutionBooleanValue;
using operations_research::sat::SolutionIntegerValue;
using operations_research::sat::SolutionIsFeasible;
using operations_research::sat::SolveCpModel;
namespace {
std::string output;
constexpr const char* kInvalid="{\"status\":\"INVALID_INPUT\",\"baseline_valid\":false}";
constexpr int kStartDoor[12]={22,0,2,4,6,8,10,12,14,16,18,20};
constexpr int kEndDoor[12]={24,2,4,6,8,10,12,14,16,18,20,22};

int number(const std::string& word) {
  if(word.empty() || word.size()>9)throw std::invalid_argument("integer size");
  for(const char c:word)if(c<'0'||c>'9')throw std::invalid_argument("not a number");
  return std::stoi(word);
}
std::vector<int> integers(const std::string& raw) {
  std::vector<int> result;
  if(raw.empty())throw std::invalid_argument("no integers");
  std::istringstream stream(raw);
  std::string part;
  while(std::getline(stream,part,',')){
    if(part.empty())throw std::invalid_argument("empty integer");
    bool minus=part.front()=='-';
    if(minus && part.size()==1)throw std::invalid_argument("invalid sign");
    int value=number(part.substr(minus?1:0));
    result.push_back(minus?-value:value);
  }
  if(raw.back()==',')throw std::invalid_argument("trailing comma");
  return result;
}
int days_in_month(int year,int month){
  if(year<2000||year>2100||month<1||month>12)
    throw std::invalid_argument("invalid month");
  constexpr int days[]={0,31,28,31,30,31,30,31,31,30,31,30,31};
  int out=days[month];
  if(month==2&&(year%4==0&&(year%100!=0||year%400==0)))++out;
  return out;
}
// Gregorian weekday: 0=Sunday, 1=Monday, ... 6=Saturday.
int weekday(int y,int m,int d){
  constexpr int t[]={0,3,2,5,0,3,5,1,4,6,2,4};
  if(m<3)--y;
  return (y+y/4-y/100+y/400+t[m-1]+d)%7;
}
// Integer hardship categories share the same slot definitions as v7.
// Door: 4 individual night segments, total night, 12-14 noon.
// Officer: total 22-06 night, 12-18 noon, 6-hour long-shift and hours.
int hardship_categories(bool door){return door?6:4;}
int hardship_units(bool door,int k,int c){
  if(door){
    if(c>=0&&c<4)return k==c?1:0;
    if(c==4)return k<4?1:0;
    return c==5&&k==7?1:0;
  }
  if(c==0)return k<4?1:0;
  if(c==1)return k==5?1:0;
  if(c==2)return (k==4||k==5)?1:0;
  constexpr int hours[7]={2,2,2,2,6,6,4};
  return c==3?hours[k]:0;
}
int hardship_weight(bool door,int c){
  if(door)return (c==4||c==5)?2:1;
  return c==3?1:2;
}

// A solution belongs to the model prefix that produced it. New auxiliary
// variables receive their exact values as the next phase creates them.
void replace_hint(CpModelBuilder& model, const CpSolverResponse& solution,
                  int prefix_size) {
  if (prefix_size > solution.solution_size())
    throw std::logic_error("Missing incumbent variable");
  model.ClearHints();
  for (int i = 0; i < prefix_size; ++i)
    model.AddHint(model.GetIntVarFromProtoIndex(i), solution.solution(i));
}

bool can_take(int s,const std::vector<int>& jobs,int slots,bool door,int year,int month) {
  const int d=s/slots, k=s%slots;
  auto stay=[&](int slot){return door ? slot>=4 && slot<=10 : slot==6;};
  int same_day=1;
  for(int prior:jobs){
    const int days_apart=std::abs(d-prior/slots), j=prior%slots;
    if(days_apart==1 || (days_apart==2 && j==k))return false;
    if(days_apart==7 && weekday(year,month,d+1)==0 && stay(k) && stay(j))return false;
    if(days_apart!=0)continue;
    if(!door || ++same_day>3)return false;
    if(kEndDoor[j]+6>kStartDoor[k] && kEndDoor[k]+6>kStartDoor[j])return false;
  }
  return true;
}

// Audit the actual assignment against the wire, independently of the CP model,
// before returning the input roster after a search timeout or an exception.
bool audit_assignment(const std::vector<int>& a, const std::string& allowed,
                      const std::vector<int>& pins, int staff, bool door,
                      int year, int month) {
  const int slots=door?12:7;
  std::vector<std::vector<int>> jobs(staff);
  for(int s=0;s<static_cast<int>(a.size());++s){
    const int p=a[s];
    if(p < -1 || p >= staff || (pins[s]!=-2 && pins[s]!=p))return false;
    if(p==-1)continue;
    if(allowed[s*staff+p]!='1')return false;
    if(!can_take(s,jobs[p],slots,door,year,month))return false;
    jobs[p].push_back(s);
  }
  return true;
}

struct GuardScores {
  int extra=0, triples=0;
  long long hardship=0;
  bool permits(const GuardScores& next) const {
    return next.extra<=extra && next.triples<=triples && next.hardship<=hardship;
  }
};

GuardScores roster_scores(const std::vector<int>& roster,int staff,bool door){
  const int slots=door?12:7, cats=hardship_categories(door);
  std::vector<int> counts(staff),daily(staff),totals(cats),load(staff*cats);
  int filled=0;
  GuardScores score;
  for(size_t s=0;s<roster.size();++s){
    if(s%slots==0)std::fill(daily.begin(),daily.end(),0);
    int p=roster[s];
    if(p<0)continue;
    ++filled; ++counts[p]; ++daily[p];
    score.extra+=daily[p]>1;
    score.triples+=daily[p]==3;
    for(int c=0;c<cats;++c){
      int units=hardship_units(door,s%slots,c);
      totals[c]+=units; load[p*cats+c]+=units;
    }
  }
  for(int p=0;p<staff;++p)for(int c=0;c<cats;++c)
    score.hardship+=hardship_weight(door,c)*std::llabs(1LL*filled*load[p*cats+c]-1LL*totals[c]*counts[p]);
  return score;
}

std::string json_array(const std::vector<int>& a) {
  std::ostringstream out;
  out << '[';
  for(size_t i=0;i<a.size();++i){if(i)out<<',';out<<a[i];}
  out<<']';
  return out.str();
}

// Only stable, internal diagnostic codes enter the wire response.
struct StageFault {const char* code;};
bool has_solution(CpSolverStatus status) {
  return status==CpSolverStatus::FEASIBLE || status==CpSolverStatus::OPTIMAL;
}
std::string recovery_result(const char* phase, const char* reason,
                            bool valid, const std::vector<int>& a,
                            const std::string& allowed, const std::vector<int>& pins,
                            const std::vector<int>& targets, bool door, int year, int month) {
  const int staff=static_cast<int>(targets.size()), slots=door?12:7, cats=hardship_categories(door);
  std::ostringstream out;
  out<<"{\"failed_stage\":\""<<phase<<"\",\"failure_reason\":\""<<reason
     <<"\",\"baseline_valid\":"<<(valid?"true":"false");
  if(!valid || !audit_assignment(a,allowed,pins,staff,door,year,month)){
    out<<",\"status\":\"SOLVER_ERROR\",\"fallback_audited\":false}";
    return out.str();
  }
  std::vector<int> counts(staff), totals(cats);
  std::vector<std::vector<int>> loads(staff,std::vector<int>(cats));
  int filled=0, cost=0;
  for(size_t s=0;s<a.size();++s){
    if(a[s]<0)continue;
    ++filled;
    ++counts[a[s]];
    for(int c=0;c<cats;++c){
      const int units=hardship_units(door,s%slots,c);
      totals[c]+=units;
      loads[a[s]][c]+=units;
    }
  }
  long long hardship=0;
  for(int p=0;p<staff;++p){
    cost+=std::abs(counts[p]-targets[p]);
    for(int c=0;c<cats;++c)
      hardship+=hardship_weight(door,c)*std::llabs(1LL*filled*loads[p][c]-1LL*totals[c]*counts[p]);
  }
  out<<",\"status\":\"FEASIBLE\",\"fallback_audited\":true,\"fill_used_baseline\":true"
     <<",\"fill_phase\":\"FEASIBLE\",\"fair_phase\":\"UNKNOWN\",\"hardship_phase\":\"UNKNOWN\""
     <<",\"fill_optimal_proven\":false,\"fair_optimal_proven_given_fill\":false"
     <<",\"hardship_optimal_proven_given_locked_predecessors\":false"
     <<",\"fixed_occupied_positions\":true,\"fairness_improved\":false,\"hardship_improved\":false"
     <<",\"assignments\":"<<json_array(a)<<",\"actual_counts\":"<<json_array(counts)
     <<",\"filled\":"<<filled<<",\"missing\":"<<a.size()-filled
     <<",\"phase1_abs_deviation\":"<<cost<<",\"final_abs_deviation\":"<<cost
     <<",\"hardship_initial_score\":"<<hardship<<",\"hardship_final_score\":"<<hardship<<"}";
  return out.str();
}

std::string solve_payload(const std::string& payload){
  if(payload.size()>200000)return kInvalid;
  std::istringstream stream(payload);
  std::array<std::string,8> lines;
  for(auto& line:lines)if(!std::getline(stream,line))return kInvalid;
  std::string extra;
  // Optional ninth line: limits_ms=fill,fair,fair_retry,hardship.
  std::vector<int> limits(4,10000);
  if(std::getline(stream,extra)){
    if(extra.rfind("limits_ms=",0)!=0)return kInvalid;
    limits=integers(extra.substr(10));
    if(limits.size()!=4 || std::any_of(limits.begin(),limits.end(),
       [](int ms){return ms<0 || ms>60000;}) || std::getline(stream,extra))return kInvalid;
  }
  if(lines[0]!="guard-month-harsh-v4"||lines[1].size()!=7||
     lines[1][4]!='-')return kInvalid;
  const int year=number(lines[1].substr(0,4));
  const int month=number(lines[1].substr(5,2));
  const int days=days_in_month(year,month);
  const bool door=lines[2]=="door";
  if(!door && lines[2]!="officer")return kInvalid;
  const int slots=door?12:7;
  const int expected=days*slots;
  std::istringstream dims(lines[3]);
  int count=0,staff=0;
  std::string tail;
  if(!(dims>>count>>staff)||(dims>>tail)||count!=expected||
     count>589||staff<1||staff>106||
     lines[4].size()!=static_cast<size_t>(count*staff))
    return kInvalid;
  for(char c:lines[4])if(c!='0'&&c!='1')return kInvalid;
  const auto pins=integers(lines[5]);
  const auto hints=integers(lines[6]);
  if(pins.size()!=static_cast<size_t>(count)||
     hints.size()!=static_cast<size_t>(count))return kInvalid;
  const auto targets=integers(lines[7]);
  if(targets.size()!=static_cast<size_t>(staff))return kInvalid;
  for(int t:targets)if(t<0 || t>count)return kInvalid;

  CpModelBuilder model;
  std::vector<int> baseline_staff = hints;
  std::vector<int> baseline_true_vars;
  std::vector<std::vector<BoolVar>> vars(count);
  std::vector<std::vector<int>> index(count,std::vector<int>(staff,-1));
  LinearExpr objective;
  for(int i=0;i<count;++i){
    LinearExpr slot;
    for(int p=0;p<staff;++p){
      if(lines[4][i*staff+p]!='1')continue;
      index[i][p]=static_cast<int>(vars[i].size());
      BoolVar x=model.NewBoolVar();
      vars[i].push_back(x);
      slot+=x;
      objective+=x;
    }
    model.AddLessOrEqual(slot,1);
    if(pins[i]<-2||pins[i]>=staff||hints[i]<-1||hints[i]>=staff)
      return kInvalid;
    if(pins[i]==-1)model.AddEquality(slot,0);
    if(pins[i]>=0){
      if(index[i][pins[i]]<0)return kInvalid;
      model.AddEquality(vars[i][index[i][pins[i]]],1);
    }
    if(hints[i]>=0 && (index[i][hints[i]]<0 ||
       (pins[i]>=0 && pins[i]!=hints[i]) || pins[i]==-1))return kInvalid;
    if(pins[i]>=0)baseline_staff[i]=pins[i];
    const int person=baseline_staff[i];
    if(person>=0)baseline_true_vars.push_back(vars[i][index[i][person]].index());
  }
  // Full month constraints are built from the fixed v7 shift scheme.
  // All pairwise person conflicts remain within the same pool and do not
  // require a quadratic explicit conflict-edge wire payload.
  std::vector<std::vector<int>> active_index(staff,std::vector<int>(days));
  std::vector<std::vector<int>> stay_index(staff,std::vector<int>(days));
  for(int p=0;p<staff;++p){
    std::vector<BoolVar> active;
    std::vector<BoolVar> standby;
    active.reserve(days);
    standby.reserve(days);
    for(int d=0;d<days;++d){
      LinearExpr total;
      LinearExpr staying;
      bool baseline_on=false, baseline_stay=false;
      for(int k=0;k<slots;++k){
        const int s=d*slots+k;
        if(index[s][p]<0)continue;
        const BoolVar x=vars[s][index[s][p]];
        total+=x;
        if(baseline_staff[s]==p)baseline_on=true;
        if(weekday(year,month,d+1)==0 &&
           ((door && k>=4 && k<=10) || (!door && k==6))){
          staying+=x;
          if(baseline_staff[s]==p)baseline_stay=true;
        }
      }
      BoolVar on=model.NewBoolVar();
      const int daycap=door?3:1;
      model.AddLessOrEqual(total,daycap*on);
      model.AddGreaterOrEqual(total,on);
      active.push_back(on);
      active_index[p][d]=on.index();
      if(baseline_on)baseline_true_vars.push_back(on.index());

      BoolVar stay=model.NewBoolVar();
      model.AddGreaterOrEqual(staying,stay);
      model.AddLessOrEqual(staying,daycap*stay);
      standby.push_back(stay);
      stay_index[p][d]=stay.index();
      if(baseline_stay)baseline_true_vars.push_back(stay.index());

      if(d>=1)model.AddLessOrEqual(active[d-1]+active[d],1);
      if(d>=7&&weekday(year,month,d+1)==0)
        model.AddLessOrEqual(standby[d-7]+standby[d],1);

      for(int k=0;k<slots;++k){
        const int a=d*slots+k;
        if(index[a][p]<0)continue;
        const BoolVar va=vars[a][index[a][p]];
        if(d+2<days){
          const int b=(d+2)*slots+k;
          if(index[b][p]>=0)
            model.AddLessOrEqual(va+vars[b][index[b][p]],1);
        }
        // Two 2-hour door shifts on the same day need >=6h break.
        if(door)for(int j=k+1;j<slots;++j){
          const int b=d*slots+j;
          if(index[b][p]<0)continue;
          const int ast=kStartDoor[k],aen=kEndDoor[k];
          const int bst=kStartDoor[j],ben=kEndDoor[j];
          if(!(aen+6<=bst || ben+6<=ast))
            model.AddLessOrEqual(va+vars[b][index[b][p]],1);
        }
      }
    }
  }
  // Check the exact model, including pins and rest. An invalid combination
  // of otherwise well-formed hints can guide search, but is never a fallback.
  const int base_vars=model.Build().variables_size();
  CpSolverResponse baseline;
  baseline.mutable_solution()->Resize(base_vars,0);
  for(int i:baseline_true_vars)baseline.set_solution(i,1);
  const int baseline_fill=std::count_if(baseline_staff.begin(),baseline_staff.end(),
                                        [](int person){return person>=0;});
  const int upper=count-std::count(pins.begin(),pins.end(),-1);
  // An unhinted, unconstrained vacancy is not evidence of a supplied roster.
  const bool valid_baseline=(baseline_fill>0 || upper==0) &&
      SolutionIsFeasible(model.Build(),
          {baseline.solution().data(),static_cast<size_t>(base_vars)});
  const bool skip_fill=valid_baseline && baseline_fill==upper;
  const char* phase="fill";
  try {
  if(valid_baseline)model.AddGreaterOrEqual(objective,baseline_fill);
  if(std::any_of(hints.begin(),hints.end(),[](int p){return p>=0;}))
    replace_hint(model,baseline,base_vars);

  SatParameters params;
  params.set_num_search_workers(1);
  params.set_max_time_in_seconds(limits[0]/1000.0);
  params.set_repair_hint(true);
  CpSolverResponse fill_search;
  if(!skip_fill){
    model.Maximize(objective);
    Model sat_model;
    sat_model.Add(NewSatParameters(params));
    fill_search=SolveCpModel(model.Build(),&sat_model);
  }
  const auto status=fill_search.status();
  if(status==CpSolverStatus::MODEL_INVALID ||
     (valid_baseline && status==CpSolverStatus::INFEASIBLE))
    throw StageFault{"invalid_fill_model_or_inconsistent_floor"};
  const bool found_fill=status==CpSolverStatus::OPTIMAL || status==CpSolverStatus::FEASIBLE;
  const std::string search_label=skip_fill?"NOT_RUN":CpSolverStatus_Name(status);
  std::ostringstream result;
  if(!found_fill && !valid_baseline){
    result<<"{\"status\":\""<<search_label<<"\",\"fill_phase\":\""<<search_label
          <<"\",\"baseline_valid\":false,\"fair_phase\":\"NOT_RUN\",\"fill_optimal_proven\":false"
          <<",\"fair_optimal_proven_given_fill\":false,\"hardship_phase\":\"NOT_RUN\"}";
    return result.str();
  }
  const auto searched_fill=found_fill?SolutionIntegerValue(fill_search,objective):-1;
  if(valid_baseline && found_fill && searched_fill<baseline_fill)
    throw StageFault{"violated_fill_floor"};
  const bool use_baseline=valid_baseline && searched_fill<=baseline_fill;
  const auto& first=use_baseline?baseline:fill_search;
  const char* fill_label=(skip_fill || status==CpSolverStatus::OPTIMAL)?"OPTIMAL":"FEASIBLE";
  int locked=0;
  std::vector<int> first_counts(staff,0);
  for(int s=0;s<count;++s)for(int p=0;p<staff;++p){
    if(index[s][p]>=0 && SolutionBooleanValue(first,vars[s][index[s][p]])){
      ++locked;
      ++first_counts[p];
    }
  }
  int first_cost=0;
  for(int p=0;p<staff;++p)first_cost+=std::abs(first_counts[p]-targets[p]);
  phase="fair";
  model.AddEquality(objective,locked);
  replace_hint(model,first,base_vars);
  // Compare like-for-like coverage. After gaining fill, protect that new incumbent.
  auto roster_of=[&](const CpSolverResponse& response){
    std::vector<int> roster(count,-1);
    for(int s=0;s<count;++s)for(int p=0;p<staff;++p)
      if(index[s][p]>=0 && SolutionBooleanValue(response,vars[s][index[s][p]]))roster[s]=p;
    return roster;
  };
  const auto start_roster=roster_of(first);
  const auto floor=roster_scores(start_roster,staff,door);
  const bool protect=valid_baseline;
  std::vector<std::tuple<int,int,BoolVar>> triple_flags;
  if(protect && door){
    LinearExpr active_days, triples;
    for(int p=0;p<staff;++p)for(int d=0;d<days;++d){
      active_days+=model.GetBoolVarFromProtoIndex(active_index[p][d]);
      LinearExpr daily;
      int options=0, initial=0;
      for(int s=d*slots;s<(d+1)*slots;++s){
        if(index[s][p]<0)continue;
        daily+=vars[s][index[s][p]]; ++options; initial+=start_roster[s]==p;
      }
      if(options<3)continue;
      if(floor.triples==0){model.AddLessOrEqual(daily,2);continue;}
      auto flag=model.NewBoolVar();
      model.AddLessOrEqual(daily,2+flag);
      model.AddGreaterOrEqual(daily,3*flag);
      model.AddHint(flag,initial==3);
      triples+=flag; triple_flags.emplace_back(p,d,flag);
    }
    model.AddGreaterOrEqual(active_days,locked-floor.extra);
    model.AddLessOrEqual(triples,floor.triples);
  }
  LinearExpr fairness;
  std::vector<IntVar> count_deviations;
  for(int p=0;p<staff;++p){
    LinearExpr assigned;
    for(int s=0;s<count;++s){
      if(index[s][p]>=0)assigned+=vars[s][index[s][p]];
    }
    const auto deviation=model.NewIntVar({0,count});
    model.AddAbsEquality(deviation,assigned-targets[p]);
    count_deviations.push_back(deviation);
    model.AddHint(deviation,std::abs(first_counts[p]-targets[p]));
    fairness+=deviation;
  }
  model.AddLessOrEqual(fairness,first_cost);
  model.Minimize(fairness);
  auto solve_fair=[&](int budget_ms,bool repair_hint){
    SatParameters attempt=params;
    attempt.set_max_time_in_seconds(budget_ms/1000.0);
    attempt.set_repair_hint(repair_hint);
    Model solver;
    solver.Add(NewSatParameters(attempt));
    auto response=SolveCpModel(model.Build(),&solver);
    if(response.status()==CpSolverStatus::MODEL_INVALID)
      throw StageFault{"invalid_fair_model"};
    if(response.status()==CpSolverStatus::INFEASIBLE)
      throw StageFault{"incumbent_excluded"};
    if(protect && has_solution(response.status()) &&
       !floor.permits(roster_scores(roster_of(response),staff,door))){
      // Discard the candidate as well as its optimality claim for this guarded search.
      return CpSolverResponse{};
    }
    return response;
  };
  auto cost_of=[&](const CpSolverResponse& r){
    if(!has_solution(r.status()))return first_cost;
    const int cost=SolutionIntegerValue(r,fairness);
    if(cost>first_cost)throw StageFault{"violated_fair_floor"};
    return cost;
  };
  auto second=solve_fair(limits[1],true);
  const auto warm_status=second.status();
  const int warm_cost=cost_of(second);
  int second_cost=warm_cost;
  std::string retry_label="NOT_RUN";
  // L1 cannot be lower than the difference of the two count totals.
  const int lower=std::abs(locked-std::accumulate(targets.begin(),targets.end(),0));
  if(limits[2]>0 && warm_status!=CpSolverStatus::OPTIMAL &&
     warm_cost==first_cost && warm_cost>lower){
    phase="fair_retry";
    model.ClearHints();
    auto retry=solve_fair(limits[2],false);
    retry_label=CpSolverStatus_Name(retry.status());
    const int retry_cost=cost_of(retry);
    if(has_solution(retry.status()) && (!has_solution(warm_status) ||
       retry_cost<second_cost || retry.status()==CpSolverStatus::OPTIMAL)){
      second=std::move(retry);
      second_cost=retry_cost;
    }
  }
  const auto fair_status=second.status();
  const bool fair_found=has_solution(fair_status);
  const std::string fair_label=CpSolverStatus_Name(fair_status);
  const int search_cost=second_cost;
  const bool use_second=fair_found && second_cost<first_cost;
  const CpSolverResponse* selected=use_second?&second:&first;
  int chosen_cost=use_second?second_cost:first_cost;
  CpSolverResponse balanced;
  int transfers=0;
  // If the CP attempts still leave count imbalance, transfer an unpinned
  // assignment directly from a surplus to a deficit. Each move lowers L1 by
  // two, leaves fill positions intact, and only adds duties to the receiver.
  if(limits[2]>0 && chosen_cost>lower && fair_status!=CpSolverStatus::OPTIMAL){
    phase="balance";
    std::vector<int> assignment(count,-1), counts(staff);
    std::vector<std::vector<int>> jobs(staff);
    for(int s=0;s<count;++s)for(int p=0;p<staff;++p){
      if(index[s][p]<0 || !SolutionBooleanValue(*selected,vars[s][index[s][p]]))continue;
      assignment[s]=p; ++counts[p]; jobs[p].push_back(s);
    }
    for(int s=0;s<count && chosen_cost>lower;++s){
      const int from=assignment[s];
      if(from<0 || pins[s]!=-2 || counts[from]<=targets[from])continue;
      int best=-1, deficit=0;
      for(int p=0;p<staff;++p){
        const int need=targets[p]-counts[p];
        if(need>deficit && index[s][p]>=0 && can_take(s,jobs[p],slots,door,year,month)){
          if(protect){
            assignment[s]=p;
            const bool ok=floor.permits(roster_scores(assignment,staff,door));
            assignment[s]=from;
            if(!ok)continue;
          }
          best=p; deficit=need;
        }
      }
      if(best<0)continue;
      auto& previous=jobs[from];
      previous.erase(std::find(previous.begin(),previous.end(),s));
      jobs[best].push_back(s);
      assignment[s]=best; --counts[from]; ++counts[best];
      ++transfers; chosen_cost-=2;
    }
    if(transfers){
      balanced.mutable_solution()->Resize(model.Build().variables_size(),0);
      for(int s=0;s<count;++s){
        const int p=assignment[s];
        if(p<0)continue;
        const int day=s/slots, k=s%slots;
        balanced.set_solution(vars[s][index[s][p]].index(),1);
        balanced.set_solution(active_index[p][day],1);
        if(weekday(year,month,day+1)==0 && (door?(k>=4 && k<=10):k==6))
          balanced.set_solution(stay_index[p][day],1);
      }
      for(const auto& [p,d,flag]:triple_flags)
        balanced.set_solution(flag.index(),std::count(assignment.begin()+d*slots,assignment.begin()+(d+1)*slots,p)==3);
      for(int p=0;p<staff;++p)
        balanced.set_solution(count_deviations[p].index(),std::abs(counts[p]-targets[p]));
      if(!SolutionIsFeasible(model.Build(),{balanced.solution().data(),
             static_cast<size_t>(balanced.solution_size())}) ||
         SolutionIntegerValue(balanced,fairness)!=chosen_cost ||
         !audit_assignment(assignment,lines[4],pins,staff,door,year,month))
        throw StageFault{"transfer_failed_audit"};
      selected=&balanced;
    }
  }
  phase="hardship";
  // No stage-3 optimization can create a new missing shift, sacrifice a
  // previously covered shift, or worsen the achieved second-stage L1 cost.
  model.AddEquality(fairness,chosen_cost);
  replace_hint(model,*selected,base_vars);
  for(int p=0;p<staff;++p){
    const auto deviation=count_deviations[p];
    model.AddHint(deviation,selected!=&first?selected->solution(deviation.index()):
                  std::abs(first_counts[p]-targets[p]));
  }
  const auto stage2_roster=roster_of(*selected);
  for(const auto& [p,d,flag]:triple_flags)
    model.AddHint(flag,std::count(stage2_roster.begin()+d*slots,stage2_roster.begin()+(d+1)*slots,p)==3);
  std::vector<int> occupied(count,0);
  for(int s=0;s<count;++s){
    LinearExpr one;
    for(const BoolVar x:vars[s]){
      one+=x;
      if(SolutionBooleanValue(*selected,x))occupied[s]=1;
    }
    model.AddEquality(one,occupied[s]);
  }
  const int cats=hardship_categories(door);
  std::vector<int> category_totals(cats,0);
  for(int s=0;s<count;++s)if(occupied[s])
    for(int c=0;c<cats;++c)
      category_totals[c]+=hardship_units(door,s%slots,c);
  // Independent scoring of the actual candidate assignment. Each person's
  // category load is normalized by their assigned total duty count, avoiding
  // an unfair penalty on a person with fewer total (credited) duties.
  auto hardship_score=[&](const auto& response)->long long {
    std::vector<int> counts(staff,0);
    std::vector<std::vector<int>> load(staff,std::vector<int>(cats,0));
    for(int s=0;s<count;++s)for(int p=0;p<staff;++p){
      if(index[s][p]<0 ||
         !SolutionBooleanValue(response,vars[s][index[s][p]]))continue;
      ++counts[p];
      for(int c=0;c<cats;++c)
        load[p][c]+=hardship_units(door,s%slots,c);
    }
    long long score=0;
    for(int p=0;p<staff;++p)for(int c=0;c<cats;++c)
      score+=hardship_weight(door,c)*
        std::llabs(static_cast<long long>(locked)*load[p][c]-
                   static_cast<long long>(category_totals[c])*counts[p]);
    return score;
  };
  const long long prior_hardship=hardship_score(*selected);
  LinearExpr hardship;
  for(int p=0;p<staff;++p){
    LinearExpr assigned;
    for(int s=0;s<count;++s)
      if(index[s][p]>=0)assigned+=vars[s][index[s][p]];
    for(int c=0;c<cats;++c){
      LinearExpr load;
      for(int s=0;s<count;++s)if(index[s][p]>=0){
        const int unit=hardship_units(door,s%slots,c);
        if(unit)load+=unit*vars[s][index[s][p]];
      }
      // 12*count^2 safely bounds scaled officer hours and night/noon terms.
      const auto dev=model.NewIntVar({0,12*count*count});
      const LinearExpr imbalance=locked*load-category_totals[c]*assigned;
      model.AddAbsEquality(dev,imbalance);
      model.AddHint(dev,std::abs(SolutionIntegerValue(*selected,imbalance)));
      hardship+=hardship_weight(door,c)*dev;
    }
  }
  model.AddLessOrEqual(hardship,prior_hardship);
  model.Minimize(hardship);
  params.set_max_time_in_seconds(limits[3]/1000.0);
  Model harsh_model;
  harsh_model.Add(NewSatParameters(params));
  const auto third=SolveCpModel(model.Build(),&harsh_model);
  const auto harsh_status=third.status();
  if(harsh_status==CpSolverStatus::MODEL_INVALID || harsh_status==CpSolverStatus::INFEASIBLE)
    throw StageFault{"invalid_hardship_model_or_inconsistent_floor"};
  const bool harsh_found=harsh_status==CpSolverStatus::OPTIMAL ||
                         harsh_status==CpSolverStatus::FEASIBLE;
  const char* harsh_label=harsh_status==CpSolverStatus::OPTIMAL?"OPTIMAL":
                          harsh_status==CpSolverStatus::FEASIBLE?"FEASIBLE":
                          harsh_status==CpSolverStatus::INFEASIBLE?"INFEASIBLE":"UNKNOWN";
  long long selected_hardship=prior_hardship;
  if(harsh_found){
    const long long new_score=hardship_score(third);
    if(new_score<prior_hardship){
      selected=&third;
      selected_hardship=new_score;
    }else if(new_score>prior_hardship && harsh_status==CpSolverStatus::OPTIMAL){
      throw StageFault{"violated_hardship_bound"};
    }
  }
  const bool harsh_proven=harsh_status==CpSolverStatus::OPTIMAL;

  phase="return";
  if(selected==&baseline && !audit_assignment(baseline_staff,lines[4],pins,staff,door,year,month))
    throw StageFault{"baseline_audit_failed"};
  if(protect && !floor.permits(roster_scores(roster_of(*selected),staff,door)))
    throw StageFault{"violated_roster_quality_floor"};
  const bool fill_proven=status==CpSolverStatus::OPTIMAL || locked==upper;
  const bool fair_proven=fair_status==CpSolverStatus::OPTIMAL && second_cost==chosen_cost;
  const char* overall=fill_proven && fair_proven && harsh_proven?"OPTIMAL":"FEASIBLE";
  result<<"{\"status\":\""<<overall<<"\",\"fill_phase\":\""<<fill_label
        <<"\",\"fill_search_status\":\""<<search_label
        <<"\",\"fill_used_baseline\":"<<(use_baseline?"true":"false")
        <<",\"baseline_valid\":"<<(valid_baseline?"true":"false")
        <<",\"fair_warm_status\":\""<<CpSolverStatus_Name(warm_status)<<"\""
        <<",\"fair_warm_cost\":"<<warm_cost
        <<",\"fair_search_cost\":"<<search_cost
        <<",\"fair_transfers\":"<<transfers
        <<",\"fair_retry_status\":\""<<retry_label<<"\""
        <<",\"fair_phase\":\""<<fair_label<<"\""
        <<",\"fill_optimal_proven\":"<<(fill_proven?"true":"false")
        <<",\"fair_optimal_proven_given_fill\":"<<(fair_proven?"true":"false")
        <<",\"phase1_abs_deviation\":"<<first_cost
        <<",\"final_abs_deviation\":"<<chosen_cost
        <<",\"fairness_improved\":"<<(chosen_cost<first_cost?"true":"false")
        <<",\"hardship_phase\":\""<<harsh_label<<"\""
        <<",\"hardship_initial_score\":"<<prior_hardship
        <<",\"hardship_final_score\":"<<selected_hardship
        <<",\"hardship_improved\":"<<(selected_hardship<prior_hardship?"true":"false")
        <<",\"hardship_optimal_proven_given_locked_predecessors\":"<<(harsh_proven?"true":"false")
        <<",\"fixed_occupied_positions\":true";
  {
    int filled=0;
    result<<",\"assignments\":[";
    for(int s=0;s<count;++s){
      if(s)result<<',';
      int chosen=-1;
      for(int p=0;p<staff;++p){
        if(index[s][p]<0)continue;
        if(SolutionBooleanValue(*selected,vars[s][index[s][p]])){
          if(chosen>=0)throw StageFault{"multiple_assignments"};
          chosen=p;
          ++filled;
        }
      }
      result<<chosen;
    }
    if(filled!=locked)throw StageFault{"protected_fill_changed"};
    result<<"],\"filled\":"<<filled
          <<",\"missing\":"<<(count-filled);
    result<<",\"actual_counts\":[";
    for(int p=0;p<staff;++p){
      if(p)result<<',';
      int assigned=0;
      for(int s=0;s<count;++s)
        if(index[s][p]>=0 && SolutionBooleanValue(*selected,vars[s][index[s][p]]))
          ++assigned;
      result<<assigned;
    }
    result<<"]";
  }
  result<<'}';
  return result.str();
  } catch(const StageFault& fault) {
    return recovery_result(phase,fault.code,valid_baseline,baseline_staff,
                           lines[4],pins,targets,door,year,month);
  } catch(const std::exception&) {
    return recovery_result(phase,"solver_exception",valid_baseline,baseline_staff,
                           lines[4],pins,targets,door,year,month);
  }
}
} // anonymous namespace

extern "C" KEEP const char* solve_guard_month_harsh_v4(const char* payload){
  try{
    if(!payload)return kInvalid;
    output=solve_payload(std::string(payload));
    return output.c_str();
  }catch(const std::exception&){
    output=kInvalid;
    return output.c_str();
  }
}
