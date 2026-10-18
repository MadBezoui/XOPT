module XOPT
using JuMP, HiGHS, Random, Statistics
const MOI=JuMP.MOI
export Instance,Foil,Options,Result,make_instance,forward,explain,explain_menu,verify,resultdict

struct Instance
    id::String
    family::Symbol
    demand::Matrix{Float64}
    capacity::Vector{Float64}
    fixed::Matrix{Float64}
    unit::Matrix{Float64}
    holding::Matrix{Float64}
    retention::Float64
    initial::Vector{Float64}
end
struct Foil
    literals::Vector{Tuple{Int,Int,Int}}
    function Foil(literals)
        isempty(literals) && throw(ArgumentError("Foil must contain a literal"))
        all(l->l[3] in (0,1),literals) || throw(ArgumentError("Binary values required"))
        length(unique((l[1],l[2]) for l in literals))==length(literals) || throw(ArgumentError("Duplicate foil coordinate"))
        new(literals)
    end
end
Base.@kwdef struct Options
    mode::Symbol=:weak
    epsilon::Float64=0.
    margin::Float64=.01
    cost_bound::Float64=.8
    k_time::Int=typemax(Int)
    k_param::Int=typemax(Int)
    lambda_time::Float64=.01
    lambda_param::Float64=0.
    time_limit::Float64=120.
    tolerance::Float64=1e-6
    max_iterations::Int=1000
end
Base.@kwdef struct Result
    status::String="UNKNOWN"
    objective::Float64=Inf
    lower_bound::Float64=0.
    seconds::Float64=0.
    iterations::Int=0
    cuts::Int=0
    delta::Matrix{Float64}=zeros(0,0)
    y::Matrix{Float64}=zeros(0,0)
    q::Matrix{Float64}=zeros(0,0)
    state::Matrix{Float64}=zeros(0,0)
    follower_gap::Float64=Inf
    changed_periods::Int=0
    changed_parameters::Int=0
    trace::Vector{Any}=Any[]
end
function resultdict(r::Result)
    Dict(string(k)=>(getfield(r,k) isa Float64 && !isfinite(getfield(r,k)) ? nothing : getfield(r,k)) for k in fieldnames(Result))
end
function make_instance(id,family,demand;seed=1,capacity_factor=1.4)
    d=Matrix{Float64}(demand); I,T=size(d); rng=MersenneTwister(seed)
    all(isfinite,d) && minimum(d)>=0 || throw(ArgumentError("Invalid demand"))
    f=(2.0 .+rand(rng,I,T)); u=fill(.25,I,T); h=fill(.2,I,T)
    if family==:retail
        cap=fill(capacity_factor*maximum(vec(sum(d,dims=1))),T)
        initial=zeros(I);rho=1.
    elseif family==:hospital
        rho=.8; initial=copy(d[:,1]); cap=fill(capacity_factor*maximum(vec(sum(d,dims=1))),T)
        h.=.5
    else
        throw(ArgumentError("Unknown family"))
    end
    Instance(id,family,d,cap,f,u,h,rho,initial)
end
function optimizer_model(limit)
    m=Model(HiGHS.Optimizer);set_silent(m)
    set_optimizer_attribute(m,"threads",1)
    set_optimizer_attribute(m,"mip_rel_gap",0.)
    set_optimizer_attribute(m,"mip_abs_gap",1e-8)
    set_optimizer_attribute(m,"primal_feasibility_tolerance",1e-8)
    set_optimizer_attribute(m,"mip_feasibility_tolerance",1e-8)
    set_optimizer_attribute(m,"random_seed",0)
    set_time_limit_sec(m,max(.001,limit));m
end
function physical_model(d::Instance;capacity=d.capacity,limit=120.)
    I,T=size(d.demand); m=optimizer_model(limit)
    @variable(m,y[1:I,1:T],Bin)
    @variable(m,q[1:I,1:T]>=0)
    bound=sum(capacity)+maximum(d.initial)
    @variable(m,0<=s[1:I,1:T]<=bound)
    @constraint(m,[i=1:I,t=1:T],q[i,t]<=capacity[t]*y[i,t])
    @constraint(m,[t=1:T],sum(q[i,t] for i=1:I)<=capacity[t])
    for i=1:I,t=1:T
        prev=t==1 ? d.initial[i] : s[i,t-1]
        consumption=d.family==:retail ? d.demand[i,t] : 0.
        @constraint(m,s[i,t]==d.retention*prev+q[i,t]-consumption)
        if d.family==:hospital; @constraint(m,s[i,t]>=d.demand[i,t]); end
    end
    if d.family==:retail; @constraint(m,[i=1:I],s[i,T]==0);end
    base=@expression(m,sum(d.unit.*q)+sum(d.holding.*s))
    (m=m,y=y,q=q,s=s,base=base)
end
function add_foil!(m,y,foil;complement=false)
    if complement
        @constraint(m,sum(v==1 ? 1-y[i,t] : y[i,t] for (i,t,v) in foil.literals)>=1)
    else
        for (i,t,v) in foil.literals;@constraint(m,y[i,t]==v);end
    end
end
matches(y,foil)=all(round(Int,y[i,t])==v for (i,t,v) in foil.literals)
function forward(d::Instance;cost=d.fixed,capacity=d.capacity,foil=nothing,complement=false,pattern=nothing,excluded=[],limit=120.)
    if limit<=0;return (status="TIME_LIMIT",objective=Inf,bound=-Inf,y=zeros(0,0),q=zeros(0,0),state=zeros(0,0),base=Inf);end
    b=physical_model(d;capacity=capacity,limit=limit);m,y=b.m,b.y
    !isnothing(foil) && add_foil!(m,y,foil;complement=complement)
    if !isnothing(pattern)
        for j in eachindex(y);fix(y[j],pattern[j];force=true);unset_binary(y[j]);end
    end
    for yp in excluded
        @constraint(m,sum(yp[j]>.5 ? 1-y[j] : y[j] for j in eachindex(y))>=1)
    end
    @objective(m,Min,b.base+sum(cost.*y));optimize!(m)
    status=string(termination_status(m)); val=has_values(m)
    (status=status,objective=val ? objective_value(m) : Inf,bound=objective_bound(m),
     y=val ? round.(value.(y)) : zeros(0,0),q=val ? value.(b.q) : zeros(0,0),
     state=val ? value.(b.s) : zeros(0,0),base=val ? value(b.base) : Inf)
end
function master(d,foil,opt,capacity,active,capcost,remaining)
    I,T=size(d.demand);b=physical_model(d;capacity=capacity,limit=remaining);m=b.m
    add_foil!(m,b.y,foil)
    B=opt.cost_bound.*d.fixed
    @variable(m,-B[i,t]<=delta[i=1:I,t=1:T]<=B[i,t])
    @variable(m,a[1:I,1:T]>=0)
    @variable(m,z[1:T],Bin)
    @variable(m,u[1:I,1:T],Bin)
    @variable(m,w[1:I,1:T])
    @constraint(m,[i=1:I,t=1:T],a[i,t]>=delta[i,t])
    @constraint(m,[i=1:I,t=1:T],a[i,t]>=-delta[i,t])
    @constraint(m,[i=1:I,t=1:T],delta[i,t]<=B[i,t]*u[i,t])
    @constraint(m,[i=1:I,t=1:T],delta[i,t]>=-B[i,t]*u[i,t])
    @constraint(m,[i=1:I,t=1:T],u[i,t]<=z[t])
    @constraint(m,[t=1:T],z[t]>=active[t])
    @constraint(m,sum(z)<=min(T,opt.k_time))
    @constraint(m,sum(u)+sum(active)<=min(I*T+T,opt.k_param))
    # Exact convex-hull formulation of w = delta*y because y is binary.
    @constraint(m,[i=1:I,t=1:T],w[i,t]<=B[i,t]*b.y[i,t])
    @constraint(m,[i=1:I,t=1:T],w[i,t]>=-B[i,t]*b.y[i,t])
    @constraint(m,[i=1:I,t=1:T],w[i,t]<=delta[i,t]+B[i,t]*(1-b.y[i,t]))
    @constraint(m,[i=1:I,t=1:T],w[i,t]>=delta[i,t]-B[i,t]*(1-b.y[i,t]))
    foilcost=@expression(m,b.base+sum(d.fixed.*b.y)+sum(w))
    @objective(m,Min,sum(a./d.fixed)+opt.lambda_time*sum(z)+opt.lambda_param*(sum(u)+sum(active))+capcost)
    (m=m,b=b,delta=delta,foilcost=foilcost)
end
function add_cut!(M,d,r,opt)
    offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    @constraint(M.m,M.foilcost<=r.base+sum((d.fixed.+M.delta).*r.y)+offset)
end
# A minimizing oracle's incumbent can disprove a candidate, but only its
# reported lower bound can support numerical acceptance. This is not an
# exact rational certificate: all solver bounds remain floating-point values.
function numerical_acceptance(witness, oracle_bound, offset, tolerance)
    isfinite(witness) && isfinite(oracle_bound) && witness-oracle_bound<=offset+tolerance
end
function explain(d::Instance,foil::Foil;options=Options(),method=:ccg,capacity=d.capacity,capcost=0.)
    opt=options; t0=time();remaining()=opt.time_limit-(time()-t0)
    opt.mode in (:weak,:strong) || throw(ArgumentError("mode"))
    0<=opt.cost_bound<=1 || throw(ArgumentError("cost_bound"))
    opt.epsilon>=0 && opt.margin>=0 || throw(ArgumentError("epsilon/margin"))
    opt.mode==:strong && opt.margin<=opt.tolerance && throw(ArgumentError("strong margin must exceed tolerance"))
    all(d.fixed.>0) || throw(ArgumentError("Positive normalization costs required"))
    method in (:ccg,:multicut,:enumerate) || throw(ArgumentError("method"))
    trace=Any[];cuts=0;lb=0.;I,T=size(d.demand);active=Int.(abs.(capacity.-d.capacity).>opt.tolerance)
    stop(status,k=0)=Result(status=status,seconds=time()-t0,iterations=k,cuts=cuts,lower_bound=lb,trace=trace)
    remaining()<=0 && return stop("TIME_LIMIT")
    M=master(d,foil,opt,capacity,active,capcost,remaining())
    if method==:enumerate
        I*T>20 && throw(ArgumentError("Enumeration restricted to at most 20 binaries"))
        for mask in 0:(2^(I*T)-1)
            remaining()<=0 && return stop("TIME_LIMIT")
            yp=reshape(Float64.([(mask>>(j-1))&1 for j in 1:I*T]),I,T)
            opt.mode==:strong && matches(yp,foil) && continue
            r=forward(d;capacity=capacity,pattern=yp,limit=remaining())
            if r.status=="OPTIMAL";add_cut!(M,d,r,opt);cuts+=1
            elseif r.status!="INFEASIBLE";return stop(r.status);end
        end
    end
    for iteration in 1:opt.max_iterations
        remaining()<=0 && return stop("TIME_LIMIT",iteration)
        set_time_limit_sec(M.m,max(.001,remaining()));optimize!(M.m)
        lb=max(lb,objective_bound(M.m))
        status=string(termination_status(M.m))
        status=="INFEASIBLE" && return stop("SOLVER_INFEASIBLE",iteration)
        status!="OPTIMAL" && return stop(status,iteration)
        delta=value.(M.delta);fc=value(M.foilcost);obj=objective_value(M.m)
        r=forward(d;cost=d.fixed.+delta,capacity=capacity,
            foil=opt.mode==:strong ? foil : nothing,complement=opt.mode==:strong,limit=remaining())
        offset=opt.mode==:strong ? -opt.margin : opt.epsilon
        gap=r.status=="INFEASIBLE" ? -Inf : fc-r.bound
        push!(trace,Dict("iteration"=>iteration,"master"=>obj,"lower_bound"=>lb,
            "oracle_status"=>r.status,"oracle_bound"=>isfinite(r.bound) ? r.bound : nothing,"comparison_tolerance"=>opt.tolerance,"foil_cost"=>fc,"oracle_cost"=>isfinite(r.objective) ? r.objective : nothing,"seconds"=>time()-t0,"cuts"=>cuts))
        if (r.status=="INFEASIBLE" && opt.mode==:strong) || (r.status=="OPTIMAL" && numerical_acceptance(fc,r.bound,offset,opt.tolerance))
            changed=abs.(delta).>opt.tolerance
            return Result(status="SOLVER_VALIDATED",objective=obj,lower_bound=lb,seconds=time()-t0,iterations=iteration,cuts=cuts,
                delta=delta,y=round.(value.(M.b.y)),q=value.(M.b.q),state=value.(M.b.s),follower_gap=gap,
                changed_periods=sum(vec(any(changed,dims=1)).|(active.>0)),changed_parameters=sum(changed)+sum(active),trace=trace)
        end
        r.status!="OPTIMAL" && return stop(r.status,iteration)
        # If the incumbent comparison passes but its lower bound does not,
        # adding that same pattern again does not resolve the numerical gap.
        fc-r.objective<=offset+opt.tolerance && return stop("NUMERICAL_UNRESOLVED",iteration)
        add_cut!(M,d,r,opt);cuts+=1
        if method==:multicut
            excluded=[r.y]
            for extra in 1:2
                remaining()<=0 && return stop("TIME_LIMIT",iteration)
                rr=forward(d;cost=d.fixed.+delta,capacity=capacity,excluded=excluded,
                    foil=opt.mode==:strong ? foil : nothing,complement=opt.mode==:strong,limit=remaining())
                rr.status=="INFEASIBLE" && break
                rr.status!="OPTIMAL" && return stop(rr.status,iteration)
                add_cut!(M,d,rr,opt);cuts+=1;push!(excluded,rr.y)
            end
        end
    end
    stop("ITERATION_LIMIT",opt.max_iterations)
end
function verify(d,foil,r;options=Options(),capacity=d.capacity)
    r.status=="SOLVER_VALIDATED" || return Dict("valid"=>false,"reason"=>"not solver-validated")
    opt=options;I,T=size(d.demand); tol=1e-5
    balance=maximum(abs(r.state[i,t]-d.retention*(t==1 ? d.initial[i] : r.state[i,t-1])-r.q[i,t]+(d.family==:retail ? d.demand[i,t] : 0.)) for i in 1:I,t in 1:T)
    physical=balance<=tol && minimum(r.q)>=-tol && minimum(r.state)>=-tol && maximum(vec(sum(r.q,dims=1)).-capacity)<=tol && maximum(r.q.-r.y.*reshape(capacity,1,:))<=tol && matches(r.y,foil)
    physical &= d.family==:retail ? maximum(abs.(r.state[:,end]))<=tol : minimum(r.state.-d.demand)>=-tol
    active=abs.(capacity.-d.capacity).>opt.tolerance;changed=abs.(r.delta).>opt.tolerance
    actionable=maximum(abs.(r.delta).-opt.cost_bound.*d.fixed)<=tol && sum(vec(any(changed,dims=1)).|active)<=opt.k_time && sum(changed)+sum(active)<=opt.k_param
    z=forward(d;cost=d.fixed.+r.delta,capacity=capacity,foil=opt.mode==:strong ? foil : nothing,complement=opt.mode==:strong,limit=opt.time_limit)
    witness=sum((d.fixed.+r.delta).*r.y)+sum(d.unit.*r.q)+sum(d.holding.*r.state)
    offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    bound_ok=(z.status=="INFEASIBLE" && opt.mode==:strong)||(z.status=="OPTIMAL" && numerical_acceptance(witness,z.bound,offset,tol))
    Dict("valid"=>physical&&actionable&&bound_ok,"arithmetic"=>"Float64","validation_tolerance"=>tol,"exact_certificate"=>false,"physical"=>physical,"actionable"=>actionable,"balance_residual"=>balance,"oracle_status"=>z.status,
        "witness_cost"=>witness,"oracle_bound"=>isfinite(z.bound) ? z.bound : nothing,"gap"=>isfinite(z.bound) ? witness-z.bound : nothing)
end
function explain_menu(d,foil,increments;options=Options(),method=:ccg)
    t0=time(); records=Any[];best=Inf;winner=0;bestresult=nothing;allresolved=true
    order=sortperm([sum(abs.(inc)./d.capacity) for inc in increments])
    for idx in order
        inc=increments[idx];capcost=sum(abs.(inc)./d.capacity);active=sum(abs.(inc).>options.tolerance)
        bound=capcost+options.lambda_time*active+options.lambda_param*active
        if bound>=best-options.tolerance
            push!(records,Dict("scenario"=>idx,"status"=>"PRUNED","lower_bound"=>bound));continue
        end
        remain=options.time_limit-(time()-t0)
        remain<=0 && (allresolved=false;break)
        vals=(; (k=>getfield(options,k) for k in fieldnames(Options) if k!=:time_limit)...)
        opt=Options(;vals...,time_limit=remain)
        r=explain(d,foil;options=opt,method=method,capacity=d.capacity.+inc,capcost=capcost)
        push!(records,Dict("scenario"=>idx,"result"=>resultdict(r)))
        if r.status=="SOLVER_VALIDATED" && r.objective<best
            best=r.objective;winner=idx;bestresult=resultdict(r)
        end
        if !(r.status in ["SOLVER_VALIDATED","SOLVER_INFEASIBLE"]);allresolved=false;end
    end
    Dict("status"=>allresolved ? (isfinite(best) ? "SOLVER_VALIDATED" : "SOLVER_INFEASIBLE") : "TIME_LIMIT",
      "objective"=>isfinite(best) ? best : nothing,"scenario"=>winner,"result"=>bestresult,"seconds"=>time()-t0,"scenarios"=>records)
end
end
