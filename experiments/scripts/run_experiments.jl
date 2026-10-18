using CSV, DataFrames, JSON3, Dates, Random, Statistics, SHA
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
const ROOT=normpath(joinpath(@__DIR__,"..",".."))
const OUT=joinpath(ROOT,"experiments","results")
profile=isempty(ARGS) ? "main" : ARGS[1]
file=joinpath(OUT,profile*".jsonl")
# Resume only exact record keys within the same profile and source fingerprint.
sourcehash=bytes2hex(sha256(read(joinpath(ROOT,"experiments/src/XOPT.jl"))))
seen=Set{String}()
if isfile(file)
    for l in eachline(file)
        obj=JSON3.read(l); obj.source_sha256==sourcehash || error("Source changed; archive existing $file before rerun")
        push!(seen,String(obj.key))
    end
end
raw=Dict(f=>CSV.read(joinpath(ROOT,"data/processed",f==:retail ? "retail_weekly.csv" : "nhs_monthly.csv"),DataFrame;types=Dict(:series=>String)) for f in [:retail,:hospital])
function instance(family,I,T,seed)
    df=raw[family];codes=unique(df.series);start=mod((seed-1)*I,length(codes)-I+1)+1;selected=codes[start:start+I-1]
    maxperiod=maximum(df.period)
    firstperiod=family==:retail ? min(14+3*(seed-1),maxperiod-T+1) : min(2,maxperiod-T+1)
    d=zeros(I,T);scales=Float64[]
    for (i,code) in enumerate(selected)
        z=sort(df[df.series.==code,:],:period)
        calibration=family==:retail ? mean(z.demand[1:13]) : z.demand[1]
        push!(scales,max(1.,calibration));d[i,:]=z.demand[firstperiod:firstperiod+T-1]./scales[end]
    end
    id="$(family)_I$(I)_T$(T)_s$(seed)"
    x=make_instance(id,family,d;seed=seed)
    meta=Dict("id"=>id,"family"=>string(family),"I"=>I,"T"=>T,"seed"=>seed,"series"=>selected,"first_period"=>firstperiod,"scales"=>scales,
      "demand"=>d,"capacity"=>x.capacity,"fixed"=>x.fixed,"unit"=>x.unit,"holding"=>x.holding,"retention"=>x.retention,"initial"=>x.initial)
    x,meta
end
function store!(key,record)
    record["key"]=key;record["source_sha256"]=sourcehash;record["profile"]=profile;record["recorded_utc"]=string(now(UTC));record["julia"]=string(VERSION)
    open(file,"a") do io;JSON3.write(io,record);write(io,'\n');flush(io);end
    push!(seen,key)
end
# Warm up compilation before timing; all solver models use one thread.
w=make_instance("warmup",:retail,ones(1,3));wf=Foil([(1,2,1)])
for meth in [:ccg,:multicut,:enumerate];explain(w,wf;method=meth,options=Options(time_limit=30.));end
jobs=[]
if profile=="correctness"
    for family in [:retail,:hospital], seed in 1:5, mode in [:weak,:strong], method in [:ccg,:enumerate]
        push!(jobs,(family=family,I=2,T=4,seed=seed,mode=mode,method=method,K=4,epsilon=0.,margin=.02,limit=30.))
    end
elseif profile=="main"
    for family in [:retail,:hospital], (I,T) in [(1,4),(2,6),(3,8)], seed in 1:5, mode in [:weak,:strong], method in [:ccg,:multicut]
        push!(jobs,(family=family,I=I,T=T,seed=seed,mode=mode,method=method,K=T,epsilon=0.,margin=.02,limit=15.))
    end
elseif profile=="sensitivity"
    for family in [:retail,:hospital],seed in 1:4,K in [1,2,6],(mode,eps,margin) in [(:weak,0.,.02),(:weak,.1,.02),(:strong,0.,.1)]
        push!(jobs,(family=family,I=2,T=6,seed=seed,mode=mode,method=:ccg,K=K,epsilon=eps,margin=margin,limit=15.))
    end
elseif profile=="scale"
    for family in [:retail,:hospital],(I,T) in [(5,8),(5,11),(10,11)],seed in 1:3, mode in [:weak,:strong]
        push!(jobs,(family=family,I=I,T=T,seed=seed,mode=mode,method=:ccg,K=T,epsilon=0.,margin=.02,limit=20.))
    end
elseif profile=="multifoil"
    for family in [:retail,:hospital],(I,T) in [(2,6),(3,8)],seed in 1:3,mode in [:weak,:strong]
        push!(jobs,(family=family,I=I,T=T,seed=seed,mode=mode,method=:ccg,K=T,epsilon=0.,margin=.02,limit=15.))
    end
elseif profile=="long"
    for (I,T) in [(5,24),(10,32)],seed in 1:3,mode in [:weak,:strong]
        push!(jobs,(family=:retail,I=I,T=T,seed=seed,mode=mode,method=:ccg,K=T,epsilon=0.,margin=.02,limit=20.))
    end
elseif profile=="capacity"
    for family in [:retail,:hospital],seed in 1:4,mode in [:weak,:strong]
        push!(jobs,(family=family,I=2,T=6,seed=seed,mode=mode,method=:ccg,K=3,epsilon=0.,margin=.02,limit=30.))
    end
else;error("Unknown profile: $profile");end
shuffle!(MersenneTwister(20261016),jobs)
for (j,job) in enumerate(jobs)
    d,meta=instance(job.family,job.I,job.T,job.seed)
    key=join(string.([d.id,job.mode,job.method,job.K,job.epsilon,job.margin]),"|")
    key in seen && continue
    nominal=forward(d;limit=30.)
    if nominal.status!="OPTIMAL"
        store!(key,Dict("instance"=>meta,"job"=>job,"status"=>"NOMINAL_"*nominal.status));continue
    end
    qt=2+mod(job.seed-1,job.T-1);qi=1+mod(job.seed-1,job.I)
    foil=Foil([(qi,qt,1-round(Int,nominal.y[qi,qt]))])
    if profile=="multifoil"
        qi2=mod(qi,job.I)+1;qt2=mod(qt,job.T)+1
        foil=Foil([(qi,qt,1-round(Int,nominal.y[qi,qt])),(qi2,qt2,1-round(Int,nominal.y[qi2,qt2]))])
    end
    opts=Options(mode=job.mode,k_time=job.K,epsilon=job.epsilon,margin=job.margin,time_limit=job.limit)
    rec=Dict{String,Any}("instance"=>meta,"job"=>job,"foil"=>foil.literals,"nominal_objective"=>nominal.objective,"nominal_y"=>nominal.y)
    GC.gc()
    if profile=="capacity"
        increments=[zeros(job.T)]
        for t in 1:job.T;inc=zeros(job.T);inc[t]=.25*d.capacity[t];push!(increments,inc);end
        r=explain_menu(d,foil,increments;options=opts);rec["menu"]=r;rec["increments"]=increments;rec["status"]=r["status"]
        # Menu winner is independently recomputed at exactly the selected capacity.
        if r["scenario"]>0
            inc=increments[r["scenario"]]
            rr=explain(d,foil;options=opts,capacity=d.capacity.+inc,capcost=sum(inc./d.capacity))
            rec["verification"]=verify(d,foil,rr;options=opts,capacity=d.capacity.+inc)
        end
    else
        r=explain(d,foil;options=opts,method=job.method);rec["result"]=resultdict(r);rec["status"]=r.status
        r.status=="SOLVER_VALIDATED" && (rec["verification"]=verify(d,foil,r;options=opts))
    end
    store!(key,rec)
    println("$profile $j/$(length(jobs)) $key => ",rec["status"]);flush(stdout)
end
