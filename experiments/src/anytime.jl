module AnytimeXOPT
using ..XOPT
using JuMP
export anytime_explain, anytime_menu, coordinate_baseline, with_options, validate_incumbent

with_options(o;kwargs...) = Options(;merge((; (k=>getfield(o,k) for k in fieldnames(Options))...), (;kwargs...))...)
finite(x)=isfinite(x) ? x : nothing
function check_options(o)
    o.mode in (:weak,:strong) || throw(ArgumentError("mode"))
    0<=o.cost_bound<=1 || throw(ArgumentError("cost_bound"))
    o.epsilon>=0 && o.margin>=0 && o.lambda_time>=0 && o.lambda_param>=0 || throw(ArgumentError("negative parameter"))
    o.mode==:strong && o.margin<=o.tolerance && throw(ArgumentError("margin must exceed tolerance"))
end
function intervention_cost(d,r,o,capacity,capcost)
    changed=abs.(r.delta).>o.tolerance
    active=abs.(capacity.-d.capacity).>o.tolerance
    periods=sum(vec(any(changed,dims=1)).|active)
    parameters=sum(changed)+sum(active)
    sum(abs.(r.delta)./d.fixed)+capcost+o.lambda_time*periods+o.lambda_param*parameters,periods,parameters
end
# The original verifier's status gate is adapted internally: it tests explanation
# feasibility, not global optimality. Public output distinguishes these concepts.
function validate_incumbent(d,foil,r,o;capacity=d.capacity,limit=o.time_limit)
    limit<=0 && return Dict{String,Any}("valid"=>false,"reason"=>"validation deadline")
    adapter=Result(status="SOLVER_VALIDATED",delta=r.delta,y=r.y,q=r.q,state=r.state)
    v=XOPT.verify(d,foil,adapter;options=with_options(o;time_limit=limit),capacity=capacity)
    offset=o.mode==:strong ? -o.margin : o.epsilon
    strict=(o.mode==:strong && get(v,"oracle_status","")=="INFEASIBLE") ||
        (!isnothing(get(v,"oracle_bound",nothing)) && XOPT.numerical_acceptance(v["witness_cost"],v["oracle_bound"],offset,o.tolerance))
    v["valid"] &= strict
    v["comparison_tolerance"]=o.tolerance
    v
end
function coordinate_baseline(d,foil;options=Options(),capacity=d.capacity,capcost=0.)
    o=options;check_options(o);start=time();remaining()=o.time_limit-(time()-start)
    fail(s)= (status=s,result=nothing,verification=nothing,seconds=time()-start)
    length(foil.literals)==1 || return fail("NOT_APPLICABLE")
    remaining()>0 || return fail("TIME_LIMIT")
    i,t,b=only(foil.literals)
    inside=forward(d;foil=foil,capacity=capacity,limit=remaining())
    inside.status=="INFEASIBLE" && return fail("FOIL_INFEASIBLE")
    inside.status=="OPTIMAL" || return fail(inside.status)
    outside=forward(d;foil=foil,complement=true,capacity=capacity,limit=remaining())
    outside.status in ("OPTIMAL","INFEASIBLE") || return fail(outside.status)
    # A reported lower bound is used even for the analytical edit, preventing
    # an optimistic incumbent-only computation when a residual solver gap exists.
    shift=o.mode==:strong ? o.margin : -o.epsilon
    amount=outside.status=="INFEASIBLE" ? 0. : max(0.,inside.objective-outside.bound+shift)
    amount<=o.cost_bound*d.fixed[i,t]+o.tolerance || return fail("EDIT_BOUND_EXCEEDED")
    delta=zeros(size(d.demand));delta[i,t]=(1-2b)*amount
    r=Result(status="FEASIBLE_VALIDATED",delta=delta,y=inside.y,q=inside.q,state=inside.state)
    cost,nt,np=intervention_cost(d,r,o,capacity,capcost)
    nt<=o.k_time && np<=o.k_param || return fail("SUPPORT_BOUND_EXCEEDED")
    v=validate_incumbent(d,foil,r,o;capacity=capacity,limit=remaining())
    v["valid"] || return fail("VALIDATION_UNRESOLVED")
    r=Result(status="FEASIBLE_VALIDATED",objective=cost,delta=delta,y=r.y,q=r.q,state=r.state,changed_periods=nt,changed_parameters=np)
    (status="RESTRICTED_VALIDATED",result=r,verification=v,seconds=time()-start)
end
function seed_master!(M,r,o,capacity,d)
    active=abs.(capacity.-d.capacity).>o.tolerance
    u=Float64.(abs.(r.delta).>o.tolerance);z=Float64.(vec(any(u.>0,dims=1)).|active)
    for (var,vals) in [(M.b.y,r.y),(M.b.q,r.q),(M.b.s,r.state),(M.delta,r.delta),
                       (M.m[:a],abs.(r.delta)),(M.m[:u],u),(M.m[:z],z),(M.m[:w],r.delta.*r.y)]
        for j in eachindex(var);set_start_value(var[j],vals[j]);end
    end
    @constraint(M.m,objective_function(M.m)<=r.objective+o.tolerance)
end
function anytime_explain(d,foil;options=Options(),initialize=true,baseline_only=false,
                         capacity=d.capacity,capcost=0.,seed=nothing)
    o=options;check_options(o);all(d.fixed.>0)||throw(ArgumentError("positive scales"))
    start=time();remaining()=o.time_limit-(time()-start)
    active=Int.(abs.(capacity.-d.capacity).>o.tolerance)
    lb=capcost+o.lambda_time*sum(active)+o.lambda_param*sum(active)
    best=nothing;validation=nothing;first_time=nothing;trace=Any[];cuts=0;iterations=0;warm_status="DISABLED"
    function finish(reason;optimal=false,infeasible=false)
        ub=isnothing(best) ? Inf : best.objective
        status=infeasible ? "SOLVER_INFEASIBLE" : optimal ? "SOLVER_VALIDATED" :
            isnothing(best) ? reason : "FEASIBLE_"*reason
        out=isnothing(best) ? nothing : XOPT.resultdict(best)
        !isnothing(out) && (out["status"]=optimal ? "SOLVER_VALIDATED" : "FEASIBLE_VALIDATED")
        Dict{String,Any}("status"=>status,"termination_reason"=>reason,"upper_bound"=>finite(ub),
          "lower_bound"=>finite(lb),"absolute_gap"=>isfinite(ub) ? max(0.,ub-lb) : nothing,
          "relative_gap"=>isfinite(ub) ? max(0.,ub-lb)/max(1e-9,abs(ub)) : nothing,
          "first_feasible_seconds"=>first_time,"seconds"=>time()-start,"iterations"=>iterations,
          "cuts"=>cuts,"initialization_status"=>warm_status,"result"=>out,"verification"=>validation,"trace"=>trace)
    end
    remaining()>0 || return finish("TIME_LIMIT")
    if !isnothing(seed)
        v=validate_incumbent(d,foil,seed,o;capacity=capacity,limit=remaining())
        if v["valid"]
            cost,nt,np=intervention_cost(d,seed,o,capacity,capcost)
            best=Result(status="FEASIBLE_VALIDATED",objective=cost,delta=seed.delta,y=seed.y,q=seed.q,state=seed.state,changed_periods=nt,changed_parameters=np)
            validation=v;first_time=time()-start;warm_status="REVALIDATED_SEED"
        else;warm_status="SEED_REJECTED";end
    elseif initialize || baseline_only
        allocation=baseline_only ? remaining() : min(20.,o.time_limit/4,remaining())
        base=coordinate_baseline(d,foil;options=with_options(o;time_limit=allocation),capacity=capacity,capcost=capcost)
        warm_status=base.status
        if !isnothing(base.result)
            best=base.result;validation=base.verification;first_time=time()-start
        elseif base.status=="FOIL_INFEASIBLE"
            return finish("FOIL_INFEASIBLE";infeasible=true)
        end
    end
    push!(trace,Dict("event"=>"initialization","seconds"=>time()-start,"status"=>warm_status,
        "upper_bound"=>isnothing(best) ? nothing : best.objective,"lower_bound"=>lb))
    baseline_only && return finish("BASELINE")
    remaining()>0 || return finish("TIME_LIMIT")
    M=XOPT.master(d,foil,o,capacity,active,capcost,remaining())
    !isnothing(best) && seed_master!(M,best,o,capacity,d)
    for k in 1:o.max_iterations
        iterations=k
        remaining()>0 || return finish("TIME_LIMIT")
        set_time_limit_sec(M.m,max(.001,remaining()));optimize!(M.m)
        bound=objective_bound(M.m);isfinite(bound) && (lb=max(lb,bound))
        status=string(termination_status(M.m))
        push!(trace,Dict("event"=>"master","iteration"=>k,"seconds"=>time()-start,"status"=>status,
             "lower_bound"=>finite(lb),"upper_bound"=>isnothing(best) ? nothing : best.objective))
        if !isnothing(best)
            lb>best.objective+1e-5 && return finish("NUMERICAL_UNRESOLVED")
            lb>=best.objective-o.tolerance && return finish("GAP_CLOSED";optimal=true)
        end
        status=="INFEASIBLE" && return isnothing(best) ? finish("INFEASIBLE";infeasible=true) : finish("NUMERICAL_UNRESOLVED")
        status=="OPTIMAL" || return finish(status)
        remaining()>0 || return finish("TIME_LIMIT")
        delta=value.(M.delta);fc=value(M.foilcost)
        oracle=forward(d;cost=d.fixed.+delta,capacity=capacity,foil=o.mode==:strong ? foil : nothing,
            complement=o.mode==:strong,limit=remaining())
        offset=o.mode==:strong ? -o.margin : o.epsilon
        accepted=(oracle.status=="INFEASIBLE" && o.mode==:strong)||
            (oracle.status=="OPTIMAL" && XOPT.numerical_acceptance(fc,oracle.bound,offset,o.tolerance))
        push!(trace,Dict("event"=>"oracle","iteration"=>k,"seconds"=>time()-start,"status"=>oracle.status,
            "bound"=>finite(oracle.bound),"witness_cost"=>fc,"accepted"=>accepted))
        if accepted
            r=Result(status="FEASIBLE_VALIDATED",delta=delta,y=round.(value.(M.b.y)),q=value.(M.b.q),state=value.(M.b.s))
            v=validate_incumbent(d,foil,r,o;capacity=capacity,limit=remaining())
            if v["valid"]
                cost,nt,np=intervention_cost(d,r,o,capacity,capcost)
                # The master objective includes any redundant selected support;
                # using it is a conservative feasible UB under numerical tolerance.
                cost=max(cost,objective_value(M.m))
                r=Result(status="FEASIBLE_VALIDATED",objective=cost,delta=delta,y=r.y,q=r.q,state=r.state,changed_periods=nt,changed_parameters=np)
                if isnothing(best)||r.objective<best.objective
                    best=r;validation=v;isnothing(first_time)&&(first_time=time()-start)
                end
                push!(trace,Dict("event"=>"validated","seconds"=>time()-start,"upper_bound"=>best.objective,"lower_bound"=>lb))
                lb>best.objective+1e-5 && return finish("NUMERICAL_UNRESOLVED")
                return finish("GAP_CLOSED";optimal=best.objective-lb<=1e-5)
            end
            return finish(remaining()<=0 ? "TIME_LIMIT" : "VALIDATION_UNRESOLVED")
        end
        oracle.status=="OPTIMAL" || return finish(oracle.status)
        fc-oracle.objective<=offset+o.tolerance && return finish("NUMERICAL_UNRESOLVED")
        XOPT.add_cut!(M,d,oracle,o);cuts+=1
    end
    finish("ITERATION_LIMIT")
end
function from_dict(r)
    # Internal callers preserve matrix shapes; disk reconstruction is handled by drivers.
    Result(status="FEASIBLE_VALIDATED",objective=r["objective"],delta=r["delta"],y=r["y"],q=r["q"],state=r["state"])
end
function anytime_menu(d,foil,increments;options=Options())
    o=options;check_options(o);start=time();remaining()=o.time_limit-(time()-start)
    n=length(increments);n>0||throw(ArgumentError("empty menu"))
    costs=[sum(abs.(inc)./d.capacity) for inc in increments]
    lbs=[costs[j]+(o.lambda_time+o.lambda_param)*sum(abs.(increments[j]).>o.tolerance) for j in 1:n]
    states=fill("UNVISITED",n);records=Any[];best=nothing;bestver=nothing;winner=0;ub=Inf;first=nothing
    nominal=findfirst(inc->all(abs.(inc).<=o.tolerance),increments)
    seed=nothing
    if !isnothing(nominal) && remaining()>0
        b=coordinate_baseline(d,foil;options=with_options(o;time_limit=min(20.,o.time_limit/4,remaining())))
        if !isnothing(b.result);seed=b.result;best=XOPT.resultdict(seed);bestver=b.verification;winner=nominal;ub=seed.objective;first=time()-start;end
        push!(records,Dict("event"=>"nominal_initialization","status"=>b.status,"seconds"=>time()-start))
    end
    for j in sortperm(lbs)
        if lbs[j]>=ub-o.tolerance;states[j]="PRUNED";continue;end
        remaining()>0 || break
        r=anytime_explain(d,foil;options=with_options(o;time_limit=remaining()),capacity=d.capacity.+increments[j],
            capcost=costs[j],seed=j==nominal ? seed : nothing)
        states[j]=r["status"]
        if r["status"]=="SOLVER_INFEASIBLE";lbs[j]=Inf
        elseif !isnothing(r["lower_bound"]);lbs[j]=max(lbs[j],r["lower_bound"]);end
        if !isnothing(r["upper_bound"]) && r["upper_bound"]<ub
            ub=r["upper_bound"];winner=j;best=r["result"];bestver=r["verification"]
            isnothing(first)&&(first=time()-start)
        end
        push!(records,Dict("scenario"=>j,"result"=>r,"seconds"=>time()-start))
    end
    lb=minimum(lbs);contradiction=isfinite(ub)&&lb>ub+1e-5
    optimal=isfinite(ub)&&!contradiction&&ub-lb<=1e-5
    status=contradiction ? "FEASIBLE_NUMERICAL_UNRESOLVED" : optimal ? "SOLVER_VALIDATED" : all(states.=="SOLVER_INFEASIBLE") ? "SOLVER_INFEASIBLE" : isfinite(ub) ? "FEASIBLE_UNRESOLVED" : "UNRESOLVED"
    Dict("status"=>status,"upper_bound"=>finite(ub),"lower_bound"=>finite(lb),"absolute_gap"=>isfinite(ub) ? max(0.,ub-lb) : nothing,
      "relative_gap"=>isfinite(ub) ? max(0.,ub-lb)/max(1e-9,abs(ub)) : nothing,"seconds"=>time()-start,
      "first_feasible_seconds"=>first,"scenario"=>winner,"result"=>best,"verification"=>bestver,
      "scenario_lower_bounds"=>[finite(x) for x in lbs],"scenario_statuses"=>states,"scenarios"=>records)
end
end
