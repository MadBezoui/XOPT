const R=normpath(joinpath(@__DIR__,".."))*"/"
include(R*"src/XOPT.jl");using .XOPT
include(R*"src/uc2.jl");using .UCX2
include(R*"research/fixedwitness.jl")
using Random
U=["107_CC_1","213_CC_3","101_STEAM_3","115_STEAM_3","202_STEAM_4","113_CT_1","123_CT_1","207_CT_1","301_CT_3","322_CT_5"]
for (units,T,day) in [(U[[1,3,5,6,8,10]],6,"2020-10-27"),(U,12,"2020-04-03"),(U,12,"2020-07-06")]
 d=load_uc(R*"data/pglib_uc/rts_$day.json",units;T=T,start=1,ramps=false);nom=uc_forward(d);G=length(units)
 cand=shuffle(MersenneTwister(1),[(g,t) for g in 1:G for t in 2:T if uc_forward(d;foil=Foil([(g,t,1-round(Int,nom.u[g,t]))]),limit=30).status=="OPTIMAL"])[1:2]
 for (g,t) in cand,(name,lev) in [("M",UCLevers(noload=false,marginal=true)),("FM",UCLevers(marginal=true))]
  fo=Foil([(g,t,1-round(Int,nom.u[g,t]))]);o=Options(mode=:strong,margin=1e-3*nom.objective,time_limit=300.)
  r=fw_explain(d,fo;options=o,levers=lev)
  ok=missing
  if r["status"]=="VALID"   # independent check with the same verifier as the exact method
   wf=uc_forward(d;delta=r["delta"],zeta=r["zeta"],foil=fo)
   rr=Dict{String,Any}("status"=>"SOLVER_VALIDATED","u"=>wf.u,"p"=>wf.p,"r"=>wf.r,"delta"=>r["delta"],"zeta"=>r["zeta"],"foil_cost"=>wf.objective)
   ok=uc_verify(d,fo,rr;options=o,levers=lev)["valid"]
  end
  println("FW G$G T$T $day $name ",fo.literals," ",r["status"]," obj=",get(r,"objective",nothing)," it",r["iterations"]," ",round(r["seconds"],digits=1),"s verified=",ok);flush(stdout)
 end
end
