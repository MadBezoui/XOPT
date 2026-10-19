# Cycle 4: fixed-witness constraint generation. The foil witness (pattern and dispatch) is fixed,
# so the master is linear in the edits apart from support binaries; competitors enter through exact
# dual cuts. Every returned explanation is valid; optimality is only within the fixed witness.
using JuMP
const MOI=JuMP.MOI
function fw_master(d,ŷ,x̂,opt,lev,limit)
    G,T=UCX2.G_(d),UCX2.T_(d);m=XOPT.optimizer_model(limit)
    Bf=lev.noload ? opt.cost_bound.*repeat(d.noload,1,T) : zeros(G,T);Bm=lev.marginal ? lev.bound.*repeat(UCX2.mref(d),1,T) : zeros(G,T)
    @variable(m,-Bf[g,t]<=delta[g=1:G,t=1:T]<=Bf[g,t]);@variable(m,-Bm[g,t]<=zeta[g=1:G,t=1:T]<=Bm[g,t])
    @variable(m,af[1:G,1:T]>=0);@variable(m,am[1:G,1:T]>=0)
    @constraint(m,af.>=delta);@constraint(m,af.>=-delta);@constraint(m,am.>=zeta);@constraint(m,am.>=-zeta)
    @variable(m,uf[1:G,1:T],Bin);@variable(m,um[1:G,1:T],Bin);@variable(m,z[1:T],Bin)
    for (x,s,B) in ((delta,uf,Bf),(zeta,um,Bm)),g=1:G,t=1:T
        if B[g,t]>0;@constraint(m,x[g,t]<=B[g,t]*s[g,t]);@constraint(m,x[g,t]>=-B[g,t]*s[g,t]);@constraint(m,s[g,t]<=z[t]);else;fix(s[g,t],0.;force=true);end
    end
    @constraint(m,sum(z)<=min(T,opt.k_time));@constraint(m,sum(uf)+sum(um)<=min(2G*T,opt.k_param))
    v̂,_=UCX2.transitions(d,ŷ)
    foilcost=@expression(m,sum((d.noload[g]+delta[g,t])*ŷ[g,t]+d.startup[g]*v̂[g,t] for g=1:G,t=1:T)+
        sum((d.marginal[g][k]+zeta[g,t])*x̂[g][k,t] for g=1:G for k=1:UCX2.K_(d,g) for t=1:T))
    nl=d.noload;mr=UCX2.mref(d)
    @objective(m,Min,sum(af[g,t]/nl[g] for g=1:G,t=1:T)+sum(am[g,t]/mr[g] for g=1:G,t=1:T)+opt.lambda_time*sum(z)+opt.lambda_param*(sum(uf)+sum(um)))
    (m=m,delta=delta,zeta=zeta,foilcost=foilcost)
end
function fw_explain(d,foil;options=Options(),levers=UCLevers(marginal=true))
    w=uc_forward(d;foil=foil);fw_explain_from(d,foil,w.u,w.p;options=options,levers=levers)
end
function fw_explain_from(d,foil,ŷ,x̂;options=Options(),levers=UCLevers(marginal=true))
    opt=options;lev=levers;t0=time();rem()=opt.time_limit-(time()-t0);G,T=UCX2.G_(d),UCX2.T_(d)
    offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    pool=Matrix{Float64}[];it=0
    while rem()>0 && it<200
        it+=1;M=fw_master(d,ŷ,x̂,opt,lev,rem())
        for uk in pool;UCX2.uc_dual_cut!(M,d,uk,offset);end
        optimize!(M.m);st=string(termination_status(M.m))
        st=="INFEASIBLE" && return Dict("status"=>"WITNESS_INFEASIBLE","iterations"=>it,"seconds"=>time()-t0)
        st=="OPTIMAL" || return Dict("status"=>st,"iterations"=>it,"seconds"=>time()-t0)
        δ=value.(M.delta);ζ=value.(M.zeta);obj=objective_value(M.m)
        # The best foil completion at the edited costs can only be cheaper than the fixed witness.
        wf=uc_forward(d;delta=δ,zeta=ζ,foil=foil,limit=rem());fc=wf.objective
        r=uc_forward(d;delta=δ,zeta=ζ,foil=opt.mode==:strong ? foil : nothing,complement=opt.mode==:strong,limit=rem())
        if (r.status=="INFEASIBLE" && opt.mode==:strong) || (r.status=="OPTIMAL" && XOPT.numerical_acceptance(fc,r.bound,offset,opt.tolerance))
            return Dict("status"=>"VALID","objective"=>obj,"iterations"=>it,"seconds"=>time()-t0,"delta"=>δ,"zeta"=>ζ,"cuts"=>length(pool))
        end
        r.status=="OPTIMAL" || return Dict("status"=>r.status,"iterations"=>it,"seconds"=>time()-t0)
        any(p->p==r.u,pool) ? (ŷ,x̂=wf.u,wf.p) : push!(pool,r.u)
    end
    Dict("status"=>"LIMIT","iterations"=>it,"seconds"=>time()-t0)
end

# Cycle 5: several witnesses. Candidates are the k best foil patterns at nominal costs (no-good cuts),
# each with its best completion; the explanation with the smallest objective is kept.
function fw_multi(d,foil;options=Options(),levers=UCLevers(marginal=true),k=5)
    t0=time();best=Dict{String,Any}("status"=>"NONE","objective"=>Inf);G,T=UCX2.G_(d),UCX2.T_(d)
    excl=Matrix{Float64}[];tried=0
    for i in 1:k
        rem=options.time_limit-(time()-t0);rem<=0 && break
        b=UCX2.uc_physical(d;limit=rem);UCX2.add_uc_foil!(b.m,b.u,foil)
        for e in excl;@constraint(b.m,sum(e[j]>.5 ? 1-b.u[j] : b.u[j] for j in eachindex(b.u))>=1);end
        @objective(b.m,Min,sum(d.noload[g]*b.u[g,t]+d.startup[g]*b.v[g,t] for g=1:G,t=1:T)+
            sum(d.marginal[g][kk]*b.p[g][kk,t] for g=1:G for kk=1:UCX2.K_(d,g) for t=1:T))
        optimize!(b.m);termination_status(b.m)==MOI.OPTIMAL || break
        ŷ=round.(value.(b.u));x̂=[value.(b.p[g]) for g in 1:G];push!(excl,ŷ);tried+=1
        o=Options(;(f=>getfield(options,f) for f in fieldnames(Options) if f!=:time_limit)...,time_limit=options.time_limit-(time()-t0))
        r=fw_explain_from(d,foil,ŷ,x̂;options=o,levers=levers)
        if r["status"]=="VALID" && r["objective"]<best["objective"];best=r;end
    end
    best["seconds"]=time()-t0;best["witnesses"]=tried;best
end
