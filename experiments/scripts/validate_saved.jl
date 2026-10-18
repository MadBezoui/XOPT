using JSON3
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
root=normpath(joinpath(@__DIR__,"..",".."));records=Any[]
for profile in ["correctness","main","sensitivity","scale","capacity","long","multifoil"]
 file=joinpath(root,"experiments/results/"*profile*".jsonl");isfile(file)||continue
 for line in eachline(file)
  a=JSON3.read(line);a.status=="SOLVER_VALIDATED"||continue
  m=a.instance;I=Int(m.I);T=Int(m.T);mat(v)=reshape(Float64.(v),I,T)
  d=Instance(String(m.id),Symbol(m.family),mat(m.demand),Float64.(m.capacity),mat(m.fixed),mat(m.unit),mat(m.holding),Float64(m.retention),Float64.(m.initial))
  foil=Foil([Tuple(Int.(x)) for x in a.foil]);job=a.job;capacity=copy(d.capacity)
  z=profile=="capacity" ? a.menu.result : a.result
  if profile=="capacity";capacity.+=Float64.(a.increments[a.menu.scenario]);end
  r=Result(status="SOLVER_VALIDATED",delta=mat(z.delta),y=mat(z.y),q=mat(z.q),state=mat(z.state))
  opts=Options(mode=Symbol(job.mode),epsilon=Float64(job.epsilon),margin=Float64(job.margin),k_time=Int(job.K),time_limit=60.)
  audit=verify(d,foil,r;options=opts,capacity=capacity)
  active=abs.(capacity.-d.capacity).>1e-6;changed=abs.(r.delta).>1e-6
  psi=sum(abs.(r.delta)./d.fixed)+sum(abs.(capacity.-d.capacity)./d.capacity)+.01*sum(vec(any(changed,dims=1)).|active)
  audit["objective_residual"]=abs(psi-Float64(z.objective));audit["valid"] &= audit["objective_residual"]<1e-5
  push!(records,Dict("key"=>a.key,"profile"=>profile,"audit"=>audit))
  audit["valid"]||error("Failed saved witness: $(a.key)")
 end
end
open(joinpath(root,"experiments/results/saved_witness_validation.json"),"w") do io;JSON3.write(io,Dict("checked"=>length(records),"all_valid"=>all(r["audit"]["valid"] for r in records),"records"=>records));end
println("Validated ",length(records)," saved witnesses, including actual capacity-menu witnesses.")
