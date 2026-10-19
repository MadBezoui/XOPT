# Timing harness for the research cycles: one query per process, run several processes in parallel.
const R=normpath(joinpath(@__DIR__,".."))*"/"
include(R*"src/XOPT.jl");using .XOPT
include(R*"src/uc2.jl");using .UCX2
using Random
job=parse(Int,ARGS[1]);for (k,v) in [split(a,"=") for a in ARGS[2:end] if occursin("=",a)];UCX2.CYCLE[Symbol(k)]=v=="true";end
U=["107_CC_1","213_CC_3","101_STEAM_3","115_STEAM_3","202_STEAM_4","113_CT_1","123_CT_1","207_CT_1","301_CT_3","322_CT_5"]
cases=[(U[[1,3,5,6,8,10]],6,"2020-10-27"),(U,12,"2020-04-03"),(U,12,"2020-07-06")]
jobs=[(c,q,lev) for c in cases for q in 1:2 for lev in ("M","FM")]
(units,T,day),q,levname=jobs[job]
d=load_uc(R*"data/pglib_uc/rts_$day.json",units;T=T,start=1,ramps=false);nom=uc_forward(d);G=length(units)
cand=shuffle(MersenneTwister(1),[(g,t) for g in 1:G for t in 2:T if uc_forward(d;foil=Foil([(g,t,1-round(Int,nom.u[g,t]))]),limit=30).status=="OPTIMAL"])[1:2]
g,t=cand[q];fo=Foil([(g,t,1-round(Int,nom.u[g,t]))]);o=Options(mode=:strong,margin=1e-3*nom.objective,time_limit=parse(Float64,get(ENV,"LIMIT","300")))
lev=levname=="M" ? UCLevers(noload=false,marginal=true) : UCLevers(marginal=true)
r=uc_explain(d,fo;options=o,levers=lev)
v=r["status"]=="SOLVER_VALIDATED" ? uc_verify(d,fo,r;options=o,levers=lev)["valid"] : missing
println("G$G T$T $day $levname ",fo.literals," ",r["status"]," obj=",get(r,"objective",nothing)," lb=",round(r["lower_bound"],digits=4)," it",r["iterations"]," ",round(r["seconds"],digits=1),"s valid=",v," ",UCX2.CYCLE)
