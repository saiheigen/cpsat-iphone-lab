// Experimental full-calendar dynamic CP-SAT bridge for WebAssembly.
// Does NOT support operational rosters, fairness, business weights, meal
// credits, or compensation. Availability/history must be compiled locally
// into an anonymous eligibility matrix BEFORE invoking this module.
//
// guard-month-v2 is *not* assignment-v1. Two duty pools are solved
// separately, each must include every calendar shift; NO chunking.
// Single-threaded, bounded model with strict validation and time limit.
#include <array>
#include <exception>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
#include "ortools/sat/cp_model.h"
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
using operations_research::sat::CpSolverStatus;
using operations_research::sat::LinearExpr;
using operations_research::sat::Model;
using operations_research::sat::NewSatParameters;
using operations_research::sat::SatParameters;
using operations_research::sat::SolutionBooleanValue;
using operations_research::sat::SolveCpModel;
namespace {
std::string output;
constexpr const char* kInvalid="{\"status\":\"INVALID_INPUT\"}";
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
std::string solve_payload(const std::string& payload){
  if(payload.size()>200000)return kInvalid;
  std::istringstream stream(payload);
  std::array<std::string,7> lines;
  for(auto& line:lines)if(!std::getline(stream,line))return kInvalid;
  std::string extra;
  if(std::getline(stream,extra))return kInvalid;
  if(lines[0]!="guard-month-v2"||lines[1].size()!=7||
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

  CpModelBuilder model;
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
    if(hints[i]>=0){
      if(index[i][hints[i]]<0 ||
         (pins[i]>=0 && pins[i]!=hints[i]) || pins[i]==-1)
        return kInvalid;
      for(int p=0;p<staff;++p){
        if(index[i][p]>=0)
          model.AddHint(vars[i][index[i][p]], p==hints[i]);
      }
    }
  }
  // Full month constraints are built from the fixed v7 shift scheme.
  // All pairwise person conflicts remain within the same pool and do not
  // require a quadratic explicit conflict-edge wire payload.
  for(int p=0;p<staff;++p){
    std::vector<BoolVar> active;
    std::vector<BoolVar> standby;
    active.reserve(days);
    standby.reserve(days);
    for(int d=0;d<days;++d){
      LinearExpr total;
      LinearExpr staying;
      for(int k=0;k<slots;++k){
        const int s=d*slots+k;
        if(index[s][p]<0)continue;
        const BoolVar x=vars[s][index[s][p]];
        total+=x;
        if(weekday(year,month,d+1)==0 &&
           ((door && k>=4 && k<=10) || (!door && k==6)))
          staying+=x;
      }
      BoolVar on=model.NewBoolVar();
      const int daycap=door?3:1;
      model.AddLessOrEqual(total,daycap*on);
      model.AddGreaterOrEqual(total,on);
      active.push_back(on);

      BoolVar stay=model.NewBoolVar();
      model.AddGreaterOrEqual(staying,stay);
      model.AddLessOrEqual(staying,daycap*stay);
      standby.push_back(stay);

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
  model.Maximize(objective);
  SatParameters params;
  params.set_num_search_workers(1);
  params.set_max_time_in_seconds(10.0);
  Model sat_model;
  sat_model.Add(NewSatParameters(params));
  const auto response=SolveCpModel(model.Build(),&sat_model);
  const auto status=response.status();
  const char* label=status==CpSolverStatus::OPTIMAL?"OPTIMAL":
                    status==CpSolverStatus::FEASIBLE?"FEASIBLE":
                    status==CpSolverStatus::INFEASIBLE?"INFEASIBLE":"UNKNOWN";
  std::ostringstream result;
  result<<"{\"status\":\""<<label<<"\"";
  if(status==CpSolverStatus::OPTIMAL||status==CpSolverStatus::FEASIBLE){
    int filled=0;
    result<<",\"assignments\":[";
    for(int s=0;s<count;++s){
      if(s)result<<',';
      int chosen=-1;
      for(int p=0;p<staff;++p){
        if(index[s][p]<0)continue;
        if(SolutionBooleanValue(response,vars[s][index[s][p]])){
          if(chosen>=0)throw std::runtime_error("double booked");
          chosen=p;
          ++filled;
        }
      }
      result<<chosen;
    }
    result<<"],\"filled\":"<<filled
          <<",\"missing\":"<<(count-filled);
  }
  result<<'}';
  return result.str();
}
} // anonymous namespace

extern "C" KEEP const char* solve_guard_month_v2(const char* payload){
  try{
    if(!payload)return kInvalid;
    output=solve_payload(std::string(payload));
    return output.c_str();
  }catch(const std::exception&){
    output=kInvalid;
    return output.c_str();
  }
}
