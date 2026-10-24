using JSON3,SHA,Dates,Random,Statistics
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","anytime.jl"));using .AnytimeXOPT
const ROOT=normpath(joinpath(@__DIR__,"..",".."))
profile=isempty(ARGS) ? "extended" : ARGS[1]
smoke=length(ARGS)>1 && ARGS[2]=="smoke"
file=joinpath(ROOT,smoke ? "experiments/release/revision_smoke_$(profile).jsonl" : "experiments/results/revision_$(profile).jsonl")
hashes=Dict(p=>bytes2hex(sha256(read(joinpath(ROOT,p)))) for p in ["experiments/src/XOPT.jl","experiments/src/anytime.jl","experiments/scripts/run_revision.jl","experiments/docs/revision_protocol_20261017.md"])
seen=Set{String}()
if isfile(file)
 for line in eachline(file)
  a=JSON3.read(line);Dict(String(k)=>String(v) for (k,v) in pairs(a.source_sha256))==hashes || error("Source changed; preserve and archive previous extension records before resuming")
  push!(seen,String(a.key))
 end
end
function write_record(key,a)
 a["key"]=key;a["profile"]=profile;a["source_sha256"]=hashes;a["recorded_utc"]=string(now(UTC));a["julia"]=string(VERSION)
 open(file,"a") do io;JSON3.write(io,a);write(io,'\n');flush(io);end
 push!(seen,key);println(key," => ",get(a,"status",get(get(a,"output",Dict()),"status","recorded")));flush(stdout)
end
function restore(m;factor=nothing)
 I=Int(m.I);T=Int(m.T);mat(x)=reshape(Float64.(x),I,T);dem=mat(m.demand)
 cap=isnothing(factor) ? Float64.(m.capacity) : fill(factor*maximum(vec(sum(dem,dims=1))),T)
 Instance(String(m.id),Symbol(m.family),dem,cap,mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
end
function meta(d,m)
 Dict("id"=>d.id,"family"=>String(d.family),"I"=>size(d.demand,1),"T"=>size(d.demand,2),"seed"=>Int(m.seed),
 "demand"=>d.demand,"capacity"=>d.capacity,"fixed"=>d.fixed,"unit"=>d.unit,"holding"=>d.holding,"retention"=>d.retention,"initial"=>d.initial,
 "series"=>m.series,"first_period"=>m.first_period,"scales"=>m.scales)
end
records(p)=[JSON3.read(l) for l in eachline(joinpath(ROOT,"experiments/results/$p.jsonl"))]
# Compilation warmup includes cold, initialized, baseline and menu in both regimes.
w=Instance("warmup",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));wf=Foil([(1,2,1)])
for mode in [:weak,:strong]
 o=Options(mode=mode,margin=.02,time_limit=30.)
 anytime_explain(w,wf;options=o,initialize=false);anytime_explain(w,wf;options=o,initialize=true)
 anytime_explain(w,wf;options=o,baseline_only=true);anytime_menu(w,wf,[zeros(2),[.1,0.]];options=o)
end
if profile=="extended"
 cohort=sort([a for a in vcat(records("scale"),records("long")) if
   (String(a.instance.family),Int(a.instance.I),Int(a.instance.T)) in [("hospital",10,11),("retail",5,24),("retail",10,32)]];by=a->(String(a.instance.id),String(a.job.mode)))
 for (i,a) in enumerate(cohort)
  smoke && i>1 && break
  key="$(a.instance.id)|$(a.job.mode)|baseline|20"
  key in seen && continue
  d=restore(a.instance);f=Foil([Tuple(Int.(x)) for x in a.foil]);o=Options(mode=Symbol(a.job.mode),margin=Float64(a.job.margin),epsilon=Float64(a.job.epsilon),k_time=Int(a.job.K),time_limit=20.)
  GC.gc();r=anytime_explain(d,f;options=o,baseline_only=true)
  write_record(key,Dict{String,Any}("instance"=>meta(d,a.instance),"foil"=>f.literals,"mode"=>String(o.mode),"method"=>"baseline","budget"=>20.,"K"=>o.k_time,"epsilon"=>o.epsilon,"margin"=>o.margin,"output"=>r))
 end
 jobs=[(a,b) for a in cohort for b in (Int(a.instance.seed)==1 ? [20.,60.,120.,300.] : [20.])]
 shuffle!(MersenneTwister(20261017),jobs)
 for (i,(a,budget)) in enumerate(jobs)
  smoke && i>1 && break
  budget=smoke ? 2. : budget
  for method in (isodd(i) ? ["cold","warm"] : ["warm","cold"])
   key="$(a.instance.id)|$(a.job.mode)|$method|$budget";key in seen&&continue
   d=restore(a.instance);f=Foil([Tuple(Int.(x)) for x in a.foil]);o=Options(mode=Symbol(a.job.mode),margin=Float64(a.job.margin),epsilon=Float64(a.job.epsilon),k_time=Int(a.job.K),time_limit=budget)
   GC.gc();r=anytime_explain(d,f;options=o,initialize=method=="warm")
   write_record(key,Dict{String,Any}("instance"=>meta(d,a.instance),"foil"=>f.literals,"mode"=>String(o.mode),"method"=>method,"budget"=>budget,"K"=>o.k_time,"epsilon"=>o.epsilon,"margin"=>o.margin,"output"=>r))
  end
 end
elseif profile in ["compound","capacity_stress"]
 panels=Dict(String(a.instance.id)=>a.instance for a in records("sensitivity"))
 for (panelidx,id) in enumerate(sort(collect(keys(panels))))
  smoke && panelidx>1 && break
  m=panels[id]
  if profile=="compound"
   d=restore(m);nominal=forward(d;limit=30.);nominal.status=="OPTIMAL"||error("Nominal construction unresolved: $id")
   for literals in [2,3]
    f=Foil([(1+mod(Int(m.seed)+k-2,Int(m.I)),2k,1-round(Int,nominal.y[1+mod(Int(m.seed)+k-2,Int(m.I)),2k])) for k in 1:literals])
    physical=forward(d;foil=f,limit=30.)
    for mode in [:weak,:strong],K in [1,2,3,6]
     key="$id|$literals|$mode|$K";key in seen&&continue
     o=Options(mode=mode,k_time=K,margin=.02,time_limit=smoke ? 2. : 15.)
     GC.gc();r=anytime_explain(d,f;options=o,initialize=false)
     write_record(key,Dict{String,Any}("instance"=>meta(d,m),"foil"=>f.literals,"literal_count"=>literals,"mode"=>String(mode),"K"=>K,"margin"=>.02,"epsilon"=>0.,"physical_foil_status"=>physical.status,"budget"=>o.time_limit,"output"=>r))
    end
   end
  else
   for factor in [1.05,1.4]
    d=restore(m;factor=factor);diagnostic_start=time();nominal=forward(d;limit=30.)
    if nominal.status!="OPTIMAL"
     for mode in [:weak,:strong];key="$id|$factor|$mode";key in seen||write_record(key,Dict{String,Any}("status"=>"NOMINAL_"*nominal.status,"instance"=>meta(d,m),"factor"=>factor,"mode"=>String(mode)));end
     continue
    end
    candidates=[(i,t) for t in 2:Int(m.T) for i in 1:Int(m.I) if nominal.y[i,t]>.5]
    if isempty(candidates)
     for mode in [:weak,:strong];key="$id|$factor|$mode";key in seen||write_record(key,Dict{String,Any}("status"=>"NO_ACTIVE_COORDINATE","instance"=>meta(d,m),"factor"=>factor,"mode"=>String(mode)));end
     continue
    end
    i,t=first(candidates);f=Foil([(i,t,0)])
    increments=[zeros(Int(m.T))]
    for t in 1:Int(m.T);inc=zeros(Int(m.T));inc[t]=.25*d.capacity[t];push!(increments,inc);end
    diagnostics=[forward(d;capacity=d.capacity.+inc,foil=f,limit=30.).status for inc in increments]
    diag_seconds=time()-diagnostic_start
    utilization=maximum(vec(sum(nominal.q,dims=1))./d.capacity)
    for mode in [:weak,:strong]
     key="$id|$factor|$mode";key in seen&&continue
     o=Options(mode=mode,k_time=3,margin=.02,time_limit=smoke ? 2. : 30.)
     GC.gc();r=anytime_menu(d,f,increments;options=o)
     write_record(key,Dict{String,Any}("instance"=>meta(d,m),"foil"=>f.literals,"factor"=>factor,"mode"=>String(mode),"K"=>3,"margin"=>.02,"epsilon"=>0.,"budget"=>o.time_limit,"increments"=>increments,"physical_scenario_statuses"=>diagnostics,"diagnostic_seconds"=>diag_seconds,"nominal_peak_utilization"=>utilization,"output"=>r))
    end
   end
  end
 end
else;error("Unknown revision profile")
end
