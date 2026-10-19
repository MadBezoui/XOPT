const R=normpath(joinpath(@__DIR__,".."))*"/"
include(R*"src/XOPT.jl");using .XOPT
include(R*"src/uc.jl");using .UCX
using JSON3
a=nothing
for f in filter(x->startswith(basename(x),"uc_enum_w"),readdir(R*"results";join=true)), l in eachline(f)
  x=JSON3.read(l); String(x.key)=="tiny_2020-07-06_s1_h15|[(3, 2, 1)]|strong|M" && (global a=x)
end
d=uc_restore(a.instance);fo=Foil([Tuple(Int.(v)) for v in a.foil]);lev=UCLevers(noload=false,marginal=true)
o=Options(mode=:strong,margin=Float64(a.margin),time_limit=300.)
println("demand ",d.demand," renew ",d.renew," pmin ",d.pmin," marg ",d.marginal," width ",d.width)
e=uc_explain_by_enumeration(d,fo;options=o,levers=lev);uh,de,ze=e["argmin"];println("enum ",e["objective"]," u=",uh," ze=",ze)
rd=uc_explain(d,fo;options=o,levers=lev,cuts=:dual);println("dual ",rd["objective"]," ze=",rd["zeta"]," u=",rd["u"])
# Is the enumeration optimum valid against the exact oracle?
z=uc_forward(d;zeta=ze,foil=fo,complement=true);w=uc_forward(d;zeta=ze,pattern=uh)
println("enum optimum: foil best ",w.objective," outside best ",z.objective," status ",z.status," diff ",z.objective-w.objective)
for t in rd["trace"];println(t);end
using JuMP
y1=uc_forward(d;foil=fo,complement=true).u;println("y1=",y1)
for withcut in (false,true)
 M=UCX.uc_master(d,fo,o,lev,300.)
 withcut && UCX.uc_dual_cut!(M,d,y1,-o.margin)
 for j in eachindex(uh);fix(M.b.u[j],uh[j];force=true);end
 for j in eachindex(ze);fix(M.zeta[j],ze[j];force=true);end
 optimize!(M.m);println("cut=",withcut," status ",termination_status(M.m)," foilcost ",has_values(M.m) ? value(M.foilcost) : nothing," obj ",objective_value(M.m))
end
# exact competitor value at ze
c=uc_forward(d;zeta=ze,pattern=y1);println("competitor y1 at ze: ",c.objective)
