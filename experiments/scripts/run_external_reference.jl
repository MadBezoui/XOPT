using JSON3,SHA,Dates,Random,JuMP
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","literature_cg.jl"))
root=normpath(joinpath(@__DIR__,"..",".."));out=joinpath(root,"experiments/results/external_reference.jsonl")
hashes=Dict(name=>bytes2hex(sha256(read(joinpath(root,"experiments/src",name)))) for name in ["XOPT.jl","literature_cg.jl"])
jobs=Any[]
for profile in ["main","multifoil"],line in eachline(joinpath(root,"experiments/results/"*profile*".jsonl"))
    a=JSON3.read(line);a.job.method=="ccg" && push!(jobs,(profile,a))
end
shuffle!(MersenneTwister(20261017),jobs)
d=make_instance("warmup",:retail,ones(1,3));f=Foil([(1,2,1)])
for mode in [:weak,:strong],method in [:xopt,:literature]
    (method==:xopt ? explain : literature_cg)(d,f;options=Options(mode=mode))
end
open(out,"w") do io
 for (j,(profile,a)) in enumerate(jobs)
    m=a.instance;I=Int(m.I);T=Int(m.T);mat(v)=reshape(Float64.(v),I,T)
    d=Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
    foil=Foil([Tuple(Int.(x)) for x in a.foil]);job=a.job
    opts=Options(mode=Symbol(job.mode),epsilon=Float64(job.epsilon),margin=Float64(job.margin),k_time=Int(job.K),time_limit=15.)
    methods=isodd(j) ? [:xopt,:literature] : [:literature,:xopt]
    for method in methods
        GC.gc(); r=(method==:xopt ? explain : literature_cg)(d,foil;options=opts)
        audit=r.status=="SOLVER_VALIDATED" ? verify(d,foil,r;options=opts) : nothing
        rec=Dict("profile"=>profile,"key"=>a.key,"family"=>m.family,"mode"=>job.mode,
            "method"=>string(method),"result"=>resultdict(r),"verification"=>audit,
            "source_sha256"=>hashes,"recorded_utc"=>string(now(UTC)),"reference"=>"arXiv:2510.17624v2 Algorithm 1 / Eq. (14), independent reimplementation")
        JSON3.write(io,rec);write(io,'\n');flush(io)
        isnothing(audit)||audit["valid"]||error("Reference benchmark failed validation")
    end
    println(j,"/",length(jobs)," ",a.key);flush(stdout)
 end
end
