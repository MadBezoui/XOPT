# Quick test harness for the research cycles: correctness on tiny cases, then timing on larger ones.
const R=normpath(joinpath(@__DIR__,".."))*"/"
include(R*"src/XOPT.jl");using .XOPT
include(R*"src/uc2.jl");using .UCX2
using Random
for (k,v) in [split(a,"=") for a in ARGS if occursin("=",a)];UCX2.CYCLE[Symbol(k)]=v=="true";end
println("CYCLE ",UCX2.CYCLE);flush(stdout)
f(day)=R*"data/pglib_uc/rts_$day.json"
# 1. tiny correctness
ok=0;n=0
for day in ["2020-01-27","2020-07-06"],(units,sec) in [(["101_CT_1","201_CT_1","301_CT_1"],true),(["113_CT_1","301_CT_1"],false)]
 d=load_uc(f(day),units;T=4,start=15,alpha=.6,ramps=false,secant=sec);nom=uc_forward(d)
 for (g,t) in [(1,2),(2,3)], mode in [:weak,:strong]
  fo=Foil([(g,t,1-round(Int,nom.u[g,t]))]);uc_forward(d;foil=fo).status=="OPTIMAL" || continue
  o=Options(mode=mode,margin=1e-3*nom.objective,time_limit=120.);lev=UCLevers(marginal=true)
  e=uc_explain_by_enumeration(d,fo;options=o,levers=lev);r=uc_explain(d,fo;options=o,levers=lev)
  agree=e["status"]=="INFEASIBLE" ? r["status"]=="SOLVER_INFEASIBLE" : (r["status"]=="SOLVER_VALIDATED" && abs(r["objective"]-e["objective"])<=1e-6)
  global n+=1;global ok+=agree;agree || println("DISAGREE ",day,units,(g,t,mode)," ",e["status"]," ",e["objective"]," ",r["status"]," ",get(r,"objective",nothing))
 end
end
println("tiny agree $ok/$n");flush(stdout)
# 2. timing
U=["107_CC_1","213_CC_3","101_STEAM_3","115_STEAM_3","202_STEAM_4","113_CT_1","123_CT_1","207_CT_1","301_CT_3","322_CT_5"]
for (units,T,day) in [(U[[1,3,5,6,8,10]],6,"2020-10-27"),(U,12,"2020-04-03"),(U,12,"2020-07-06")]
 d=load_uc(f(day),units;T=T,start=1,ramps=false);nom=uc_forward(d)
 rng=MersenneTwister(1);G=length(units)
 cand=shuffle(rng,[(g,t) for g in 1:G for t in 2:T if uc_forward(d;foil=Foil([(g,t,1-round(Int,nom.u[g,t]))]),limit=30).status=="OPTIMAL"])[1:2]
 for (g,t) in cand, (name,lev) in [("M",UCLevers(noload=false,marginal=true)),("FM",UCLevers(marginal=true))]
  fo=Foil([(g,t,1-round(Int,nom.u[g,t]))]);o=Options(mode=:strong,margin=1e-3*nom.objective,time_limit=300.)
  r=uc_explain(d,fo;options=o,levers=lev)
  v=r["status"]=="SOLVER_VALIDATED" ? uc_verify(d,fo,r;options=o,levers=lev)["valid"] : missing
  println("G$G T$T $day $name ",fo.literals," ",r["status"]," obj=",get(r,"objective",nothing)," lb=",round(r["lower_bound"],digits=4)," it",r["iterations"]," ",round(r["seconds"],digits=1),"s valid=",v," mc=",get(r,"changed_marginal",nothing));flush(stdout)
 end
end
