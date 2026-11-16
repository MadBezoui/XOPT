# Recheck the recorded intervention, not the unrecorded historical witness.
# Read-only historical inputs; writes a new, explicitly linked output.
using JSON3, SHA, Dates
include(joinpath(@__DIR__, "..", "src", "XOPT.jl")); using .XOPT
include(joinpath(@__DIR__, "..", "src", "anytime.jl")); using .AnytimeXOPT
const ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const RES = joinpath(ROOT, "experiments", "results")
const OUT = joinpath(RES, "corrections_20261028", "single_lever_revalidated.jsonl")
const SCRIPT = relpath(@__FILE__, ROOT)
digest(p) = bytes2hex(sha256(read(p)))
source_hashes = Dict(p=>digest(joinpath(ROOT,p)) for p in ["experiments/src/XOPT.jl", "experiments/src/anytime.jl", SCRIPT])
oldfile = joinpath(RES, "single_lever.jsonl")
oldhash = digest(oldfile)
parents = Dict{Tuple{String,String},Tuple{Any,String,String}}()
for profile in ("main", "scale", "long")
    path=joinpath(RES, profile*".jsonl"); fh=digest(path)
    for line in eachline(path)
        a=JSON3.read(line)
        String(a.job.method)=="ccg" || continue
        k=(profile,String(a.key))
        haskey(parents,k) && error("Duplicate parent: $k")
        parents[k]=(a,bytes2hex(sha256(line)),fh)
    end
end
isfile(OUT) && error("Output already exists; retain it and choose a new independently documented path")
mkpath(dirname(OUT)); temp=OUT*".part"
checks=0;passed=0
open(temp,"w") do io
 for line in eachline(oldfile)
    global checks,passed
    a=JSON3.read(line)
    String(a.status)=="RESTRICTED_SOLVER_OPTIMAL" || continue
    key=(String(a.profile),String(a.key)); haskey(parents,key)||error("Missing historical parent: $key")
    p,parent_line_hash,parent_file_hash=parents[key];m=p.instance
    I,T=Int(m.I),Int(m.T);mat(x)=reshape(Float64.(x),I,T)
    d=Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
    f=Foil([Tuple(Int.(x)) for x in p.foil]); i,t,b=only(f.literals)
    amount=Float64(a.amount);delta=zeros(I,T);delta[i,t]=(1-2b)*amount
    o=Options(mode=Symbol(p.job.mode),epsilon=Float64(p.job.epsilon),margin=Float64(p.job.margin),k_time=Int(p.job.K),time_limit=60.)
    z=forward(d;cost=d.fixed.+delta,foil=f,limit=60.)
    verification=nothing; witness=nothing; objective_residual=abs((amount/d.fixed[i,t]+(amount>1e-6 ? .01 : 0.))-Float64(a.objective))
    if z.status=="OPTIMAL"
        r=Result(status="FEASIBLE_VALIDATED",delta=delta,y=z.y,q=z.q,state=z.state)
        verification=validate_incumbent(d,f,r,o;limit=60.)
        witness=resultdict(r)
    end
    valid=!isnothing(verification) && verification["valid"] && objective_residual<=1e-5
    rec=Dict("profile"=>key[1],"key"=>key[2],"status"=>(valid ? "VALIDATED" : "UNRESOLVED"),
      "scope"=>"Fresh witness reconstructed for historical intervention; not the original witness or an exact optimality proof",
      "historical_amount"=>amount,"historical_objective"=>Float64(a.objective),"objective_residual"=>objective_residual,
      "historical_file_sha256"=>oldhash,"historical_record_sha256"=>bytes2hex(sha256(line)),
      "parent_file_sha256"=>parent_file_hash,"parent_record_sha256"=>parent_line_hash,
      "source_sha256"=>source_hashes,"forward_status"=>z.status,"verification"=>verification,"witness"=>witness,
      "recorded_utc"=>string(now(UTC)),"julia"=>string(VERSION))
    JSON3.write(io,rec);write(io,'\n');flush(io)
    checks+=1;passed+=valid
    println(checks," ",key," ",rec["status"]);flush(stdout)
 end
end
checks==94 || error("Expected 94 recorded interventions, found $checks; partial results retained in $temp")
mv(temp,OUT;force=false)
println("Reconstructed intervention witnesses validated: ",passed,"/",checks)
passed==checks || error("Some interventions unresolved; see $OUT")
