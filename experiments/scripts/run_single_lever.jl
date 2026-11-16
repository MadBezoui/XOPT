# Resolve the existing ancestor before creating anything, including dangling
# symlinks. Use the canonical paths for the eventual write as well as the guard.
function canonical_driver_path(path)
    candidate = abspath(path)
    suffix = String[]
    visited = Set{String}()
    while !ispath(candidate)
        candidate in visited && error("Output path contains a symbolic-link cycle")
        push!(visited, candidate)
        if islink(candidate)
            target = readlink(candidate)
            candidate = abspath(isabspath(target) ? target : joinpath(dirname(candidate), target))
        else
            pushfirst!(suffix, basename(candidate))
            parent = dirname(candidate)
            parent == candidate && error("Output path has no existing ancestor")
            candidate = parent
        end
    end
    normpath(joinpath(realpath(candidate), suffix...))
end

function driver_inside_history(path, history)
    relative = relpath(path, history)
    !isabspath(relative) && first(splitpath(relative)) != ".."
end

root = normpath(joinpath(@__DIR__, "..", ".."))
history = canonical_driver_path(joinpath(root, "experiments", "results"))
requested_output = get(ENV, "XOPT_RESULTS_DIR", history)
recompute = get(ENV, "XOPT_RECOMPUTE", "") == "1"
recompute && isempty(strip(requested_output)) &&
    error("Set XOPT_RESULTS_DIR outside historical results before recomputing")
outputdir = canonical_driver_path(requested_output)
file = canonical_driver_path(joinpath(outputdir, "single_lever.jsonl"))
# Never truncate frozen attempts, including relative aliases, descendants and
# symlinked result files. Check before loading the model or creating directories.
if recompute && (driver_inside_history(outputdir, history) || driver_inside_history(file, history))
    error("Set XOPT_RESULTS_DIR outside historical results before recomputing historical attempts")
end
if isfile(file) && filesize(file) > 0 && !recompute
    println("Existing records kept: ", file)
    exit(0)
end
mkpath(outputdir)
using JSON3, SHA, Dates
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
source_hashes=Dict(path=>bytes2hex(sha256(read(joinpath(root,path)))) for path in
    ["experiments/src/XOPT.jl", "experiments/scripts/run_single_lever.jl"])
# A bound-based restricted edit and its feasibility check; no global optimum is asserted.
open(file,"w") do io
 for profile in ["main","scale","long"],line in eachline(joinpath(outputdir,profile*".jsonl"))
    a=JSON3.read(line); a.job.method=="ccg" || continue
    m=a.instance;I=Int(m.I);T=Int(m.T);mat(v)=reshape(Float64.(v),I,T)
    d=Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
    foil=Foil([Tuple(Int.(x)) for x in a.foil]);i,t,b=foil.literals[1]
    start=time();z=forward(d;foil=foil,limit=20.)
    input=joinpath(outputdir,profile*".jsonl")
    rec=Dict{String,Any}("profile"=>profile,"key"=>a.key,"family"=>m.family,"mode"=>a.job.mode,"id"=>m.id,"global_status"=>a.status,"global_objective"=>a.result.objective,
      "input_origin"=>(outputdir==history ? "historical" : "new_campaign"),"input_file_sha256"=>bytes2hex(sha256(read(input))),"input_record_sha256"=>bytes2hex(sha256(line)),
      "source_sha256"=>source_hashes,"recorded_utc"=>string(now(UTC)),"julia"=>string(VERSION))
    if z.status=="INFEASIBLE";rec["status"]="FOIL_INFEASIBLE"
    elseif z.status!="OPTIMAL";rec["status"]=z.status
    else
      rem=20.0 - (time()-start);other=forward(d;foil=foil,complement=true,limit=rem)
      if other.status in ["OPTIMAL","INFEASIBLE"]
        offset=a.job.mode=="strong" ? Float64(a.job.margin) : -Float64(a.job.epsilon)
        amount=other.status=="INFEASIBLE" ? 0. : max(0.,z.objective-other.bound+offset)
        if amount<=.8*d.fixed[i,t]+1e-7
          delta=zeros(I,T);delta[i,t]=(1-2b)*amount
          objective=amount/d.fixed[i,t]+(amount>1e-6 ? .01 : 0.)
          r=Result(status="SOLVER_VALIDATED",delta=delta,y=z.y,q=z.q,state=z.state)
          opts=Options(mode=Symbol(a.job.mode),epsilon=Float64(a.job.epsilon),margin=Float64(a.job.margin),time_limit=20.)
          rec["status"]="RESTRICTED_VALIDATED";rec["objective"]=objective;rec["amount"]=amount;rec["optimization_seconds"]=time()-start
          rec["verification"]=verify(d,foil,r;options=opts)
          # The verifier adapter's status is not an optimality certificate.
          rec["witness"]=resultdict(Result(status="FEASIBLE_VALIDATED",delta=delta,y=z.y,q=z.q,state=z.state))
          rec["verification"]["valid"] || (rec["status"]="VALIDATION_UNRESOLVED")
        else;rec["status"]="EDIT_BOUND_EXCEEDED";rec["required_amount"]=amount;end
      else;rec["status"]=other.status;end
    end
    rec["seconds_with_validation"]=time()-start
    JSON3.write(io,rec);write(io,'\n');flush(io)
 end
end
