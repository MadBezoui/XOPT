using JSON3,SHA,Dates
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","anytime.jl"));using .AnytimeXOPT
root=normpath(joinpath(@__DIR__,"..",".."))
records=Any[]
for profile in ["extended","compound","capacity_stress","timing_repairs"]
    path=joinpath(root,"experiments/results/revision_$(profile).jsonl")
    source=bytes2hex(sha256(read(path)))
    for line in eachline(path)
        a=JSON3.read(line)
        haskey(a,:output) || continue
        out=a.output
        isnothing(out.upper_bound) && continue
        m=a.instance;I=Int(m.I);T=Int(m.T);mat(x)=reshape(Float64.(x),I,T)
        d=Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
        foil=Foil([Tuple(Int.(x)) for x in a.foil])
        o=Options(mode=Symbol(a.mode),epsilon=Float64(a.epsilon),margin=Float64(a.margin),k_time=Int(a.K),time_limit=120.)
        capacity=copy(d.capacity);capcost=0.
        if profile=="capacity_stress"
            inc=Float64.(a.increments[Int(out.scenario)])
            capacity.+=inc;capcost=sum(abs.(inc)./d.capacity)
        end
        saved=out.result
        r=Result(status="FEASIBLE_VALIDATED",objective=Float64(out.upper_bound),delta=mat(saved.delta),y=mat(saved.y),q=mat(saved.q),state=mat(saved.state))
        start=time();v=validate_incumbent(d,foil,r,o;capacity=capacity,limit=120.)
        cost,nt,np=AnytimeXOPT.intervention_cost(d,r,o,capacity,capcost)
        binary=all(abs(y-round(y))<=1e-8 && -1e-8<=y<=1+1e-8 for y in r.y)
        bound_consistent=cost<=r.objective+1e-5 && !isnothing(out.lower_bound) && out.lower_bound<=r.objective+1e-5
        valid=v["valid"]&&binary&&bound_consistent
        push!(records,Dict("profile"=>profile,"key"=>String(a.key),"valid"=>valid,"verification"=>v,
            "binary"=>binary,"objective_upper_bound_consistent"=>bound_consistent,"canonical_intervention_cost"=>cost,
            "reported_upper_bound"=>r.objective,"seconds"=>time()-start,"input_sha256"=>source))
        println(profile," ",a.key," ",valid);flush(stdout)
    end
end
report=Dict("checked"=>length(records),"valid"=>all(r["valid"] for r in records),"records"=>records,
    "description"=>"Post-run fresh numerical oracle and direct witness checks; same solver, no exact proof certificate; excluded from algorithm timings.",
    "created_utc"=>string(now(UTC)),"validator_sha256"=>bytes2hex(sha256(read(@__FILE__))))
open(joinpath(root,"experiments/results/revision_validation.json"),"w") do io;JSON3.write(io,report);end
report["valid"] || error("A saved supplementary incumbent failed fresh validation; inspect the retained report")
println("Validated ",length(records)," saved supplementary incumbents")
