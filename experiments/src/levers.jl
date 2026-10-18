module LeverXOPT
# Explanations that may edit activation costs AND continuous recourse costs (unit production
# costs p and holding costs h) in the retail lot-sizing model. Competitor patterns enter the
# master through LP-dual pattern cuts; the foil's recourse cost is represented exactly through
# KKT conditions with big-M constants justified by the min-cost-flow structure of the recourse.
using ..XOPT
using JuMP
export Levers, explain_levers, verify_levers, edited_instance, lever_dual_bound

Base.@kwdef struct Levers
    fixed::Bool=true
    unit::Bool=false
    holding::Bool=false
    bound::Float64=.8          # relative bound for continuous cost edits
end

edited_instance(d::Instance,zp,zh)=Instance(d.id,d.family,d.demand,d.capacity,d.fixed,d.unit.+zp,d.holding.+zh,d.retention,d.initial)

# Lemma (min-cost-flow recourse): with nonnegative costs at most cmax, there are optimal duals with
# |pi|,|mu|,|lambda| <= (N-1) cmax and reduced costs <= (3N-2) cmax, N = 1+T+I*T nodes.
function lever_dual_bound(d::Instance,lev::Levers)
    I,T=size(d.demand)
    cmax=max(maximum(d.unit)*(1+(lev.unit ? lev.bound : 0.)),maximum(d.holding)*(1+(lev.holding ? lev.bound : 0.)))
    N=1+T+I*T
    (dual=(N-1)*cmax*1.000001+1e-9,reduced=(3N-2)*cmax*1.000001+1e-9,cmax=cmax,N=N)
end

function lever_master(d,foil,opt,lev,capacity,remaining)
    d.family==:retail || throw(ArgumentError("continuous levers implemented for the retail lot-sizing model"))
    all(d.initial.==0) && d.retention==1. || throw(ArgumentError("retail model with zero initial inventory expected"))
    I,T=size(d.demand);b=XOPT.physical_model(d;capacity=capacity,limit=remaining);m=b.m;y=b.y;q=b.q;s=b.s
    XOPT.add_foil!(m,y,foil)
    F=d.fixed;P0=d.unit;H0=d.holding
    Bf=lev.fixed ? opt.cost_bound.*F : zeros(I,T)
    Bp=lev.unit ? lev.bound.*P0 : zeros(I,T)
    Bh=lev.holding ? lev.bound.*H0 : zeros(I,T);Bh[:,T].=0.   # s_iT = 0, so h_iT is not a lever
    @variable(m,-Bf[i,t]<=delta[i=1:I,t=1:T]<=Bf[i,t])
    @variable(m,-Bp[i,t]<=zp[i=1:I,t=1:T]<=Bp[i,t])
    @variable(m,-Bh[i,t]<=zh[i=1:I,t=1:T]<=Bh[i,t])
    @variable(m,af[1:I,1:T]>=0);@variable(m,ap[1:I,1:T]>=0);@variable(m,ah[1:I,1:T]>=0)
    @constraint(m,[i=1:I,t=1:T],af[i,t]>=delta[i,t]);@constraint(m,[i=1:I,t=1:T],af[i,t]>=-delta[i,t])
    @constraint(m,[i=1:I,t=1:T],ap[i,t]>=zp[i,t]);@constraint(m,[i=1:I,t=1:T],ap[i,t]>=-zp[i,t])
    @constraint(m,[i=1:I,t=1:T],ah[i,t]>=zh[i,t]);@constraint(m,[i=1:I,t=1:T],ah[i,t]>=-zh[i,t])
    @variable(m,uf[1:I,1:T],Bin);@variable(m,up[1:I,1:T],Bin);@variable(m,uh[1:I,1:T],Bin);@variable(m,z[1:T],Bin)
    for (v,u,B) in ((delta,uf,Bf),(zp,up,Bp),(zh,uh,Bh)),i=1:I,t=1:T
        if B[i,t]>0
            @constraint(m,v[i,t]<=B[i,t]*u[i,t]);@constraint(m,v[i,t]>=-B[i,t]*u[i,t]);@constraint(m,u[i,t]<=z[t])
        else;fix(u[i,t],0.;force=true);end
    end
    active=Int.(abs.(capacity.-d.capacity).>opt.tolerance)
    @constraint(m,[t=1:T],z[t]>=active[t])
    @constraint(m,sum(z)<=min(T,opt.k_time))
    @constraint(m,sum(uf)+sum(up)+sum(uh)+sum(active)<=min(3I*T+T,opt.k_param))
    # Exact product w = delta*y for the binary foil pattern.
    @variable(m,w[1:I,1:T])
    @constraint(m,[i=1:I,t=1:T],w[i,t]<=Bf[i,t]*y[i,t]);@constraint(m,[i=1:I,t=1:T],w[i,t]>=-Bf[i,t]*y[i,t])
    @constraint(m,[i=1:I,t=1:T],w[i,t]<=delta[i,t]+Bf[i,t]*(1-y[i,t]));@constraint(m,[i=1:I,t=1:T],w[i,t]>=delta[i,t]-Bf[i,t]*(1-y[i,t]))
    # KKT representation of the foil recourse value q(y;p',h').
    db=lever_dual_bound(d,lev);Th=db.dual;R=db.reduced;smax=sum(capacity)
    @variable(m,-Th<=pi_[1:I,1:T]<=Th);@variable(m,-Th<=mu[1:I,1:T]<=0);@variable(m,-Th<=la[1:T]<=0)
    pp=@expression(m,[i=1:I,t=1:T],P0[i,t]+zp[i,t]);hh=@expression(m,[i=1:I,t=1:T],H0[i,t]+zh[i,t])
    rq=@expression(m,[i=1:I,t=1:T],pp[i,t]-pi_[i,t]-mu[i,t]-la[t])
    rs=@expression(m,[i=1:I,t=1:T-1],hh[i,t]+pi_[i,t]-pi_[i,t+1])
    @constraint(m,[i=1:I,t=1:T],rq[i,t]>=0);@constraint(m,[i=1:I,t=1:T-1],rs[i,t]>=0)
    @variable(m,sq[1:I,1:T],Bin);@variable(m,ss[1:I,1:T-1],Bin);@variable(m,sm[1:I,1:T],Bin);@variable(m,sl[1:T],Bin)
    @constraint(m,[i=1:I,t=1:T],q[i,t]<=capacity[t]*sq[i,t]);@constraint(m,[i=1:I,t=1:T],rq[i,t]<=R*(1-sq[i,t]))
    @constraint(m,[i=1:I,t=1:T-1],s[i,t]<=smax*ss[i,t]);@constraint(m,[i=1:I,t=1:T-1],rs[i,t]<=R*(1-ss[i,t]))
    @constraint(m,[i=1:I,t=1:T],-mu[i,t]<=Th*sm[i,t]);@constraint(m,[i=1:I,t=1:T],capacity[t]*y[i,t]-q[i,t]<=capacity[t]*(1-sm[i,t]))
    @constraint(m,[t=1:T],-la[t]<=Th*sl[t]);@constraint(m,[t=1:T],capacity[t]-sum(q[i,t] for i=1:I)<=capacity[t]*(1-sl[t]))
    @variable(m,-Th<=mm[1:I,1:T]<=0)   # mm = mu*y
    @constraint(m,[i=1:I,t=1:T],mm[i,t]>=-Th*y[i,t]);@constraint(m,[i=1:I,t=1:T],mm[i,t]>=mu[i,t]);@constraint(m,[i=1:I,t=1:T],mm[i,t]<=mu[i,t]+Th*(1-y[i,t]))
    recourse=@expression(m,sum(d.demand[i,t]*pi_[i,t] for i=1:I,t=1:T)+sum(capacity[t]*mm[i,t] for i=1:I,t=1:T)+sum(capacity[t]*la[t] for t=1:T))
    foilcost=@expression(m,sum(F.*y)+sum(w)+recourse)
    @objective(m,Min,sum(af./F)+sum(ap[i,t]/P0[i,t] for i=1:I,t=1:T if Bp[i,t]>0;init=0.)+sum(ah[i,t]/H0[i,t] for i=1:I,t=1:T if Bh[i,t]>0;init=0.)+
        opt.lambda_time*sum(z)+opt.lambda_param*(sum(uf)+sum(up)+sum(uh)+sum(active)))
    (m=m,b=b,delta=delta,zp=zp,zh=zh,foilcost=foilcost,pp=pp,hh=hh,duals=(pi_,mu,la),dualbound=Th)
end

# Pattern dual cut: the competitor's recourse value enters through its LP dual, exact for all edits.
function add_dual_cut!(M,d,ypat,capacity,offset)
    I,T=size(d.demand);m=M.m
    pk=@variable(m,[1:I,1:T]);uk=@variable(m,[1:I,1:T],upper_bound=0.);lk=@variable(m,[1:T],upper_bound=0.)
    @constraint(m,[i=1:I,t=1:T],pk[i,t]+uk[i,t]+lk[t]<=M.pp[i,t])
    @constraint(m,[i=1:I,t=1:T-1],-pk[i,t]+pk[i,t+1]<=M.hh[i,t])
    rhs=@expression(m,sum((d.fixed[i,t]+M.delta[i,t])*ypat[i,t] for i=1:I,t=1:T)+sum(d.demand[i,t]*pk[i,t] for i=1:I,t=1:T)+
        sum(capacity[t]*ypat[i,t]*uk[i,t] for i=1:I,t=1:T)+sum(capacity[t]*lk[t] for t=1:T))
    @constraint(m,M.foilcost<=rhs+offset)
end
# Trajectory cut: the competitor's continuous trajectory is frozen at the oracle's solution.
function add_trajectory_cut!(M,d,r,offset)
    I,T=size(d.demand)
    @constraint(M.m,M.foilcost<=sum((d.fixed[i,t]+M.delta[i,t])*r.y[i,t] for i=1:I,t=1:T)+
        sum(M.pp[i,t]*r.q[i,t] for i=1:I,t=1:T)+sum(M.hh[i,t]*r.state[i,t] for i=1:I,t=1:T)+offset)
end

function explain_levers(d::Instance,foil::Foil;options=Options(),levers=Levers(),cuts=:dual,capacity=d.capacity)
    opt=options;lev=levers;t0=time();remaining()=opt.time_limit-(time()-t0)
    opt.mode in (:weak,:strong) || throw(ArgumentError("mode"))
    cuts in (:dual,:trajectory) || throw(ArgumentError("cuts"))
    I,T=size(d.demand);trace=Any[];ncuts=0;lb=0.
    out(status;k=0,extra=Dict{String,Any}())=merge(Dict{String,Any}("status"=>status,"seconds"=>time()-t0,"iterations"=>k,"cuts"=>ncuts,
        "lower_bound"=>lb,"trace"=>trace),extra)
    remaining()<=0 && return out("TIME_LIMIT")
    M=lever_master(d,foil,opt,lev,capacity,remaining())
    offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    for k in 1:opt.max_iterations
        remaining()<=0 && return out("TIME_LIMIT";k=k)
        set_time_limit_sec(M.m,max(.001,remaining()));optimize!(M.m)
        bnd=objective_bound(M.m);isfinite(bnd) && (lb=max(lb,bnd))
        st=string(termination_status(M.m))
        st=="INFEASIBLE" && return out("SOLVER_INFEASIBLE";k=k)
        st=="OPTIMAL" || return out(st;k=k)
        delta=value.(M.delta);zp=value.(M.zp);zh=value.(M.zh);fc=value(M.foilcost);obj=objective_value(M.m)
        de=edited_instance(d,zp,zh)
        r=forward(de;cost=d.fixed.+delta,capacity=capacity,foil=opt.mode==:strong ? foil : nothing,complement=opt.mode==:strong,limit=remaining())
        push!(trace,Dict("iteration"=>k,"master"=>obj,"lower_bound"=>lb,"oracle_status"=>r.status,"oracle_bound"=>isfinite(r.bound) ? r.bound : nothing,
            "foil_cost"=>fc,"seconds"=>time()-t0,"cuts"=>ncuts))
        if (r.status=="INFEASIBLE" && opt.mode==:strong) || (r.status=="OPTIMAL" && XOPT.numerical_acceptance(fc,r.bound,offset,opt.tolerance))
            pi_,mu,la=M.duals;Th=M.dualbound;yv=value.(M.b.y)
            # Diagnostic only: a dual variable that matters for the foil cost sits at its bound.
            relevant=vcat(vec(value.(pi_)),[value(mu[j]) for j in eachindex(mu) if yv[j]>.5],value.(la))
            hit=!isempty(relevant) && maximum(abs.(relevant))>=Th*(1-1e-6)
            changed=(abs.(delta).>opt.tolerance).|(abs.(zp).>opt.tolerance).|(abs.(zh).>opt.tolerance)
            act=abs.(capacity.-d.capacity).>opt.tolerance
            return out("SOLVER_VALIDATED";k=k,extra=Dict{String,Any}("objective"=>obj,"delta"=>delta,"zp"=>zp,"zh"=>zh,
                "y"=>round.(value.(M.b.y)),"q"=>value.(M.b.q),"state"=>value.(M.b.s),"foil_cost"=>fc,"dual_bound_active"=>hit,
                "changed_periods"=>sum(vec(any(changed,dims=1)).|act),
                "changed_fixed"=>sum(abs.(delta).>opt.tolerance),"changed_unit"=>sum(abs.(zp).>opt.tolerance),"changed_holding"=>sum(abs.(zh).>opt.tolerance)))
        end
        r.status=="OPTIMAL" || return out(r.status;k=k)
        fc-r.objective<=offset+opt.tolerance && return out("NUMERICAL_UNRESOLVED";k=k)
        cuts==:dual ? add_dual_cut!(M,d,r.y,capacity,offset) : add_trajectory_cut!(M,d,r,offset);ncuts+=1
    end
    out("ITERATION_LIMIT";k=opt.max_iterations)
end

# Fresh validation: witness feasibility, edit bounds, supports, KKT consistency and a fresh oracle.
function verify_levers(d,foil,r;options=Options(),levers=Levers(),capacity=d.capacity)
    r["status"]=="SOLVER_VALIDATED" || return Dict{String,Any}("valid"=>false,"reason"=>"not validated")
    opt=options;lev=levers;tol=1e-5;I,T=size(d.demand)
    rs=XOPT.Result(status="SOLVER_VALIDATED",delta=r["delta"],y=r["y"],q=r["q"],state=r["state"])
    de=edited_instance(d,r["zp"],r["zh"])
    v=XOPT.verify(de,foil,rs;options=opt,capacity=capacity)
    zp,zh=r["zp"],r["zh"]
    bounds=maximum(abs.(zp).-(lev.unit ? lev.bound : 0.).*d.unit)<=tol && maximum(abs.(zh).-(lev.holding ? lev.bound : 0.).*d.holding)<=tol &&
        maximum(abs.(zh[:,T]))<=tol && (lev.fixed || maximum(abs.(r["delta"]))<=tol)
    changed=(abs.(r["delta"]).>opt.tolerance).|(abs.(zp).>opt.tolerance).|(abs.(zh).>opt.tolerance)
    support=sum(vec(any(changed,dims=1)))<=opt.k_time && sum(changed)<=opt.k_param
    witness=v["witness_cost"]
    v["kkt_gap"]=abs(witness-r["foil_cost"])
    v["lever_bounds"]=bounds;v["lever_support"]=support
    v["valid"]=v["valid"] && bounds && support && v["kkt_gap"]<=1e-4*max(1,abs(witness))
    v
end
end
