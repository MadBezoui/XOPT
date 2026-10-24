using JSON3,SHA,Dates
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","anytime.jl"));using .AnytimeXOPT
root=normpath(joinpath(@__DIR__,"..",".."))
paths=["experiments/src/XOPT.jl","experiments/src/anytime.jl","experiments/scripts/run_timing_repairs.jl","experiments/docs/revision_protocol_20261017.md","experiments/docs/timing_repair_protocol_20261017.md"]
hashes=Dict(p=>bytes2hex(sha256(read(joinpath(root,p)))) for p in paths)
original=joinpath(root,"experiments/results/revision_extended.jsonl")
lines=readlines(original);rows=JSON3.read.(lines)
bad=Set((String(a.instance.id),String(a.mode),Float64(a.budget)) for a in rows if a.output.seconds>a.budget+max(1.,.05*a.budget))
length(bad)==3||error("Unexpected repair cohort; inspect timing audit")
outpath=joinpath(root,"experiments/results/revision_timing_repairs.jsonl")
seen=Set{String}()
if isfile(outpath)
 for line in eachline(outpath)
  a=JSON3.read(line);Dict(String(k)=>String(v) for (k,v) in pairs(a.source_sha256))==hashes||error("Repair sources changed")
  push!(seen,String(a.key))
 end
end
w=Instance("warmup",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));wf=Foil([(1,2,1)])
for mode in [:weak,:strong]
 o=Options(mode=mode,margin=.02,time_limit=30.)
 anytime_explain(w,wf;options=o,initialize=false);anytime_explain(w,wf;options=o,initialize=true)
 anytime_explain(w,wf;options=o,baseline_only=true);anytime_menu(w,wf,[zeros(2),[.1,0.]];options=o)
end
for (pairidx,query) in enumerate(sort(collect(bad)))
 for method in (isodd(pairidx) ? ["cold","warm"] : ["warm","cold"])
  idx=only(findall(a->(String(a.instance.id),String(a.mode),Float64(a.budget))==query && a.method==method,rows))
  a=rows[idx];String(a.key) in seen&&continue
  m=a.instance;I=Int(m.I);T=Int(m.T);mat(x)=reshape(Float64.(x),I,T)
  d=Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
  f=Foil([Tuple(Int.(x)) for x in a.foil]);o=Options(mode=Symbol(a.mode),margin=Float64(a.margin),epsilon=Float64(a.epsilon),k_time=Int(a.K),time_limit=Float64(a.budget))
  GC.gc();r=anytime_explain(d,f;options=o,initialize=method=="warm")
  rec=Dict{String,Any}(String(k)=>v for (k,v) in pairs(a))
  rec["profile"]="timing_repairs";rec["output"]=r;rec["source_sha256"]=hashes;rec["recorded_utc"]=string(now(UTC));rec["julia"]=string(VERSION)
  rec["replaces_key"]=String(a.key);rec["original_record_sha256"]=bytes2hex(sha256(lines[idx]));rec["original_file_sha256"]=bytes2hex(sha256(read(original)))
  rec["timing_rule_passed"]=r["seconds"]<=a.budget+max(1.,.05*a.budget)
  open(outpath,"a") do io;JSON3.write(io,rec);write(io,'\n');flush(io);end
  println(a.key," => ",r["status"]," timing_ok=",rec["timing_rule_passed"]);flush(stdout)
 end
end
