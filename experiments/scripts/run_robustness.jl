using JSON3
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","robustness.jl"))
root=normpath(joinpath(@__DIR__,"..",".."));out=joinpath(root,"experiments/results/robustness.jsonl")
# Deterministic fixed-witness audit, all solver-validated CCG explanations in the main study.
open(out,"w") do io
 for line in eachline(joinpath(root,"experiments/results/main.jsonl"))
    a=JSON3.read(line)
    (a.job.method=="ccg" && a.status=="SOLVER_VALIDATED") || continue
    m=a.instance;I=Int(m.I);T=Int(m.T);mat(v)=reshape(Float64.(v),I,T)
    d=Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
    f=Foil([Tuple(Int.(x)) for x in a.foil]);z=a.result
    r=Result(status="SOLVER_VALIDATED",delta=mat(z.delta),y=mat(z.y),q=mat(z.q),state=mat(z.state))
    audit=witness_radius(d,f,r;rho_max=.25,time_limit=20.)
    rec=Dict("key"=>a.key,"id"=>m.id,"family"=>m.family,"mode"=>a.job.mode,"radius"=>audit,"core_source_sha256"=>a.source_sha256)
    JSON3.write(io,rec);write(io,'\n');flush(io)
    println(a.key," ",audit);flush(stdout)
 end
end
