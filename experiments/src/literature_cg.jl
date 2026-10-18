"""
Independent implementation of the cost-only constraint-generation scheme in
Engelhardt et al., arXiv:2510.17624v2, Algorithm 1 / equation (7), and the
outside-foil comparison in equation (14).

This is NOT the authors' Python software. Their archived implementation
optimizes integer constraint coefficients. We retain their published
master/separation scheme and use the current continuous cost domain,
gamma-margin, support constraints and forward MILP for a matched comparison.
The physical builder and forward oracle are shared to avoid backend effects;
the inverse master, cuts, and iteration loop are implemented here separately.
No call to XOPT.master, XOPT.add_cut!, or XOPT.explain is made.
"""
function literature_cg(d,foil;options=XOPT.Options())
    opt=options; start=time(); remaining()=opt.time_limit-(time()-start)
    I,T=size(d.demand); offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    b=XOPT.physical_model(d;limit=remaining()); m=b.m
    XOPT.add_foil!(m,b.y,foil)
    bound=opt.cost_bound.*d.fixed
    @variable(m,-bound[i,t]<=edit[i=1:I,t=1:T]<=bound[i,t])
    @variable(m,magnitude[1:I,1:T]>=0)
    @variable(m,period[1:T],Bin)
    @variable(m,support[1:I,1:T],Bin)
    @variable(m,product[1:I,1:T])
    for t in 1:T,i in 1:I
        @constraint(m,magnitude[i,t]>=edit[i,t])
        @constraint(m,magnitude[i,t]>=-edit[i,t])
        @constraint(m,edit[i,t]<=bound[i,t]*support[i,t])
        @constraint(m,edit[i,t]>=-bound[i,t]*support[i,t])
        @constraint(m,support[i,t]<=period[t])
        @constraint(m,product[i,t]<=bound[i,t]*b.y[i,t])
        @constraint(m,product[i,t]>=-bound[i,t]*b.y[i,t])
        @constraint(m,product[i,t]<=edit[i,t]+bound[i,t]*(1-b.y[i,t]))
        @constraint(m,product[i,t]>=edit[i,t]-bound[i,t]*(1-b.y[i,t]))
    end
    @constraint(m,sum(period)<=min(T,opt.k_time))
    @constraint(m,sum(support)<=min(I*T,opt.k_param))
    @expression(m,witness,b.base+sum(d.fixed.*b.y)+sum(product))
    @objective(m,Min,sum(magnitude./d.fixed)+opt.lambda_time*sum(period)+opt.lambda_param*sum(support))
    trace=Any[];cuts=0;lb=0.
    stop(status,k)=XOPT.Result(status=status,seconds=time()-start,iterations=k,cuts=cuts,lower_bound=lb,trace=trace)
    for k in 1:opt.max_iterations
        remaining()<=0 && return stop("TIME_LIMIT",k)
        set_time_limit_sec(m,max(.001,remaining()));optimize!(m)
        status=string(termination_status(m));lb=max(lb,objective_bound(m))
        status=="INFEASIBLE" && return stop("SOLVER_INFEASIBLE",k)
        status!="OPTIMAL" && return stop(status,k)
        delta=value.(edit);cost=value(witness)
        other=XOPT.forward(d;cost=d.fixed.+delta,foil=opt.mode==:strong ? foil : nothing,
            complement=opt.mode==:strong,limit=remaining())
        push!(trace,Dict("iteration"=>k,"master"=>objective_value(m),"lower_bound"=>lb,
            "oracle_status"=>other.status,"oracle_bound"=>isfinite(other.bound) ? other.bound : nothing))
        ok=(opt.mode==:strong && other.status=="INFEASIBLE") ||
            (other.status=="OPTIMAL" && XOPT.numerical_acceptance(cost,other.bound,offset,opt.tolerance))
        if ok
            changed=abs.(delta).>opt.tolerance
            return XOPT.Result(status="SOLVER_VALIDATED",objective=objective_value(m),lower_bound=lb,
                seconds=time()-start,iterations=k,cuts=cuts,delta=delta,y=round.(value.(b.y)),
                q=value.(b.q),state=value.(b.s),follower_gap=cost-other.bound,
                changed_periods=sum(vec(any(changed,dims=1))),changed_parameters=sum(changed),trace=trace)
        end
        other.status!="OPTIMAL" && return stop(other.status,k)
        cost-other.objective<=offset+opt.tolerance && return stop("NUMERICAL_UNRESOLVED",k)
        # Full trajectory comparison from (7): its unedited continuous cost
        # is a constant. No explicit pattern recourse table is constructed.
        fixed_part=sum(d.unit.*other.q)+sum(d.holding.*other.state)
        @constraint(m,witness<=sum((d.fixed.+edit).*other.y)+fixed_part+offset)
        cuts+=1
    end
    stop("ITERATION_LIMIT",opt.max_iterations)
end
