using JSON3,SHA,Dates,Random
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","uc.jl"));using .UCX
const ROOT=normpath(joinpath(@__DIR__,"..",".."))
const DATA=joinpath(ROOT,"experiments/data/pglib_uc")
# Usage: julia run_uc.jl <enum|bench> <worker> <workers> [smoke]
profile=ARGS[1];worker=parse(Int,ARGS[2]);workers=parse(Int,ARGS[3]);smoke=length(ARGS)>3 && ARGS[4]=="smoke"
dir=joinpath(ROOT,smoke ? "experiments/release" : "experiments/results")
file=joinpath(dir,"uc_$(profile)_w$(worker)$(smoke ? "_smoke" : "").jsonl")
hashes=Dict(p=>bytes2hex(sha256(read(joinpath(ROOT,p)))) for p in ["experiments/src/XOPT.jl","experiments/src/uc.jl",
  "experiments/scripts/run_uc.jl","experiments/docs/uc_protocol_20261017.md","experiments/data/pglib_uc/SHA256SUMS"])
seen=Set{String}()
if isfile(file)
 for line in eachline(file)
  a=JSON3.read(line);Dict(String(k)=>String(v) for (k,v) in pairs(a.source_sha256))==hashes || error("Source changed; archive previous UC records before resuming")
  push!(seen,String(a.key))
 end
end
function write_record(key,a)
 a["key"]=key;a["profile"]=profile;a["worker"]=worker;a["source_sha256"]=hashes;a["recorded_utc"]=string(now(UTC));a["julia"]=string(VERSION)
 open(file,"a") do io;JSON3.write(io,a);write(io,'\n');flush(io);end
 push!(seen,key);println(key," => ",get(a,"status","recorded"));flush(stdout)
end
mine(jobs)=[j for (n,j) in enumerate(jobs) if mod(n-1,workers)==worker-1]
summ(r)=Dict{String,Any}(k=>v for (k,v) in r if k!="trace")
const DAYS=["2020-01-27","2020-04-03","2020-07-06","2020-10-27"]
# Ten units: two combined cycles, three steam units and five combustion turbines of different cost.
const UNITS=["107_CC_1","213_CC_3","101_STEAM_3","115_STEAM_3","202_STEAM_4","113_CT_1","123_CT_1","207_CT_1","301_CT_3","322_CT_5"]
# Tiny correctness cases: three small turbines with secant cost curves, and two units with their full curves.
const TINY=[(["101_CT_1","201_CT_1","301_CT_1"],true),(["101_CT_1","202_CT_1"],false),(["113_CT_1","301_CT_1"],false)]
# Queries: commitments that differ from the nominal plan, half asking to start and half to stop a unit.
function queries(d,nom,rng,n)
 G,T=size(nom.u);on=[(g,t) for g=1:G,t=1:T if nom.u[g,t]>.5];off=[(g,t) for g=1:G,t=1:T if nom.u[g,t]<.5]
 out=Foil[]
 for (pool,val) in ((off,1),(on,0)),c in shuffle(rng,pool)
  count(f->f.literals[1][3]==val,out)>=n÷2 && continue
  f=Foil([(c[1],c[2],val)]);uc_forward(d;foil=f,limit=60.).status=="OPTIMAL" && push!(out,f)
 end
 out
end
const CONFIGS=Dict("F-R"=>(UCLevers(noload=true),true),"F"=>(UCLevers(noload=true),false),"M"=>(UCLevers(noload=false,marginal=true),false),
  "FM"=>(UCLevers(noload=true,marginal=true),false))
# Warmup of every entry point on a tiny case.
let w=load_uc(joinpath(DATA,"rts_2020-07-06.json"),TINY[1][1];T=2,start=15,ramps=false,secant=true),f=Foil([(3,2,1)])
 for mode in [:weak,:strong],(_,(lev,_)) in CONFIGS,cuts in [:dual,:trajectory]
  o=Options(mode=mode,margin=1.,time_limit=30.);r=uc_explain(w,f;options=o,levers=lev,cuts=cuts)
  r["status"]=="SOLVER_VALIDATED" && uc_verify(w,f,r;options=o,levers=lev)
 end
 uc_explain_by_enumeration(w,f;options=Options(time_limit=30.),levers=CONFIGS["FM"][1])
end
if profile=="enum"
 jobs=Any[]
 for day in DAYS,(si,(units,sec)) in enumerate(TINY),start in (1,15)
  d=load_uc(joinpath(DATA,"rts_$day.json"),units;T=4,start=start,alpha=.6,ramps=false,secant=sec,id="tiny_$(day)_s$(si)_h$(start)")
  nom=uc_forward(d);nom.status=="OPTIMAL" || continue
  for f in queries(d,nom,MersenneTwister(hash(d.id)),2),mode in (:weak,:strong),lev in ("M","FM");push!(jobs,(d,f,mode,lev,nom.objective));end
 end
 for (d,f,mode,levname,nomobj) in mine(jobs)
  key="$(d.id)|$(f.literals)|$(mode)|$(levname)";key in seen&&continue
  lev=CONFIGS[levname][1];o=Options(mode=mode,margin=1e-3*nomobj,time_limit=smoke ? 5. : 300.)
  t=time();e=uc_explain_by_enumeration(d,f;options=o,levers=lev);te=time()-t
  rd=uc_explain(d,f;options=o,levers=lev,cuts=:dual);rt=uc_explain(d,f;options=o,levers=lev,cuts=:trajectory)
  vd=rd["status"]=="SOLVER_VALIDATED" ? uc_verify(d,f,rd;options=o,levers=lev) : nothing
  vt=rt["status"]=="SOLVER_VALIDATED" ? uc_verify(d,f,rt;options=o,levers=lev) : nothing
  write_record(key,Dict{String,Any}("instance"=>uc_meta(d),"foil"=>f.literals,"mode"=>String(mode),"levers"=>levname,"margin"=>o.margin,
   "enumeration"=>Dict{String,Any}(k=>v for (k,v) in e if k!="argmin"),"enumeration_seconds"=>te,"dual"=>summ(rd),"trajectory"=>summ(rt),
   "dual_verification"=>vd,"trajectory_verification"=>vt,"status"=>"$(e["status"])/$(rd["status"])/$(rt["status"])"))
  smoke && break
 end
elseif profile=="bench"
 jobs=Any[]
 for day in DAYS
  d=load_uc(joinpath(DATA,"rts_$day.json"),UNITS;T=12,start=1,ramps=true,id="rts_$(day)_G10_T12")
  nom=uc_forward(d);nom.status=="OPTIMAL" || error("nominal plan infeasible for $day")
  for f in queries(d,nom,MersenneTwister(hash(d.id)),4),mode in (:weak,:strong)
   for (levname,cuts) in [("F-R",:dual),("F",:dual),("M",:dual),("FM",:dual),("FM",:trajectory)];push!(jobs,(d,f,mode,levname,cuts,nom.objective));end
  end
 end
 shuffle!(MersenneTwister(20261017),jobs)
 for (d0,f,mode,levname,cuts,nomobj) in mine(jobs)
  key="$(d0.id)|$(f.literals)|$(mode)|$(levname)|$(cuts)";key in seen&&continue
  lev,ramps=CONFIGS[levname];d=UCX.with_ramps(d0,ramps)
  o=Options(mode=mode,margin=1e-3*nomobj,time_limit=smoke ? 5. : 300.)
  GC.gc();r=uc_explain(d,f;options=o,levers=lev,cuts=cuts)
  v=r["status"]=="SOLVER_VALIDATED" ? uc_verify(d,f,r;options=o,levers=lev) : nothing
  write_record(key,Dict{String,Any}("instance"=>uc_meta(d),"foil"=>f.literals,"mode"=>String(mode),"levers"=>levname,"cuts"=>String(cuts),
   "margin"=>o.margin,"nominal_objective"=>nomobj,"result"=>summ(r),"trace"=>r["trace"],"verification"=>v,"status"=>r["status"]))
  smoke && break
 end
end
