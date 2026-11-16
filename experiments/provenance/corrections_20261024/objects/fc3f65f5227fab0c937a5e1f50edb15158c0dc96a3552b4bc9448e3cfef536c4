using JSON3, SHA, Dates
include(joinpath(@__DIR__, "..", "src", "XOPT.jl")); using .XOPT
include(joinpath(@__DIR__, "..", "src", "uc.jl")); using .UCX
include(joinpath(@__DIR__, "..", "src", "robustness.jl"))

const ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const OUT = joinpath(ROOT, "experiments/results/corrections_20261024")
const CASE = "tiny_2020-07-06_s1_h15|[(3, 2, 1)]|strong|M"
digest(p) = bytes2hex(sha256(read(p)))
const SOURCE_PATHS = ["experiments/src/XOPT.jl", "experiments/src/uc.jl", "experiments/src/robustness.jl",
    "experiments/scripts/run_corrections.jl", "experiments/scripts/run_robustness.jl",
    "experiments/docs/correction_protocol_20261024.md"]
hashes() = Dict(p => digest(joinpath(ROOT,p)) for p in SOURCE_PATHS)
function preserve_previous(path)
    if isfile(path)
        archive = joinpath(OUT,"superseded",Dates.format(now(UTC),"yyyymmddTHHMMSS")*"_"*basename(path))
        mkpath(dirname(archive));cp(path,archive;force=false)
    end
end
function writejson(path, value)
    preserve_previous(path)
    temp=path*".part"
    open(temp,"w") do io; JSON3.write(io,value);write(io,'\n');end
    mv(temp,path;force=true)
end
function uc_correction()
    path=joinpath(OUT,"uc_correction.json");old=nothing;original_file="";original_line=""
    for file in sort(filter(p->startswith(basename(p),"uc_enum_w")&&endswith(p,".jsonl"),readdir(joinpath(ROOT,"experiments/results");join=true))), line in eachline(file)
        a=JSON3.read(line)
        if String(a.key)==CASE
            isnothing(old)||error("Duplicate historical UC case")
            old=a;original_file=relpath(file,ROOT);original_line=line
        end
    end
    isnothing(old)&&error("Missing known UC regression case")
    if isfile(path)&&get(ENV,"XOPT_RECOMPUTE","")!="1"
        a=JSON3.read(read(path,String))
        if Dict(String(k)=>String(v) for (k,v) in pairs(a.source_sha256))==hashes() && a.original_file_sha256==digest(joinpath(ROOT,original_file))
            println("Reusing explicitly bound UC correction");return
        end
    end
    d=uc_restore(old.instance);foil=Foil([Tuple(Int.(x)) for x in old.foil])
    opt=Options(mode=Symbol(old.mode),margin=Float64(old.margin),time_limit=120.)
    lev=UCLevers(noload=false,marginal=true)
    result=uc_explain(d,foil;options=opt,levers=lev,cuts=:dual)
    result["status"]=="SOLVER_VALIDATED"||error("UC correction unresolved: $(result["status"])")
    verification=uc_verify(d,foil,result;options=opt,levers=lev)
    verification["valid"]||error("UC correction witness validation failed")
    abs(result["objective"]-Float64(old.enumeration.objective))<=1e-6||error("UC correction disagrees with independent enumeration")
    out=Dict("key"=>CASE,"original_file"=>original_file,"original_file_sha256"=>digest(joinpath(ROOT,original_file)),
        "original_record_sha256"=>bytes2hex(sha256(original_line)),"historical_objective"=>Float64(old.dual.objective),
        "reference_objective"=>Float64(old.enumeration.objective),"result"=>result,"verification"=>verification,
        "source_sha256"=>hashes(),"recorded_utc"=>string(now(UTC)),"julia"=>string(VERSION),
        "scope"=>"One separately rerun dual-cut case, not a new execution of all UC cases")
    writejson(path,out);println("Corrected UC objective: ",result["objective"])
end
function radius_corrections()
    input=joinpath(ROOT,"experiments/results/main.jsonl");path=joinpath(OUT,"robustness_revalidated.jsonl")
    source=hashes();options=Dict("rho_max"=>.25,"atol"=>1e-5,"time_limit"=>60.)
    if isfile(path)&&get(ENV,"XOPT_RECOMPUTE","")!="1"
        rows=[JSON3.read(l) for l in eachline(path)]
        if length(rows)==50 && all(Dict(String(k)=>String(v) for (k,v) in pairs(a.source_sha256))==source && a.input_sha256==digest(input) && Dict(String(k)=>Float64(v) for (k,v) in pairs(a.options))==options for a in rows)
            println("Reusing 50 fully bound current radius records");return
        end
    end
    preserve_previous(path);temp=path*".part";n=0
    open(temp,"w") do io
        for line in eachline(input)
            a=JSON3.read(line)
            (a.job.method=="ccg"&&a.status=="SOLVER_VALIDATED")||continue
            m=a.instance;I=Int(m.I);T=Int(m.T);mat(x)=reshape(Float64.(x),I,T)
            d=Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
            f=Foil([Tuple(Int.(x)) for x in a.foil]);z=a.result
            r=Result(status="SOLVER_VALIDATED",delta=mat(z.delta),y=mat(z.y),q=mat(z.q),state=mat(z.state))
            radius=witness_radius(d,f,r;rho_max=.25,atol=1e-5,time_limit=60.)
            rec=Dict("key"=>String(a.key),"id"=>String(m.id),"family"=>String(m.family),"mode"=>String(a.job.mode),
                "radius"=>radius,"options"=>options,"source_sha256"=>source,"input_file"=>"experiments/results/main.jsonl",
                "input_sha256"=>digest(input),"input_record_sha256"=>bytes2hex(sha256(line)),"recorded_utc"=>string(now(UTC)),"julia"=>string(VERSION))
            JSON3.write(io,rec);write(io,'\n');flush(io);n+=1
            println("radius ",n," ",a.key," ",radius["status"]);flush(stdout)
        end
    end
    n==50||error("Expected 50 radius records, found $n")
    mv(temp,path;force=true)
end
mkpath(OUT)
mode=isempty(ARGS) ? "all" : first(ARGS)
mode in ("all","uc","radius")||error("Expected all, uc or radius")
mode in ("all","uc")&&uc_correction()
mode in ("all","radius")&&radius_corrections()
