module UCX
# Counterfactual explanations for single-bus unit commitment built from PGLib-UC (RTS-GMLC) data.
# The binary pattern is the commitment u (startups v and shutdowns w are determined by u), and the
# recourse is the economic dispatch above minimum output. Activation levers edit hourly no-load
# costs, recourse levers shift the marginal cost of every dispatch segment of a unit in an hour.
# With recourse levers the dispatch must stay a network flow, so ramping is switched off.
using ..XOPT
using JuMP, HiGHS, JSON3
const MOI=JuMP.MOI
export UCInstance, UCLevers, load_uc, uc_forward, uc_explain, uc_verify, uc_vertices, uc_explain_by_enumeration, uc_meta, uc_restore

struct UCInstance
    id::String
    names::Vector{String}
    demand::Vector{Float64}      # scaled load minus the renewable output that cannot be curtailed
    reserve::Vector{Float64}
    renew::Vector{Float64}       # scaled curtailable renewable output, free of charge
    pmin::Vector{Float64}
    pmax::Vector{Float64}
    noload::Vector{Float64}      # cost of running at minimum output for one hour
    startup::Vector{Float64}     # hot-start cost
    width::Vector{Vector{Float64}}
    marginal::Vector{Vector{Float64}}
    ramp_up::Vector{Float64}
    ramp_down::Vector{Float64}
    su::Vector{Float64}
    sd::Vector{Float64}
    min_up::Vector{Int}
    min_down::Vector{Int}
    u0::Vector{Int}
    p0::Vector{Float64}
    up0::Vector{Int}
    down0::Vector{Int}
    ramps::Bool
end
Base.@kwdef struct UCLevers
    noload::Bool=true
    marginal::Bool=false
    bound::Float64=.8
end
G_(d)=length(d.pmin);T_(d)=length(d.demand);K_(d,g)=length(d.width[g])
mref(d)=[minimum(d.marginal[g]) for g in 1:G_(d)]

# Build a reduced instance: units are taken by name and the horizon starts at hour `start`. The
# system is scaled so that the peak net load (demand minus available renewable output) equals
# `alpha` times the capacity of the selected units. Demand, renewables and reserves share the factor.
# With secant=true each production curve above minimum output is replaced by one segment of the
# same total cost (used only for the tiny enumeration cases).
function load_uc(file,units;T=24,start=1,alpha=.8,ramps=true,id="",secant=false)
    j=JSON3.read(read(file,String));th=j.thermal_generators;rn=j.renewable_generators
    hours=start:start+T-1
    rmax=[sum(Float64(g.power_output_maximum[t]) for (_,g) in rn) for t in 1:j.time_periods]
    rmin=[sum(Float64(g.power_output_minimum[t]) for (_,g) in rn) for t in 1:j.time_periods]
    net=j.demand.-rmax
    gs=[th[Symbol(n)] for n in units]
    pmax=[Float64(g.power_output_maximum) for g in gs]
    scale=alpha*sum(pmax)/maximum(net[hours])
    width=Vector{Vector{Float64}}();marg=Vector{Vector{Float64}}()
    for g in gs
        pw=g.piecewise_production
        if secant
            push!(width,[Float64(pw[end].mw-pw[1].mw)]);push!(marg,[Float64((pw[end].cost-pw[1].cost)/(pw[end].mw-pw[1].mw))])
        else
            push!(width,[Float64(pw[k+1].mw-pw[k].mw) for k in 1:length(pw)-1])
            push!(marg,[Float64((pw[k+1].cost-pw[k].cost)/(pw[k+1].mw-pw[k].mw)) for k in 1:length(pw)-1])
        end
        all(diff(marg[end]).>=-1e-9) || error("nonconvex production cost for $(g.name)")
    end
    UCInstance(isempty(id) ? basename(file) : id,String.(units),scale.*(j.demand[hours].-rmin[hours]),scale.*Float64.(j.reserves[hours]),
        scale.*(rmax[hours].-rmin[hours]),
        [Float64(g.power_output_minimum) for g in gs],pmax,[Float64(g.piecewise_production[1].cost) for g in gs],
        [Float64(g.startup[1].cost) for g in gs],width,marg,
        [Float64(g.ramp_up_limit) for g in gs],[Float64(g.ramp_down_limit) for g in gs],
        [Float64(g.ramp_startup_limit) for g in gs],[Float64(g.ramp_shutdown_limit) for g in gs],
        [Int(g.time_up_minimum) for g in gs],[Int(g.time_down_minimum) for g in gs],
        [Int(g.unit_on_t0) for g in gs],[Float64(g.power_output_t0) for g in gs],
        [Int(g.time_up_t0) for g in gs],[Int(g.time_down_t0) for g in gs],ramps)
end
uc_meta(d::UCInstance)=Dict(string(k)=>getfield(d,k) for k in fieldnames(UCInstance))
function uc_restore(m)
    v(x)=Float64.(collect(x));vi(x)=Int.(collect(x));vv(x)=[Float64.(collect(y)) for y in x]
    UCInstance(String(m.id),String.(collect(m.names)),v(m.demand),v(m.reserve),v(m.renew),v(m.pmin),v(m.pmax),v(m.noload),v(m.startup),
        vv(m.width),vv(m.marginal),v(m.ramp_up),v(m.ramp_down),v(m.su),v(m.sd),vi(m.min_up),vi(m.min_down),vi(m.u0),v(m.p0),vi(m.up0),vi(m.down0),Bool(m.ramps))
end
with_ramps(d::UCInstance,r::Bool)=UCInstance((getfield(d,k) for k in fieldnames(UCInstance)[1:end-1])...,r)

# Startups and shutdowns implied by a commitment pattern.
function transitions(d,u)
    G,T=size(u);v=zeros(G,T);w=zeros(G,T)
    for g=1:G,t=1:T
        prev=t==1 ? d.u0[g] : u[g,t-1];v[g,t]=max(0,u[g,t]-prev);w[g,t]=max(0,prev-u[g,t])
    end
    v,w
end
residual(d,u)=[d.demand[t]-sum(d.pmin[g]*u[g,t] for g in 1:G_(d)) for t in 1:T_(d)]
# Combinatorial feasibility of a commitment for the network dispatch (no ramps): initial states,
# minimum up and down times, reserve cover and minimum output below the load.
function pattern_feasible(d,u)
    G,T=size(u);v,w=transitions(d,u)
    for g=1:G
        if d.u0[g]==1;any(u[g,t]<.5 for t in 1:min(T,d.min_up[g]-d.up0[g])) && return false
        else;any(u[g,t]>.5 for t in 1:min(T,d.min_down[g]-d.down0[g])) && return false;end
        for t=1:T
            sum(v[g,s] for s in max(1,t-d.min_up[g]+1):t)<=u[g,t] || return false
            sum(w[g,s] for s in max(1,t-d.min_down[g]+1):t)<=1-u[g,t] || return false
        end
    end
    all(sum(d.pmax[g]*u[g,t] for g=1:G)+d.renew[t]>=d.demand[t]+d.reserve[t]-1e-9 && sum(d.pmin[g]*u[g,t] for g=1:G)<=d.demand[t]+1e-9 for t=1:T)
end

function uc_physical(d::UCInstance;limit=120.)
    G,T=G_(d),T_(d);m=XOPT.optimizer_model(limit)
    @variable(m,u[1:G,1:T],Bin);@variable(m,v[1:G,1:T],Bin);@variable(m,w[1:G,1:T],Bin)
    p=[@variable(m,[1:K_(d,g),1:T],lower_bound=0.) for g in 1:G]
    for g=1:G,t=1:T
        prev=t==1 ? d.u0[g] : u[g,t-1]
        @constraint(m,v[g,t]-w[g,t]==u[g,t]-prev);@constraint(m,v[g,t]+w[g,t]<=1)
        @constraint(m,sum(v[g,s] for s in max(1,t-d.min_up[g]+1):t)<=u[g,t])
        @constraint(m,sum(w[g,s] for s in max(1,t-d.min_down[g]+1):t)<=1-u[g,t])
        for k=1:K_(d,g);@constraint(m,p[g][k,t]<=d.width[g][k]*u[g,t]);end
    end
    for g=1:G
        if d.u0[g]==1;for t in 1:min(T,d.min_up[g]-d.up0[g]);fix(u[g,t],1.;force=true);end
        else;for t in 1:min(T,d.min_down[g]-d.down0[g]);fix(u[g,t],0.;force=true);end;end
    end
    @variable(m,0<=rr[t=1:T]<=d.renew[t])
    @constraint(m,[t=1:T],sum(d.pmax[g]*u[g,t] for g=1:G)+d.renew[t]>=d.demand[t]+d.reserve[t])
    @constraint(m,[t=1:T],sum(d.pmin[g]*u[g,t] for g=1:G)<=d.demand[t])
    @constraint(m,bal[t=1:T],sum(p[g][k,t] for g=1:G for k=1:K_(d,g))+rr[t]==d.demand[t]-sum(d.pmin[g]*u[g,t] for g=1:G))
    if d.ramps
        P=@expression(m,[g=1:G,t=1:T],d.pmin[g]*u[g,t]+sum(p[g][k,t] for k=1:K_(d,g)))
        # Initial outputs belong to the full system and are left free, so ramps start at hour 2.
        for g=1:G,t=2:T
            @constraint(m,P[g,t]-P[g,t-1]<=d.ramp_up[g]*u[g,t-1]+d.su[g]*v[g,t])
            @constraint(m,P[g,t-1]-P[g,t]<=d.ramp_down[g]*u[g,t]+d.sd[g]*w[g,t])
        end
    end
    (m=m,u=u,v=v,w=w,p=p,rr=rr)
end
add_uc_foil!(m,u,foil;complement=false)=XOPT.add_foil!(m,u,foil;complement=complement)
dispatch_cost(d,p,shift)=sum((d.marginal[g][k]+shift[g,t])*p[g][k,t] for g=1:G_(d) for k=1:K_(d,g) for t=1:T_(d))

function uc_forward(d::UCInstance;delta=zeros(G_(d),T_(d)),zeta=zeros(G_(d),T_(d)),foil=nothing,complement=false,pattern=nothing,limit=120.)
    limit<=0 && return (status="TIME_LIMIT",objective=Inf,bound=-Inf,u=zeros(0,0),p=nothing,recourse=Inf)
    b=uc_physical(d;limit=limit);m=b.m;G,T=G_(d),T_(d)
    !isnothing(foil) && add_uc_foil!(m,b.u,foil;complement=complement)
    if !isnothing(pattern);for j in eachindex(b.u);fix(b.u[j],pattern[j];force=true);end;end
    rec=@expression(m,sum((d.marginal[g][k]+zeta[g,t])*b.p[g][k,t] for g=1:G for k=1:K_(d,g) for t=1:T))
    @objective(m,Min,sum((d.noload[g]+delta[g,t])*b.u[g,t] for g=1:G,t=1:T)+sum(d.startup[g]*b.v[g,t] for g=1:G,t=1:T)+rec)
    optimize!(m);st=string(termination_status(m));ok=has_values(m)
    (status=st,objective=ok ? objective_value(m) : Inf,bound=st=="INFEASIBLE" ? Inf : objective_bound(m),
     u=ok ? round.(value.(b.u)) : zeros(0,0),p=ok ? [value.(b.p[g]) for g in 1:G] : nothing,r=ok ? value.(b.rr) : nothing,recourse=ok ? value(rec) : Inf)
end

# Dual bounds for the single-bus dispatch: by the merit-order argument there are optimal duals with
# price in [0, cbar] and capacity multipliers in [-cbar, 0], so reduced costs lie in [0, 2 cbar].
function uc_dual_bound(d,lev)
    cbar=maximum(maximum(m) for m in d.marginal)+(lev.marginal ? lev.bound*maximum(mref(d)) : 0.)
    (price=cbar*1.000001+1e-9,reduced=2cbar*1.000001+1e-9,cbar=cbar)
end

function uc_master(d,foil,opt,lev,remaining)
    G,T=G_(d),T_(d);b=uc_physical(d;limit=remaining);m=b.m;u=b.u;p=b.p
    lev.marginal && d.ramps && throw(ArgumentError("recourse-cost levers require the network dispatch without ramps"))
    add_uc_foil!(m,u,foil)
    Bf=lev.noload ? opt.cost_bound.*repeat(d.noload,1,T) : zeros(G,T)
    Bm=lev.marginal ? lev.bound.*repeat(mref(d),1,T) : zeros(G,T)
    @variable(m,-Bf[g,t]<=delta[g=1:G,t=1:T]<=Bf[g,t]);@variable(m,-Bm[g,t]<=zeta[g=1:G,t=1:T]<=Bm[g,t])
    @variable(m,af[1:G,1:T]>=0);@variable(m,am[1:G,1:T]>=0)
    @constraint(m,af.>=delta);@constraint(m,af.>=-delta);@constraint(m,am.>=zeta);@constraint(m,am.>=-zeta)
    @variable(m,uf[1:G,1:T],Bin);@variable(m,um[1:G,1:T],Bin);@variable(m,z[1:T],Bin)
    for (x,s,B) in ((delta,uf,Bf),(zeta,um,Bm)),g=1:G,t=1:T
        if B[g,t]>0;@constraint(m,x[g,t]<=B[g,t]*s[g,t]);@constraint(m,x[g,t]>=-B[g,t]*s[g,t]);@constraint(m,s[g,t]<=z[t])
        else;fix(s[g,t],0.;force=true);end
    end
    @constraint(m,sum(z)<=min(T,opt.k_time));@constraint(m,sum(uf)+sum(um)<=min(2G*T,opt.k_param))
    @variable(m,wd[1:G,1:T])   # delta*u, exact for binary u
    @constraint(m,[g=1:G,t=1:T],wd[g,t]<=Bf[g,t]*u[g,t]);@constraint(m,[g=1:G,t=1:T],wd[g,t]>=-Bf[g,t]*u[g,t])
    @constraint(m,[g=1:G,t=1:T],wd[g,t]<=delta[g,t]+Bf[g,t]*(1-u[g,t]));@constraint(m,[g=1:G,t=1:T],wd[g,t]>=delta[g,t]-Bf[g,t]*(1-u[g,t]))
    activation=@expression(m,sum(d.noload[g]*u[g,t] for g=1:G,t=1:T)+sum(wd)+sum(d.startup[g]*b.v[g,t] for g=1:G,t=1:T))
    duals=nothing
    if lev.marginal
        db=uc_dual_bound(d,lev);Th=db.price;R=db.reduced
        @variable(m,0<=la[1:T]<=Th);mu=[@variable(m,[1:K_(d,g),1:T],lower_bound=-Th,upper_bound=0.) for g in 1:G]
        sp=[@variable(m,[1:K_(d,g),1:T],Bin) for g in 1:G];sm=[@variable(m,[1:K_(d,g),1:T],Bin) for g in 1:G]
        mm=[@variable(m,[1:K_(d,g),1:T],lower_bound=-Th,upper_bound=0.) for g in 1:G]   # mu*u
        @variable(m,0<=ll[1:G,1:T]<=Th)                                                   # la*u
        for g=1:G,k=1:K_(d,g),t=1:T
            W=d.width[g][k];rc=@expression(m,d.marginal[g][k]+zeta[g,t]-la[t]-mu[g][k,t])
            @constraint(m,rc>=0);@constraint(m,rc<=R*(1-sp[g][k,t]));@constraint(m,p[g][k,t]<=W*sp[g][k,t])
            @constraint(m,-mu[g][k,t]<=Th*sm[g][k,t]);@constraint(m,W*u[g,t]-p[g][k,t]<=W*(1-sm[g][k,t]))
            @constraint(m,mm[g][k,t]>=-Th*u[g,t]);@constraint(m,mm[g][k,t]>=mu[g][k,t]);@constraint(m,mm[g][k,t]<=mu[g][k,t]+Th*(1-u[g,t]))
        end
        @constraint(m,[g=1:G,t=1:T],ll[g,t]<=Th*u[g,t]);@constraint(m,[g=1:G,t=1:T],ll[g,t]<=la[t])
        @constraint(m,[g=1:G,t=1:T],ll[g,t]>=la[t]-Th*(1-u[g,t]))
        # Curtailable renewables: a free arc of capacity renew[t].
        @variable(m,-Th<=nu[1:T]<=0);@variable(m,sr[1:T],Bin);@variable(m,sn[1:T],Bin)
        for t=1:T
            rcr=@expression(m,-la[t]-nu[t]);RN=d.renew[t]
            @constraint(m,rcr>=0);@constraint(m,rcr<=R*(1-sr[t]));@constraint(m,b.rr[t]<=RN*sr[t])
            @constraint(m,-nu[t]<=Th*sn[t]);@constraint(m,RN-b.rr[t]<=RN*(1-sn[t]))
        end
        recourse=@expression(m,sum(la[t]*d.demand[t] for t=1:T)-sum(d.pmin[g]*ll[g,t] for g=1:G,t=1:T)+
            sum(d.width[g][k]*mm[g][k,t] for g=1:G for k=1:K_(d,g) for t=1:T)+sum(d.renew[t]*nu[t] for t=1:T))
        duals=(la=la,mu=mu,bound=Th)
    else
        recourse=@expression(m,sum(d.marginal[g][k]*p[g][k,t] for g=1:G for k=1:K_(d,g) for t=1:T))
    end
    foilcost=@expression(m,activation+recourse)
    nl=d.noload;mr=mref(d)
    @objective(m,Min,sum(af[g,t]/nl[g] for g=1:G,t=1:T)+sum(am[g,t]/mr[g] for g=1:G,t=1:T)+opt.lambda_time*sum(z)+opt.lambda_param*(sum(uf)+sum(um)))
    (m=m,b=b,delta=delta,zeta=zeta,foilcost=foilcost,duals=duals)
end
function competitor_activation(M,d,uk)
    vk,_=transitions(d,uk)
    @expression(M.m,sum((d.noload[g]+M.delta[g,t])*uk[g,t]+d.startup[g]*vk[g,t] for g=1:G_(d),t=1:T_(d)))
end
# Pattern dual cut: exact for every marginal-cost edit, one cut per competitor pattern.
function uc_dual_cut!(M,d,uk,offset)
    G,T=G_(d),T_(d);m=M.m;r=residual(d,uk)
    lk=@variable(m,[1:T]);mk=[@variable(m,[1:K_(d,g),1:T],upper_bound=0.) for g in 1:G]
    nk=@variable(m,[1:T],upper_bound=0.)
    for g=1:G,k=1:K_(d,g),t=1:T;@constraint(m,lk[t]+mk[g][k,t]<=d.marginal[g][k]+M.zeta[g,t]);end
    @constraint(m,[t=1:T],lk[t]+nk[t]<=0.)
    rhs=@expression(m,competitor_activation(M,d,uk)+sum(lk[t]*r[t] for t=1:T)+sum(d.width[g][k]*uk[g,t]*mk[g][k,t] for g=1:G for k=1:K_(d,g) for t=1:T)+
        sum(d.renew[t]*nk[t] for t=1:T))
    @constraint(m,M.foilcost<=rhs+offset)
end
uc_value_cut!(M,d,uk,q,offset)=@constraint(M.m,M.foilcost<=competitor_activation(M,d,uk)+q+offset)
function uc_trajectory_cut!(M,d,uk,pk,offset)
    @constraint(M.m,M.foilcost<=competitor_activation(M,d,uk)+sum((d.marginal[g][k]+M.zeta[g,t])*pk[g][k,t] for g=1:G_(d) for k=1:K_(d,g) for t=1:T_(d))+offset)
end

function uc_explain(d::UCInstance,foil::Foil;options=Options(),levers=UCLevers(),cuts=:dual)
    opt=options;lev=levers;t0=time();remaining()=opt.time_limit-(time()-t0)
    opt.mode in (:weak,:strong) || throw(ArgumentError("mode"));cuts in (:dual,:trajectory) || throw(ArgumentError("cuts"))
    trace=Any[];ncuts=0;lb=0.
    out(status;k=0,extra=Dict{String,Any}())=merge(Dict{String,Any}("status"=>status,"seconds"=>time()-t0,"iterations"=>k,"cuts"=>ncuts,"lower_bound"=>lb,"trace"=>trace),extra)
    remaining()<=0 && return out("TIME_LIMIT")
    M=uc_master(d,foil,opt,lev,remaining());offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    for k in 1:opt.max_iterations
        remaining()<=0 && return out("TIME_LIMIT";k=k)
        set_time_limit_sec(M.m,max(.001,remaining()));optimize!(M.m)
        bnd=objective_bound(M.m);isfinite(bnd) && (lb=max(lb,bnd))
        st=string(termination_status(M.m))
        st=="INFEASIBLE" && return out("SOLVER_INFEASIBLE";k=k)
        st=="OPTIMAL" || return out(st;k=k)
        delta=value.(M.delta);zeta=value.(M.zeta);fc=value(M.foilcost);obj=objective_value(M.m)
        r=uc_forward(d;delta=delta,zeta=zeta,foil=opt.mode==:strong ? foil : nothing,complement=opt.mode==:strong,limit=remaining())
        push!(trace,Dict("iteration"=>k,"master"=>obj,"lower_bound"=>lb,"oracle_status"=>r.status,"oracle_bound"=>isfinite(r.bound) ? r.bound : nothing,"foil_cost"=>fc,"seconds"=>time()-t0,"cuts"=>ncuts))
        if (r.status=="INFEASIBLE" && opt.mode==:strong) || (r.status=="OPTIMAL" && XOPT.numerical_acceptance(fc,r.bound,offset,opt.tolerance))
            u=round.(value.(M.b.u));pv=[value.(M.b.p[g]) for g in 1:G_(d)];rv=value.(M.b.rr)
            hit=false
            if !isnothing(M.duals)
                rel=vcat(value.(M.duals.la),[value(M.duals.mu[g][k,t]) for g in 1:G_(d) for k in 1:K_(d,g) for t in 1:T_(d) if u[g,t]>.5])
                hit=!isempty(rel) && maximum(abs.(rel))>=M.duals.bound*(1-1e-6)
            end
            changed=(abs.(delta).>opt.tolerance).|(abs.(zeta).>opt.tolerance)
            return out("SOLVER_VALIDATED";k=k,extra=Dict{String,Any}("objective"=>obj,"delta"=>delta,"zeta"=>zeta,"u"=>u,"p"=>pv,"r"=>rv,"foil_cost"=>fc,
                "dual_bound_active"=>hit,"changed_periods"=>sum(vec(any(changed,dims=1))),"changed_noload"=>sum(abs.(delta).>opt.tolerance),
                "changed_marginal"=>sum(abs.(zeta).>opt.tolerance)))
        end
        r.status=="OPTIMAL" || return out(r.status;k=k)
        fc-r.objective<=offset+opt.tolerance && return out("NUMERICAL_UNRESOLVED";k=k)
        if !lev.marginal;uc_value_cut!(M,d,r.u,r.recourse,offset)
        elseif cuts==:dual;uc_dual_cut!(M,d,r.u,offset)
        else;uc_trajectory_cut!(M,d,r.u,r.p,offset);end
        ncuts+=1
    end
    out("ITERATION_LIMIT";k=opt.max_iterations)
end

# Fresh validation: physical feasibility of the witness, edit bounds and supports, the stored foil
# cost against a direct recomputation, and a fresh oracle at the edited costs.
function uc_verify(d::UCInstance,foil::Foil,r;options=Options(),levers=UCLevers())
    r["status"]=="SOLVER_VALIDATED" || return Dict{String,Any}("valid"=>false,"reason"=>"not validated")
    opt=options;lev=levers;tol=1e-5;G,T=G_(d),T_(d);u=r["u"];p=r["p"];rv=r["r"];delta=r["delta"];zeta=r["zeta"]
    chk=uc_forward(d;pattern=u,limit=opt.time_limit)   # pattern-level feasibility of u (min up/down, ramps, reserve)
    v,_=transitions(d,u)
    bal=maximum(abs(sum(p[g][k,t] for g=1:G for k=1:K_(d,g))+rv[t]-residual(d,u)[t]) for t=1:T)
    caps=maximum(p[g][k,t]-d.width[g][k]*u[g,t] for g=1:G for k=1:K_(d,g) for t=1:T)
    physical=chk.status=="OPTIMAL" && bal<=tol && caps<=tol && minimum(minimum(x) for x in p)>=-tol && XOPT.matches(u,foil) && all(-tol.<=rv.<=d.renew.+tol)
    if d.ramps
        P=[d.pmin[g]*u[g,t]+sum(p[g][k,t] for k=1:K_(d,g)) for g=1:G,t=1:T]
        _,w=transitions(d,u)
        for g=1:G,t=2:T
            physical&=P[g,t]-P[g,t-1]<=d.ramp_up[g]*u[g,t-1]+d.su[g]*v[g,t]+tol && P[g,t-1]-P[g,t]<=d.ramp_down[g]*u[g,t]+d.sd[g]*w[g,t]+tol
        end
    end
    Bf=lev.noload ? opt.cost_bound.*repeat(d.noload,1,T) : zeros(G,T);Bm=lev.marginal ? lev.bound.*repeat(mref(d),1,T) : zeros(G,T)
    changed=(abs.(delta).>opt.tolerance).|(abs.(zeta).>opt.tolerance)
    actionable=maximum(abs.(delta).-Bf)<=tol && maximum(abs.(zeta).-Bm)<=tol && sum(vec(any(changed,dims=1)))<=opt.k_time && sum(changed)<=opt.k_param
    witness=sum((d.noload[g]+delta[g,t])*u[g,t]+d.startup[g]*v[g,t] for g=1:G,t=1:T)+dispatch_cost(d,p,zeta)
    z=uc_forward(d;delta=delta,zeta=zeta,foil=opt.mode==:strong ? foil : nothing,complement=opt.mode==:strong,limit=opt.time_limit)
    offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    ok=(z.status=="INFEASIBLE" && opt.mode==:strong)||(z.status=="OPTIMAL" && XOPT.numerical_acceptance(witness,z.bound,offset,tol))
    kkt=abs(witness-r["foil_cost"])
    Dict{String,Any}("valid"=>physical&&actionable&&ok&&kkt<=1e-6*max(1,abs(witness)),"physical"=>physical,"actionable"=>actionable,"balance_residual"=>bal,
        "oracle_status"=>z.status,"witness_cost"=>witness,"oracle_bound"=>isfinite(z.bound) ? z.bound : nothing,"kkt_gap"=>kkt,
        "gap"=>isfinite(z.bound) ? witness-z.bound : nothing)
end

# ---------------- Independent reference for tiny instances (no LP duality, no KKT) ----------------
# Vertices of the hourly dispatch polytope {0 <= x <= width*u, sum x = r}: every segment at a bound
# except at most one.
function uc_vertices(d,col,r;renew=0.,tol=1e-9)
    segs=[(g,k) for g in 1:G_(d) if col[g]>.5 for k in 1:K_(d,g)];renew>tol && push!(segs,(0,0));n=length(segs)
    W=[g==0 ? renew : d.width[g][k] for (g,k) in segs]
    out=Vector{Vector{Float64}}()
    for mask in 0:(2^n-1)
        x=[(mask>>(j-1))&1==1 ? W[j] : 0. for j in 1:n];s=sum(x;init=0.)
        cands=abs(s-r)<=tol ? [x] : Vector{Vector{Float64}}()
        for j in 1:n
            x[j]==0. || continue;rest=r-s
            if rest>tol && rest<W[j]-tol;y=copy(x);y[j]=rest;push!(cands,y);end
        end
        for c in cands;any(v->maximum(abs.(v.-c);init=0.)<=1e-7,out) || push!(out,c);end
    end
    # The renewable component carries no cost and is dropped from the returned dispatch.
    full=[begin z=[zeros(K_(d,g)) for g in 1:G_(d)];for (j,(g,k)) in enumerate(segs);g>0 && (z[g][k]=x[j]);end;z end for x in out]
    full
end
function uc_explain_by_enumeration(d::UCInstance,foil::Foil;options=Options(),levers=UCLevers())
    d.ramps && throw(ArgumentError("enumeration reference assumes the network dispatch"))
    opt=options;lev=levers;G,T=G_(d),T_(d);G*T<=12 || throw(ArgumentError("too many binaries"))
    pats=Matrix{Float64}[]
    for mask in 0:(2^(G*T)-1)
        u=reshape(Float64.([(mask>>(j-1))&1 for j in 1:G*T]),G,T)
        pattern_feasible(d,u) && push!(pats,u)
    end
    V=Dict{Tuple{Int,Vector{Float64}},Vector{Vector{Vector{Float64}}}}()
    vert(t,col)=get!(()->uc_vertices(d,col,d.demand[t]-sum(d.pmin[g]*col[g] for g in 1:G);renew=d.renew[t]),V,(t,col))
    offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    comps=[u for u in pats if !(opt.mode==:strong && XOPT.matches(u,foil))]
    Bf=lev.noload ? opt.cost_bound.*repeat(d.noload,1,T) : zeros(G,T);Bm=lev.marginal ? lev.bound.*repeat(mref(d),1,T) : zeros(G,T)
    nl=d.noload;mr=mref(d);best=Inf;arg=nothing
    for uh in pats
        XOPT.matches(uh,foil) || continue
        m=Model(HiGHS.Optimizer);set_silent(m);set_optimizer_attribute(m,"mip_rel_gap",0.);set_optimizer_attribute(m,"threads",1)
        @variable(m,-Bf[g,t]<=de[g=1:G,t=1:T]<=Bf[g,t]);@variable(m,-Bm[g,t]<=ze[g=1:G,t=1:T]<=Bm[g,t])
        @variable(m,a1[1:G,1:T]>=0);@variable(m,a2[1:G,1:T]>=0)
        @constraint(m,a1.>=de);@constraint(m,a1.>=-de);@constraint(m,a2.>=ze);@constraint(m,a2.>=-ze)
        @variable(m,s[1:2,1:G,1:T],Bin);@variable(m,z[1:T],Bin)
        for (k,(x,B)) in enumerate(((de,Bf),(ze,Bm))),g=1:G,t=1:T
            @constraint(m,x[g,t]<=B[g,t]*s[k,g,t]);@constraint(m,x[g,t]>=-B[g,t]*s[k,g,t]);@constraint(m,s[k,g,t]<=z[t])
        end
        @constraint(m,sum(z)<=min(T,opt.k_time));@constraint(m,sum(s)<=min(2G*T,opt.k_param))
        # Foil witness: one dispatch vertex per hour, selected by binaries; products are exact.
        hourly=Any[]
        for t=1:T
            vs=vert(t,uh[:,t]);isempty(vs) && (hourly=nothing;break)
            b=@variable(m,[1:length(vs)],Bin);@constraint(m,sum(b)==1)
            U=sum(Bm[g,t]*sum(x[g]) for x in vs for g in 1:G;init=0.)+1.
            e=@variable(m,[1:length(vs)])
            for (j,x) in enumerate(vs)
                ex=@expression(m,sum(ze[g,t]*sum(x[g]) for g in 1:G))
                @constraint(m,e[j]<=U*b[j]);@constraint(m,e[j]>=-U*b[j]);@constraint(m,e[j]<=ex+U*(1-b[j]));@constraint(m,e[j]>=ex-U*(1-b[j]))
            end
            push!(hourly,@expression(m,sum(b[j]*sum(d.marginal[g][k]*vs[j][g][k] for g in 1:G for k in 1:K_(d,g)) for j in eachindex(vs))+sum(e)))
        end
        isnothing(hourly) && continue
        vh,_=transitions(d,uh)
        fcost=@expression(m,sum((nl[g]+de[g,t])*uh[g,t]+d.startup[g]*vh[g,t] for g=1:G,t=1:T)+sum(hourly))
        # Competitors: the hourly epigraph theta(t,col) <= cost of every vertex is exact for the minimum.
        th=Dict{Tuple{Int,Vector{Float64}},VariableRef}()
        theta(t,col)=get!(th,(t,col)) do
            v=@variable(m)
            for x in vert(t,col);@constraint(m,v<=sum((d.marginal[g][k]+ze[g,t])*x[g][k] for g in 1:G for k in 1:K_(d,g)));end
            v
        end
        for uk in comps
            vk,_=transitions(d,uk)
            @constraint(m,fcost<=sum((nl[g]+de[g,t])*uk[g,t]+d.startup[g]*vk[g,t] for g=1:G,t=1:T)+sum(theta(t,uk[:,t]) for t=1:T)+offset)
        end
        @objective(m,Min,sum(a1[g,t]/nl[g] for g=1:G,t=1:T)+sum(a2[g,t]/mr[g] for g=1:G,t=1:T)+opt.lambda_time*sum(z)+opt.lambda_param*sum(s))
        optimize!(m)
        if termination_status(m)==MOI.OPTIMAL && objective_value(m)<best;best=objective_value(m);arg=(uh,value.(de),value.(ze));end
    end
    Dict{String,Any}("status"=>isfinite(best) ? "OPTIMAL" : "INFEASIBLE","objective"=>isfinite(best) ? best : nothing,"patterns"=>length(pats),
        "competitors"=>length(comps),"argmin"=>arg)
end
end
