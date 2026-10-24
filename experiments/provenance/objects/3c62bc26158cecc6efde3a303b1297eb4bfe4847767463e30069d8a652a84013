using JSON3,SHA,Dates,Random
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","levers.jl"));using .LeverXOPT
include(joinpath(@__DIR__,"..","src","enumerate_levers.jl"));using .EnumLevers
const ROOT=normpath(joinpath(@__DIR__,"..",".."))
# Usage: julia run_levers.jl <enum|bench> <worker> <workers> [smoke]
profile=ARGS[1];worker=parse(Int,ARGS[2]);workers=parse(Int,ARGS[3]);smoke=length(ARGS)>3 && ARGS[4]=="smoke"
dir=joinpath(ROOT,smoke ? "experiments/release" : "experiments/results")
file=joinpath(dir,"levers_$(profile)_w$(worker)$(smoke ? "_smoke" : "").jsonl")
hashes=Dict(p=>bytes2hex(sha256(read(joinpath(ROOT,p)))) for p in ["experiments/src/XOPT.jl","experiments/src/levers.jl",
  "experiments/src/enumerate_levers.jl","experiments/scripts/run_levers.jl","experiments/docs/levers_protocol_20261017.md"])
seen=Set{String}()
if isfile(file)
 for line in eachline(file)
  a=JSON3.read(line);Dict(String(k)=>String(v) for (k,v) in pairs(a.source_sha256))==hashes || error("Source changed; archive previous lever records before resuming")
  push!(seen,String(a.key))
 end
end
function write_record(key,a)
 a["key"]=key;a["profile"]=profile;a["worker"]=worker;a["source_sha256"]=hashes;a["recorded_utc"]=string(now(UTC));a["julia"]=string(VERSION)
 open(file,"a") do io;JSON3.write(io,a);write(io,'\n');flush(io);end
 push!(seen,key);println(key," => ",get(a,"status","recorded"));flush(stdout)
end
function restore(m)
 I=Int(m.I);T=Int(m.T);mat(x)=reshape(Float64.(x),I,T)
 Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
end
meta(d)=Dict("id"=>d.id,"family"=>String(d.family),"I"=>size(d.demand,1),"T"=>size(d.demand,2),"demand"=>d.demand,"capacity"=>d.capacity,
  "fixed"=>d.fixed,"unit"=>d.unit,"holding"=>d.holding,"retention"=>d.retention,"initial"=>d.initial)
records(p)=[JSON3.read(l) for l in eachline(joinpath(ROOT,"experiments/results/$p.jsonl"))]
mine(jobs)=[j for (n,j) in enumerate(jobs) if mod(n-1,workers)==worker-1]
const LEVERS=Dict("F"=>Levers(fixed=true),"PH"=>Levers(fixed=false,unit=true,holding=true),"FPH"=>Levers(fixed=true,unit=true,holding=true))
summ(r)=Dict{String,Any}(k=>v for (k,v) in r if k!="trace")
# Warmup of every entry point.
w=make_instance("warmup",:retail,[1. 1.;.5 1.];seed=1);wf=Foil([(1,2,1)])
for mode in [:weak,:strong],(_,lev) in LEVERS,cuts in [:dual,:trajectory]
 o=Options(mode=mode,margin=.02,time_limit=30.)
 r=explain_levers(w,wf;options=o,levers=lev,cuts=cuts);r["status"]=="SOLVER_VALIDATED" && verify_levers(w,wf,r;options=o,levers=lev)
end
explain_by_enumeration(make_instance("warmup1",:retail,[1. 1.];seed=1),Foil([(1,2,1)]);options=Options(time_limit=30.),levers=LEVERS["PH"])
if profile=="enum"
 cases=Any[]
 for a in records("main")
  (String(a.instance.family)=="retail" && Int(a.instance.I)==1 && String(a.job.method)=="ccg" && String(a.job.mode)=="weak") || continue
  push!(cases,(restore(a.instance),Foil([Tuple(Int.(x)) for x in a.foil])))
 end
 panels=Dict(String(a.instance.id)=>a.instance for a in records("main") if String(a.instance.family)=="retail" && Int(a.instance.I)==2)
 for id in sort(collect(keys(panels)))
  m=panels[id];d6=restore(m);d=make_instance(replace(id,"I2_T6"=>"I1_T5")*"_derived",:retail,d6.demand[1:1,1:5];seed=Int(m.seed))
  nom=forward(d);push!(cases,(d,Foil([(1,3,1-round(Int,nom.y[1,3]))])))
 end
 jobs=[(d,f,mode,levname) for (d,f) in cases for mode in [:weak,:strong] for levname in ["PH","FPH"]]
 for (d,f,mode,levname) in mine(jobs)
  key="$(d.id)|$(mode)|$(levname)";key in seen&&continue
  lev=LEVERS[levname];o=Options(mode=mode,margin=.02,time_limit=smoke ? 5. : 300.)
  t=time();e=explain_by_enumeration(d,f;options=o,levers=lev);te=time()-t
  rd=explain_levers(d,f;options=o,levers=lev,cuts=:dual);rt=explain_levers(d,f;options=o,levers=lev,cuts=:trajectory)
  vd=rd["status"]=="SOLVER_VALIDATED" ? verify_levers(d,f,rd;options=o,levers=lev) : nothing
  vt=rt["status"]=="SOLVER_VALIDATED" ? verify_levers(d,f,rt;options=o,levers=lev) : nothing
  write_record(key,Dict{String,Any}("instance"=>meta(d),"foil"=>f.literals,"mode"=>String(mode),"levers"=>levname,"margin"=>.02,
    "enumeration"=>Dict{String,Any}(k=>v for (k,v) in e if k!="argmin"),"enumeration_seconds"=>te,"dual"=>summ(rd),"trajectory"=>summ(rt),
    "dual_verification"=>vd,"trajectory_verification"=>vt,"status"=>"$(e["status"])/$(rd["status"])/$(rt["status"])"))
  smoke && break
 end
elseif profile=="bench"
 pool=vcat([a for a in records("main") if String(a.instance.family)=="retail" && String(a.job.method)=="ccg"],
           [a for a in records("scale") if String(a.instance.family)=="retail" && String(a.job.method)=="ccg" && Int(a.instance.I)==5 && Int(a.instance.T) in (8,11)])
 jobs=Any[]
 for a in pool, (levname,cuts) in [("F",:dual),("PH",:dual),("PH",:trajectory),("FPH",:dual),("FPH",:trajectory)]
  push!(jobs,(a,levname,cuts))
 end
 shuffle!(MersenneTwister(20261017),jobs)
 for (a,levname,cuts) in mine(jobs)
  d=restore(a.instance);f=Foil([Tuple(Int.(x)) for x in a.foil]);mode=Symbol(a.job.mode)
  key="$(d.id)|$(mode)|$(levname)|$(cuts)";key in seen&&continue
  lev=LEVERS[levname];o=Options(mode=mode,margin=Float64(a.job.margin),epsilon=Float64(a.job.epsilon),k_time=Int(a.job.K),time_limit=smoke ? 5. : 300.)
  GC.gc();r=explain_levers(d,f;options=o,levers=lev,cuts=cuts)
  v=r["status"]=="SOLVER_VALIDATED" ? verify_levers(d,f,r;options=o,levers=lev) : nothing
  write_record(key,Dict{String,Any}("instance"=>meta(d),"seed"=>Int(a.instance.seed),"foil"=>f.literals,"mode"=>String(mode),"levers"=>levname,"cuts"=>String(cuts),
    "margin"=>o.margin,"primary_status"=>String(a.status),"primary_objective"=>a.status=="SOLVER_VALIDATED" ? a.result.objective : nothing,
    "result"=>summ(r),"trace"=>r["trace"],"verification"=>v,"status"=>r["status"]))
  smoke && break
 end
else;error("Unknown lever profile")
end
