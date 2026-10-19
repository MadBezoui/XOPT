using JSON3
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
root=normpath(joinpath(@__DIR__,"..",".."));file=joinpath(root,"experiments/results/single_lever.jsonl")
# Archived records are reused; set XOPT_RECOMPUTE=1 to recompute them.
if isfile(file) && filesize(file)>0 && get(ENV,"XOPT_RECOMPUTE","")!="1"; println("Existing records kept: ",file); exit(0); end
# Exact solution for the restricted one-coordinate problem; not asserted globally optimal.
open(file,"w") do io
 for profile in ["main","scale","long"],line in eachline(joinpath(root,"experiments/results/"*profile*".jsonl"))
    a=JSON3.read(line); a.job.method=="ccg" || continue
    m=a.instance;I=Int(m.I);T=Int(m.T);mat(v)=reshape(Float64.(v),I,T)
    d=Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
    foil=Foil([Tuple(Int.(x)) for x in a.foil]);i,t,b=foil.literals[1]
    start=time();z=forward(d;foil=foil,limit=20.)
    rec=Dict{String,Any}("profile"=>profile,"key"=>a.key,"family"=>m.family,"mode"=>a.job.mode,"id"=>m.id,"global_status"=>a.status,"global_objective"=>a.result.objective)
    if z.status=="INFEASIBLE";rec["status"]="FOIL_INFEASIBLE"
    elseif z.status!="OPTIMAL";rec["status"]=z.status
    else
      rem=20.0 - (time()-start);other=forward(d;foil=foil,complement=true,limit=rem)
      if other.status in ["OPTIMAL","INFEASIBLE"]
        offset=a.job.mode=="strong" ? Float64(a.job.margin) : -Float64(a.job.epsilon)
        amount=other.status=="INFEASIBLE" ? 0. : max(0.,z.objective-other.objective+offset)
        if amount<=.8*d.fixed[i,t]+1e-7
          delta=zeros(I,T);delta[i,t]=(1-2b)*amount
          objective=amount/d.fixed[i,t]+(amount>1e-6 ? .01 : 0.)
          r=Result(status="SOLVER_VALIDATED",delta=delta,y=z.y,q=z.q,state=z.state)
          opts=Options(mode=Symbol(a.job.mode),epsilon=Float64(a.job.epsilon),margin=Float64(a.job.margin),time_limit=20.)
          rec["status"]="RESTRICTED_SOLVER_OPTIMAL";rec["objective"]=objective;rec["amount"]=amount;rec["optimization_seconds"]=time()-start
          rec["verification"]=verify(d,foil,r;options=opts)
        else;rec["status"]="EDIT_BOUND_EXCEEDED";rec["required_amount"]=amount;end
      else;rec["status"]=other.status;end
    end
    rec["seconds_with_validation"]=time()-start
    JSON3.write(io,rec);write(io,'\n');flush(io)
 end
end
