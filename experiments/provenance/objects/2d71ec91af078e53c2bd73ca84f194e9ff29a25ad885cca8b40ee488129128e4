module AuditXOPT
using ..XOPT
using JuMP
export naive_explain, coordinate_lower_bound, foil_bounds

# Naive scenario handling: the master uses the expanded capacity, but competitors are
# separated in the nominal region. This mirrors reusing a nominal competitor pool and
# is used only to measure what scenario-specific separation prevents.
function naive_explain(d::Instance,foil::Foil;options=Options(),capacity=d.capacity,capcost=0.,oracle_capacity=d.capacity)
    opt=options;t0=time();remaining()=opt.time_limit-(time()-t0)
    active=Int.(abs.(capacity.-d.capacity).>opt.tolerance);cuts=0;lb=0.
    stop(status,k=0)=Result(status=status,seconds=time()-t0,iterations=k,cuts=cuts,lower_bound=lb)
    remaining()<=0 && return stop("TIME_LIMIT")
    M=XOPT.master(d,foil,opt,capacity,active,capcost,remaining())
    offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    for iteration in 1:opt.max_iterations
        remaining()<=0 && return stop("TIME_LIMIT",iteration)
        set_time_limit_sec(M.m,max(.001,remaining()));optimize!(M.m)
        lb=max(lb,objective_bound(M.m));status=string(termination_status(M.m))
        status=="INFEASIBLE" && return stop("SOLVER_INFEASIBLE",iteration)
        status!="OPTIMAL" && return stop(status,iteration)
        delta=value.(M.delta);fc=value(M.foilcost);obj=objective_value(M.m)
        r=forward(d;cost=d.fixed.+delta,capacity=oracle_capacity,
            foil=opt.mode==:strong ? foil : nothing,complement=opt.mode==:strong,limit=remaining())
        if (r.status=="INFEASIBLE" && opt.mode==:strong) || (r.status=="OPTIMAL" && XOPT.numerical_acceptance(fc,r.bound,offset,opt.tolerance))
            changed=abs.(delta).>opt.tolerance
            return Result(status="SOLVER_VALIDATED",objective=obj,lower_bound=lb,seconds=time()-t0,iterations=iteration,cuts=cuts,
                delta=delta,y=round.(value.(M.b.y)),q=value.(M.b.q),state=value.(M.b.s),
                changed_periods=sum(vec(any(changed,dims=1)).|(active.>0)),changed_parameters=sum(changed)+sum(active))
        end
        r.status!="OPTIMAL" && return stop(r.status,iteration)
        fc-r.objective<=offset+opt.tolerance && return stop("NUMERICAL_UNRESOLVED",iteration)
        XOPT.add_cut!(M,d,r,opt);cuts+=1
    end
    stop("ITERATION_LIMIT",opt.max_iterations)
end

# Bounds on the best foil value alpha and the best nonfoil value beta at nominal costs.
function foil_bounds(d::Instance,foil::Foil;limit=120.)
    inside=forward(d;foil=foil,limit=limit)
    outside=forward(d;foil=foil,complement=true,limit=limit)
    Dict{String,Any}("inside_status"=>inside.status,"alpha_lb"=>isfinite(inside.bound) ? inside.bound : nothing,
        "alpha_ub"=>isfinite(inside.objective) ? inside.objective : nothing,
        "outside_status"=>outside.status,"beta_lb"=>isfinite(outside.bound) ? outside.bound : nothing,
        "beta_ub"=>isfinite(outside.objective) ? outside.objective : nothing,"amax"=>maximum(d.fixed))
end

# Valid lower bound on the intervention objective in the nominal scenario (any binary foil):
# every explanation needs sum_j |delta_j| >= alpha - beta + s, and sum_j |delta_j|/a_j >= that / max a.
function coordinate_lower_bound(b,mode;epsilon=0.,margin=0.,lambda=0.,tol=1e-6)
    b["inside_status"]=="OPTIMAL" || return nothing
    b["outside_status"]=="INFEASIBLE" && return 0.
    b["outside_status"]=="OPTIMAL" || return nothing
    s=mode=="strong" ? margin : -epsilon
    D=max(0.,b["alpha_lb"]-b["beta_ub"]+s)
    D/b["amax"]+(D>tol ? lambda : 0.)
end
end
