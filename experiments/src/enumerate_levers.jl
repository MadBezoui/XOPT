module EnumLevers
# Independent exact reference for tiny retail instances: every binary pattern, every vertex of its
# recourse polytope (basis enumeration, no LP duality, no KKT), and one linear model per foil vertex.
using ..XOPT
using ..LeverXOPT
using JuMP, HiGHS, LinearAlgebra
const MOI=JuMP.MOI
# k-subsets of 1:n in lexicographic order (avoids an extra package dependency).
function combinations(r::UnitRange{Int},k::Int)
    n=length(r);out=Vector{Vector{Int}}();c=collect(1:k)
    k==0 && return [Int[]];k>n && return out
    while true
        push!(out,[r[j] for j in c])
        i=k;while i>=1 && c[i]==n-k+i;i-=1;end
        i==0 && break
        c[i]+=1;for j=i+1:k;c[j]=c[j-1]+1;end
    end
    out
end
export recourse_vertices, explain_by_enumeration

# Recourse polytope of pattern y in variables x=(q_it, s_it for t<T); s_iT = 0, s_i0 = 0.
function recourse_system(d::Instance,y,capacity)
    I,T=size(d.demand);nq=I*T;ns=I*(T-1);n=nq+ns
    qi(i,t)=(t-1)*I+i;si(i,t)=nq+(t-1)*I+i
    Aeq=zeros(I*T,n);beq=zeros(I*T)
    for i=1:I,t=1:T
        r=(t-1)*I+i;Aeq[r,qi(i,t)]=1.
        t>1 && (Aeq[r,si(i,t-1)]=1.)
        t<T && (Aeq[r,si(i,t)]=-1.)
        beq[r]=d.demand[i,t]
    end
    rows=Vector{Vector{Float64}}();rhs=Float64[]
    for i=1:I,t=1:T;a=zeros(n);a[qi(i,t)]=1.;push!(rows,a);push!(rhs,capacity[t]*y[i,t]);end
    for t=1:T;a=zeros(n);for i=1:I;a[qi(i,t)]=1.;end;push!(rows,a);push!(rhs,capacity[t]);end
    for j=1:n;a=zeros(n);a[j]=-1.;push!(rows,a);push!(rhs,0.);end
    Ain=reduce(vcat,permutedims.(rows));(Aeq=Aeq,beq=beq,Ain=Ain,bin=rhs,n=n,qi=qi,si=si)
end
function recourse_vertices(d::Instance,y,capacity=d.capacity;tol=1e-9)
    S=recourse_system(d,y,capacity);I,T=size(d.demand);k=S.n-size(S.Aeq,1)
    verts=Vector{Vector{Float64}}()
    for B in combinations(1:size(S.Ain,1),k)
        A=vcat(S.Aeq,S.Ain[B,:]);rank(A)<S.n && continue
        x=A\vcat(S.beq,S.bin[B])
        maximum(abs.(S.Aeq*x.-S.beq))<=1e-7 && maximum(S.Ain*x.-S.bin)<=1e-7 || continue
        x=round.(x;digits=9);any(v->maximum(abs.(v.-x))<=1e-7,verts) || push!(verts,x)
    end
    q=[ [v[S.qi(i,t)] for i=1:I,t=1:T] for v in verts]
    s=[ [t<T ? v[S.si(i,t)] : 0. for i=1:I,t=1:T] for v in verts]
    collect(zip(q,s))
end
matches(y,foil)=all(round(Int,y[i,t])==v for (i,t,v) in foil.literals)
function explain_by_enumeration(d::Instance,foil::Foil;options=Options(),levers=Levers(),capacity=d.capacity)
    opt=options;lev=levers;I,T=size(d.demand)
    pats=[reshape([(mask>>(j-1))&1 for j in 1:I*T],I,T) for mask in 0:(2^(I*T)-1)]
    V=Dict(p=>recourse_vertices(d,p,capacity) for p in pats);feas=[p for p in pats if !isempty(V[p])]
    offset=opt.mode==:strong ? -opt.margin : opt.epsilon
    comps=[(p,v) for p in feas if !(opt.mode==:strong && matches(p,foil)) for v in V[p]]
    best=Inf;arg=nothing
    F=d.fixed;P0=d.unit;H0=d.holding
    Bf=lev.fixed ? opt.cost_bound.*F : zeros(I,T);Bp=lev.unit ? lev.bound.*P0 : zeros(I,T);Bh=lev.holding ? lev.bound.*H0 : zeros(I,T);Bh[:,T].=0.
    for yh in feas
        matches(yh,foil) || continue
        for (qv,sv) in V[yh]
            m=Model(HiGHS.Optimizer);set_silent(m);set_optimizer_attribute(m,"mip_rel_gap",0.);set_optimizer_attribute(m,"threads",1)
            @variable(m,-Bf[i,t]<=de[i=1:I,t=1:T]<=Bf[i,t]);@variable(m,-Bp[i,t]<=zp[i=1:I,t=1:T]<=Bp[i,t]);@variable(m,-Bh[i,t]<=zh[i=1:I,t=1:T]<=Bh[i,t])
            @variable(m,a1[1:I,1:T]>=0);@variable(m,a2[1:I,1:T]>=0);@variable(m,a3[1:I,1:T]>=0)
            @constraint(m,a1.>=de);@constraint(m,a1.>=-de);@constraint(m,a2.>=zp);@constraint(m,a2.>=-zp);@constraint(m,a3.>=zh);@constraint(m,a3.>=-zh)
            @variable(m,u[1:3,1:I,1:T],Bin);@variable(m,z[1:T],Bin)
            for (k,(v,B)) in enumerate(((de,Bf),(zp,Bp),(zh,Bh))),i=1:I,t=1:T
                @constraint(m,v[i,t]<=B[i,t]*u[k,i,t]);@constraint(m,v[i,t]>=-B[i,t]*u[k,i,t]);@constraint(m,u[k,i,t]<=z[t])
            end
            @constraint(m,sum(z)<=min(T,opt.k_time));@constraint(m,sum(u)<=min(3I*T,opt.k_param))
            fcost=@expression(m,sum((F[i,t]+de[i,t])*yh[i,t]+(P0[i,t]+zp[i,t])*qv[i,t]+(H0[i,t]+zh[i,t])*sv[i,t] for i=1:I,t=1:T))
            for (p,(qw,sw)) in comps
                @constraint(m,fcost<=sum((F[i,t]+de[i,t])*p[i,t]+(P0[i,t]+zp[i,t])*qw[i,t]+(H0[i,t]+zh[i,t])*sw[i,t] for i=1:I,t=1:T)+offset)
            end
            obj=sum(a1./F)+sum(a2[i,t]/P0[i,t] for i=1:I,t=1:T if Bp[i,t]>0;init=0.)+sum(a3[i,t]/H0[i,t] for i=1:I,t=1:T if Bh[i,t]>0;init=0.)
            @objective(m,Min,obj+opt.lambda_time*sum(z)+opt.lambda_param*sum(u));optimize!(m)
            if termination_status(m)==MOI.OPTIMAL && objective_value(m)<best
                best=objective_value(m);arg=(yh,qv,sv,value.(de),value.(zp),value.(zh))
            end
        end
    end
    Dict{String,Any}("status"=>isfinite(best) ? "OPTIMAL" : "INFEASIBLE","objective"=>isfinite(best) ? best : nothing,
        "patterns"=>length(feas),"competitor_vertices"=>length(comps),"argmin"=>arg)
end
end
