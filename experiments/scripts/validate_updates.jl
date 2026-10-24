# Fresh witness checks with corrected code; historical attempts are read-only.
using JSON3, SHA, Dates
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","levers.jl"));using .LeverXOPT
include(joinpath(@__DIR__,"..","src","uc.jl"));using .UCX
const ROOT=normpath(joinpath(@__DIR__,"..",".."))
const RES=joinpath(ROOT,"experiments/results")
const OUT=joinpath(RES,"corrections_20261024")
digest(p)=bytes2hex(sha256(read(p)))
rows(file)=[JSON3.read(line,Dict{String,Any}) for line in eachline(file) if !isempty(strip(line))]
const FILES=Dict(basename(p)=>rows(p) for p in sort(readdir(RES;join=true)) if endswith(p,".jsonl"))
const CHECKS=Any[]
function restore(m)
    I,T=Int(m["I"]),Int(m["T"]);mat=x->reshape(Float64.(x),I,T)
    Instance(m["id"],Symbol(m["family"]),mat(m["demand"]),Float64.(m["capacity"]),mat(m["fixed"]),mat(m["unit"]),mat(m["holding"]),Float64(m["retention"]),Float64.(m["initial"]))
end
foil(a)=Foil([Tuple(Int.(x)) for x in a["foil"]])
function options(a;lambda_time=.01)
    Options(mode=Symbol(get(a,"mode","weak")),margin=Float64(get(a,"margin",.02)),epsilon=Float64(get(a,"epsilon",0.)),
        k_time=Int(get(a,"K",typemax(Int))),cost_bound=Float64(get(a,"cost_bound",.8)),lambda_time=lambda_time,time_limit=60.)
end
function save_check(file,a,variant,v,cost,reported;expected=true,binary=true)
    residual=abs(cost-Float64(reported))
    valid=get(v,"valid",false)&&binary&&residual<=1e-5
    profile=file=="external_reference.jsonl" ? a["profile"]*"|" : ""
    item=Dict("id"=>file*"|"*profile*a["key"]*"|"*variant,"valid"=>valid,"expected_valid"=>expected,"passed"=>valid==expected,
        "verification"=>v,"binary"=>binary,"objective_residual"=>residual)
    push!(CHECKS,item)
    if !item["passed"];println("FAILED ",item["id"]," ",JSON3.write(item));flush(stdout);end
end
function basic(file,a,z,o;variant="result",capacity=nothing,capcost=0.,expected=true,instance=a["instance"])
    d=restore(instance);I,T=size(d.demand);mat=x->reshape(Float64.(x),I,T)
    cap=isnothing(capacity) ? d.capacity : capacity
    r=Result(status="SOLVER_VALIDATED",delta=mat(z["delta"]),y=mat(z["y"]),q=mat(z["q"]),state=mat(z["state"]))
    v=verify(d,foil(a),r;options=o,capacity=cap)
    ch=abs.(r.delta).>o.tolerance;active=abs.(cap.-d.capacity).>o.tolerance
    cost=sum(abs.(r.delta)./d.fixed)+capcost+o.lambda_time*sum(vec(any(ch,dims=1)).|active)+o.lambda_param*(sum(ch)+sum(active))
    binary=all(x->isfinite(x)&&-1e-8<=x<=1+1e-8&&abs(x-round(x))<=1e-8,r.y)
    save_check(file,a,variant,v,cost,z["objective"];expected=expected,binary=binary)
end
function lever_check(file,a,z,variant)
    d=restore(a["instance"]);I,T=size(d.demand);mat=x->reshape(Float64.(x),I,T)
    lev=Levers(fixed=a["levers"]!="PH",unit=a["levers"]!="F",holding=a["levers"]!="F")
    r=Dict(k=>(k in ("delta","zp","zh","y","q","state") ? mat(v) : v) for (k,v) in z)
    o=options(a);v=verify_levers(d,foil(a),r;options=o,levers=lev)
    cost=sum(abs.(r["delta"])./d.fixed)+sum(abs.(r["zp"])./d.unit)+sum(abs.(r["zh"])./d.holding)+o.lambda_time*r["changed_periods"]
    binary=all(x->isfinite(x)&&-1e-8<=x<=1+1e-8&&abs(x-round(x))<=1e-8,r["y"])
    save_check(file,a,variant,v,cost,z["objective"];binary=binary)
end
function uc_check(file,a,z,variant)
    d=uc_restore(JSON3.read(JSON3.write(a["instance"])));G,T=length(d.pmin),length(d.demand);mat=x->reshape(Float64.(x),G,T)
    lev=UCLevers(noload=a["levers"]!="M",marginal=a["levers"] in ("M","FM"))
    r=Dict{String,Any}(k=>(k in ("delta","zeta","u") ? mat(v) : k=="p" ? [reshape(Float64.(x),length(d.width[g]),T) for (g,x) in enumerate(v)] : v) for (k,v) in z)
    r["r"]=Float64.(r["r"]);o=options(a);v=uc_verify(d,foil(a),r;options=o,levers=lev)
    cost=sum(abs.(r["delta"])./repeat(d.noload,1,T))+sum(abs.(r["zeta"])./repeat(UCX.mref(d),1,T))+o.lambda_time*r["changed_periods"]
    binary=all(x->isfinite(x)&&-1e-8<=x<=1+1e-8&&abs(x-round(x))<=1e-8,r["u"])
    save_check(file,a,variant,v,cost,z["objective"];binary=binary)
end
const UC_CORRECTION=JSON3.read(read(joinpath(OUT,"uc_correction.json"),String),Dict{String,Any})
const MENUS=Dict{Tuple{String,String,String},Any}()
for a in FILES["capacity.jsonl"];MENUS[(a["instance"]["id"],a["job"]["mode"],"primary")]=a["instance"];end
for a in FILES["revision_capacity_stress.jsonl"]
    haskey(a,"foil")||continue
    MENUS[(a["instance"]["id"],a["mode"],"stress_"*string(a["factor"]))]=a["instance"]
end
for file in sort(collect(keys(FILES)))
    before=length(CHECKS)
    for a in FILES[file]
        if file in [p*".jsonl" for p in ("correctness","main","sensitivity","scale","capacity","long","multifoil")]
            a["status"]=="SOLVER_VALIDATED"||continue
            z=file=="capacity.jsonl" ? a["menu"]["result"] : a["result"]
            d=restore(a["instance"]);inc=file=="capacity.jsonl" ? Float64.(a["increments"][a["menu"]["scenario"]]) : zeros(length(d.capacity))
            basic(file,a,z,options(a["job"]);variant=file=="capacity.jsonl" ? "menu" : "result",capacity=d.capacity.+inc,capcost=sum(abs.(inc)./d.capacity))
        elseif file=="external_reference.jsonl"
            a["result"]["status"]=="SOLVER_VALIDATED"||continue
            parent=only(x for x in FILES[a["profile"]*".jsonl"] if x["key"]==a["key"])
            copied=merge(parent,Dict("result"=>a["result"]))
            basic(file,copied,a["result"],options(parent["job"]);variant=a["method"])
        elseif startswith(file,"revision_")
            out=get(a,"output",nothing);isnothing(out)&&continue
            isnothing(out["upper_bound"])&&continue
            d=restore(a["instance"]);inc=startswith(file,"revision_capacity_stress") ? Float64.(a["increments"][out["scenario"]]) : zeros(length(d.capacity))
            basic(file,a,out["result"],options(a);capacity=d.capacity.+inc,capcost=sum(abs.(inc)./d.capacity))
        elseif startswith(file,"audit_long_w")||startswith(file,"audit_sparsity_w")
            isnothing(a["output"]["upper_bound"])&&continue
            basic(file,a,a["output"]["result"],options(a;lambda_time=startswith(file,"audit_sparsity") ? 0. : .01))
        elseif startswith(file,"audit_margin_w")
            a["result"]["status"]=="SOLVER_VALIDATED"||continue
            basic(file,a,a["result"],options(a))
        elseif startswith(file,"audit_naive_w")
            m=MENUS[(a["id"],a["mode"],a["source"])];d=restore(m);cap=d.capacity.+Float64.(a["increment"])
            for variant in ("correct","naive")
                a[variant]["status"]=="SOLVER_VALIDATED"||continue
                basic(file,a,a[variant],Options(mode=Symbol(a["mode"]),margin=.02,k_time=3,time_limit=60.);variant=variant,
                    instance=m,capacity=cap,capcost=Float64(a["capcost"]),expected=a[variant*"_verification"]["valid"])
            end
        elseif startswith(file,"levers_enum_w")||startswith(file,"levers_bench_w")
            for variant in (startswith(file,"levers_enum") ? ("dual","trajectory") : ("result",))
                a[variant]["status"]=="SOLVER_VALIDATED"||continue
                lever_check(file,a,a[variant],variant)
            end
        elseif startswith(file,"uc_enum_w")||startswith(file,"uc_bench_w")
            for variant in (startswith(file,"uc_enum") ? ("dual","trajectory") : ("result",))
                z=a["key"]==UC_CORRECTION["key"]&&variant=="dual" ? UC_CORRECTION["result"] : a[variant]
                z["status"]=="SOLVER_VALIDATED"||continue
                uc_check(file,a,z,variant)
            end
        end
    end
    println(file," : ",length(CHECKS)-before," current witness checks");flush(stdout)
end
paths=["experiments/src/XOPT.jl","experiments/src/levers.jl","experiments/src/uc.jl","experiments/scripts/validate_updates.jl","experiments/docs/correction_protocol_20261024.md"]
inputs=Dict("experiments/results/"*file=>digest(joinpath(RES,file)) for file in keys(FILES))
for name in ("uc_correction.json","robustness_revalidated.jsonl");inputs["experiments/results/corrections_20261024/"*name]=digest(joinpath(OUT,name));end
report=Dict("source_sha256"=>Dict(p=>digest(joinpath(ROOT,p)) for p in paths),"input_sha256"=>inputs,"checks"=>CHECKS,
    "all_passed"=>all(c["passed"] for c in CHECKS),"recorded_utc"=>string(now(UTC)),"julia"=>string(VERSION),
    "scope"=>"Fresh Float64 witness admissibility and direct intervention-cost checks with the same models/solver; not a proof of intervention optimality")
path=joinpath(OUT,"current_validation.json");temp=path*".part"
open(temp,"w") do io;JSON3.write(io,report);write(io,'\n');end
mv(temp,path;force=true)
report["all_passed"]||error("Current witness validation failed; inspect current_validation.json")
println("Validated ",length(CHECKS)," current witnesses/negative controls")
