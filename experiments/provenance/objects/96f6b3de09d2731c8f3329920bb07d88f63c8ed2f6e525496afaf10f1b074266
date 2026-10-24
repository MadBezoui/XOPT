using JSON3,SHA,Dates,Random,Statistics
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","anytime.jl"));using .AnytimeXOPT
include(joinpath(@__DIR__,"..","src","robustness.jl"))
include(joinpath(@__DIR__,"..","src","audit.jl"));using .AuditXOPT
const ROOT=normpath(joinpath(@__DIR__,"..",".."))
# Usage: julia run_audit.jl <profile> <worker> <workers> [smoke]
profile=ARGS[1];worker=parse(Int,ARGS[2]);workers=parse(Int,ARGS[3]);smoke=length(ARGS)>3 && ARGS[4]=="smoke"
dir=joinpath(ROOT,smoke ? "experiments/release" : "experiments/results")
file=joinpath(dir,"audit_$(profile)_w$(worker)$(smoke ? "_smoke" : "").jsonl")
hashes=Dict(p=>bytes2hex(sha256(read(joinpath(ROOT,p)))) for p in ["experiments/src/XOPT.jl","experiments/src/anytime.jl",
  "experiments/src/robustness.jl","experiments/src/audit.jl","experiments/scripts/run_audit.jl","experiments/docs/audit_protocol_20261017.md"])
seen=Set{String}()
if isfile(file)
 for line in eachline(file)
  a=JSON3.read(line);Dict(String(k)=>String(v) for (k,v) in pairs(a.source_sha256))==hashes || error("Source changed; archive previous audit records before resuming")
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
meta(d,m)=Dict("id"=>d.id,"family"=>String(d.family),"I"=>size(d.demand,1),"T"=>size(d.demand,2),"seed"=>Int(m.seed),
 "demand"=>d.demand,"capacity"=>d.capacity,"fixed"=>d.fixed,"unit"=>d.unit,"holding"=>d.holding,"retention"=>d.retention,"initial"=>d.initial,
 "series"=>m.series,"first_period"=>m.first_period,"scales"=>m.scales)
records(p)=[JSON3.read(l) for l in eachline(joinpath(ROOT,"experiments/results/$p.jsonl"))]
mine(jobs)=[j for (n,j) in enumerate(jobs) if mod(n-1,workers)==worker-1]
foilof(a)=Foil([Tuple(Int.(x)) for x in a.foil])
function sparsity_foils()
 panels=Dict(String(a.instance.id)=>a.instance for a in records("main") if Int(a.instance.I)==3 && Int(a.instance.T)==8)
 out=Any[]
 for id in sort(collect(keys(panels)))
  m=panels[id];d=restore(m);nominal=forward(d;limit=60.);nominal.status=="OPTIMAL"||error("Nominal unresolved: $id")
  for k in [2,3,4]
   push!(out,(m,d,k,Foil([(1+mod(Int(m.seed)+l-2,Int(m.I)),2l,1-round(Int,nominal.y[1+mod(Int(m.seed)+l-2,Int(m.I)),2l])) for l in 1:k])))
  end
 end
 out
end
# Compilation warmup for every entry point used below.
w=Instance("warmup",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));wf=Foil([(1,2,1)])
for mode in [:weak,:strong]
 o=Options(mode=mode,margin=.02,time_limit=30.)
 anytime_explain(w,wf;options=o,initialize=false);anytime_explain(w,wf;options=o,initialize=true)
 r=explain(w,wf;options=o);naive_explain(w,wf;options=o,capacity=[2.5,2.],capcost=.25)
 r.status=="SOLVER_VALIDATED" && witness_radius(w,wf,r;rho_max=.5);foil_bounds(w,wf;limit=10.)
end
if profile=="long"
 cohort=sort([a for a in vcat(records("scale"),records("long")) if
   (String(a.instance.family),Int(a.instance.I),Int(a.instance.T)) in [("hospital",10,11),("retail",5,24),("retail",10,32)]];by=a->(String(a.instance.id),String(a.job.mode)))
 jobs=[(a,b,meth) for a in cohort for b in (Int(a.instance.seed)==1 ? [600.,1800.] : [600.]) for meth in ["cold","warm"]]
 sort!(jobs;by=j->(-j[2],String(j[1].instance.id),String(j[1].job.mode),j[3]))
 for (a,budget,method) in mine(jobs)
  budget=smoke ? 3. : budget
  key="$(a.instance.id)|$(a.job.mode)|$method|$budget";key in seen&&continue
  d=restore(a.instance);f=foilof(a);o=Options(mode=Symbol(a.job.mode),margin=Float64(a.job.margin),epsilon=Float64(a.job.epsilon),k_time=Int(a.job.K),time_limit=budget)
  GC.gc();r=anytime_explain(d,f;options=o,initialize=method=="warm")
  write_record(key,Dict{String,Any}("instance"=>meta(d,a.instance),"foil"=>f.literals,"mode"=>String(o.mode),"method"=>method,"budget"=>budget,"K"=>o.k_time,"epsilon"=>o.epsilon,"margin"=>o.margin,"status"=>r["status"],"output"=>r))
  smoke && break
 end
elseif profile=="sparsity"
 jobs=[(x,mode,K,cb) for x in sparsity_foils() for mode in [:weak,:strong] for K in [1,2,3,4,8] for cb in [.8,.4]]
 for ((m,d,k,f),mode,K,cb) in mine(jobs)
  key="$(d.id)|$k|$mode|$K|$cb";key in seen&&continue
  o=Options(mode=mode,k_time=K,margin=.02,cost_bound=cb,lambda_time=0.,lambda_param=0.,time_limit=smoke ? 3. : 30.)
  physical=forward(d;foil=f,limit=30.).status
  GC.gc();r=anytime_explain(d,f;options=o,initialize=false)
  write_record(key,Dict{String,Any}("instance"=>meta(d,m),"foil"=>f.literals,"literal_count"=>k,"mode"=>String(mode),"K"=>K,"cost_bound"=>cb,"margin"=>.02,"epsilon"=>0.,"physical_foil_status"=>physical,"budget"=>o.time_limit,"status"=>r["status"],"output"=>r))
  smoke && break
 end
elseif profile=="margin"
 queries=[a for a in records("main") if String(a.job.method)=="ccg" && String(a.job.mode)=="strong"]
 jobs=[(a,g) for a in queries for g in [.01,.02,.05,.1,.2,.5]]
 for (a,g) in mine(jobs)
  key="$(a.instance.id)|strong|$g";key in seen&&continue
  d=restore(a.instance);f=foilof(a);o=Options(mode=:strong,margin=g,k_time=Int(a.job.K),time_limit=smoke ? 3. : 15.)
  GC.gc();r=explain(d,f;options=o)
  rec=Dict{String,Any}("instance"=>meta(d,a.instance),"foil"=>f.literals,"mode"=>"strong","margin"=>g,"nominal_objective"=>a.nominal_objective,"status"=>r.status,"result"=>resultdict(r))
  if r.status=="SOLVER_VALIDATED"
   rec["verification"]=verify(d,f,r;options=o)
   rec["radius"]=witness_radius(d,f,r;rho_max=.5,time_limit=30.)
  end
  write_record(key,rec);smoke && break
 end
elseif profile=="naive"
 menus=Any[]
 for a in records("capacity")
  push!(menus,(a,restore(a.instance),foilof(a),Symbol(a.job.mode),[Float64.(x) for x in a.increments],"primary"))
 end
 for a in records("revision_capacity_stress")
  haskey(a,:foil) || continue
  push!(menus,(a,restore(a.instance),foilof(a),Symbol(a.mode),[Float64.(x) for x in a.increments],"stress_$(a.factor)"))
 end
 jobs=[(x,j) for x in menus for j in 2:length(x[5])]
 for ((a,d,f,mode,incs,source),j) in mine(jobs)
  key="$source|$(d.id)|$mode|$j";key in seen&&continue
  inc=incs[j];cap=d.capacity.+inc;capcost=sum(abs.(inc)./d.capacity)
  o=Options(mode=mode,k_time=3,margin=.02,time_limit=smoke ? 3. : 30.)
  GC.gc();rc=explain(d,f;options=o,capacity=cap,capcost=capcost)
  GC.gc();rn=naive_explain(d,f;options=o,capacity=cap,capcost=capcost,oracle_capacity=d.capacity)
  rec=Dict{String,Any}("source"=>source,"id"=>d.id,"family"=>String(d.family),"foil"=>f.literals,"mode"=>String(mode),"scenario"=>j,"increment"=>inc,"capcost"=>capcost,
     "correct"=>resultdict(rc),"naive"=>resultdict(rn),"status"=>"$(rc.status)/$(rn.status)")
  rc.status=="SOLVER_VALIDATED" && (rec["correct_verification"]=verify(d,f,rc;options=o,capacity=cap))
  rn.status=="SOLVER_VALIDATED" && (rec["naive_verification"]=verify(d,f,rn;options=o,capacity=cap))
  write_record(key,rec);smoke && break
 end
elseif profile=="bound"
 pairs_=Dict{String,Any}()
 for p in ["main","scale","long"],a in records(p)
  String(a.job.method)=="ccg" || continue
  d=restore(a.instance);f=foilof(a);pairs_["$(d.id)|$(f.literals)"]=(d,f,p)
 end
 for a in records("revision_compound")
  d=restore(a.instance);f=foilof(a);pairs_["$(d.id)|$(f.literals)"]=(d,f,"compound")
 end
 for (m,d,k,f) in sparsity_foils();pairs_["$(d.id)|$(f.literals)"]=(d,f,"sparsity");end
 for key in mine(sort(collect(keys(pairs_))))
  key in seen&&continue
  d,f,src=pairs_[key];b=foil_bounds(d,f;limit=smoke ? 3. : 120.)
  b["id"]=d.id;b["foil"]=f.literals;b["source"]=src;b["I"]=size(d.demand,1);b["T"]=size(d.demand,2);b["family"]=String(d.family);b["status"]="$(b["inside_status"])/$(b["outside_status"])"
  write_record(key,b);smoke && break
 end
else;error("Unknown audit profile")
end
