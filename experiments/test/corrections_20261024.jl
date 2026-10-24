using Test, JSON3, JuMP
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","levers.jl"));using .LeverXOPT
include(joinpath(@__DIR__,"..","src","enumerate_levers.jl"));using .EnumLevers
include(joinpath(@__DIR__,"..","src","uc.jl"));using .UCX
include(joinpath(@__DIR__,"..","src","anytime.jl"));using .AnytimeXOPT
include(joinpath(@__DIR__,"..","src","uc2.jl"))
include(joinpath(@__DIR__,"..","src","audit.jl"))
include(joinpath(@__DIR__,"..","src","literature_cg.jl"))

@testset "Audit correction regressions" begin
if get(ENV,"XOPT_REGRESSION_GROUP","all") in ("all","validation")
@testset "A03 witness domains and anytime seeds" begin
    d=Instance("audit_fractional",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));f=Foil([(1,2,1)])
    for y in ([.5 .6],[-1. 1.],[1. NaN],[1. Inf],ones(1,1),ones(2,1))
        r=Result(status="SOLVER_VALIDATED",delta=zeros(1,2),y=y,q=ones(1,2),state=zeros(1,2))
        @test !verify(d,f,r)["valid"]
        @test !validate_incumbent(d,f,r,Options())["valid"]
    end
    for key in (:delta,:q,:state), x in (fill(NaN,1,2),zeros(1,1))
        fields=Dict(:delta=>zeros(1,2),:y=>ones(1,2),:q=>ones(1,2),:state=>zeros(1,2));fields[key]=x
        @test !verify(d,f,Result(;status="SOLVER_VALIDATED",fields...))["valid"]
    end
    r=Dict{String,Any}("status"=>"SOLVER_VALIDATED","delta"=>zeros(1,2),"zp"=>zeros(1,2),"zh"=>zeros(1,2),"y"=>[.5 .6],"q"=>ones(1,2),"state"=>zeros(1,2),"foil_cost"=>3.3)
    @test !verify_levers(d,f,r)["valid"]
    r["y"]=ones(1,2);r["zp"]=zeros(1,1)
    @test !verify_levers(d,f,r)["valid"]
end
@testset "A06 separate cost parameters and shared capacity budgets" begin
    d=Instance("audit_support",:retail,ones(1,1),[1.],fill(3.,1,1),ones(1,1),fill(.2,1,1),1.,zeros(1));f=Foil([(1,1,1)])
    r=Dict{String,Any}("status"=>"SOLVER_VALIDATED","delta"=>fill(.1,1,1),"zp"=>fill(.1,1,1),"zh"=>zeros(1,1),"y"=>ones(1,1),"q"=>ones(1,1),"state"=>zeros(1,1),"foil_cost"=>4.2)
    @test !verify_levers(d,f,r;options=Options(k_param=1),levers=Levers(unit=true))["valid"]
    d2=Instance("capacity_support",:retail,ones(1,2),[1.,1.],fill(3.,1,2),ones(1,2),fill(.2,1,2),1.,zeros(1));f2=Foil([(1,1,1)])
    r2=Dict{String,Any}("status"=>"SOLVER_VALIDATED","delta"=>zeros(1,2),"zp"=>[.1 0.],"zh"=>zeros(1,2),"y"=>ones(1,2),"q"=>ones(1,2),"state"=>zeros(1,2),"foil_cost"=>8.1)
    @test !verify_levers(d2,f2,r2;options=Options(k_time=1),levers=Levers(unit=true),capacity=[1.,1.1])["valid"]
    @test !verify_levers(d2,f2,r2;options=Options(k_param=1),levers=Levers(unit=true),capacity=[1.,1.1])["valid"]
    ud=load_uc(joinpath(@__DIR__,"..","data","pglib_uc","rts_2020-07-06.json"),["113_CT_1"];T=1,start=15,ramps=false,secant=true)
    z=uc_forward(ud;delta=fill(.1,1,1),zeta=fill(.1,1,1));uf=Foil([(1,1,round(Int,z.u[1,1]))])
    ur=Dict{String,Any}("status"=>"SOLVER_VALIDATED","u"=>z.u,"p"=>z.p,"r"=>z.r,"delta"=>fill(.1,1,1),"zeta"=>fill(.1,1,1),"foil_cost"=>z.objective)
    @test !uc_verify(ud,uf,ur;options=Options(k_param=1),levers=UCLevers(marginal=true))["valid"]
    for key in ("u","delta","zeta"), bad in (fill(NaN,1,1),zeros(1,2))
        rr=copy(ur);rr[key]=bad;@test !uc_verify(ud,uf,rr;levers=UCLevers(marginal=true))["valid"]
    end
    rr=copy(ur);rr["u"]=fill(.6,1,1);@test !uc_verify(ud,uf,rr;levers=UCLevers(marginal=true))["valid"]
    rr=copy(ur);rr["p"]=[zeros(2,1)];@test !uc_verify(ud,uf,rr;levers=UCLevers(marginal=true))["valid"]
    rr=copy(ur);rr["r"]=[NaN];@test !uc_verify(ud,uf,rr;levers=UCLevers(marginal=true))["valid"]
end
@testset "A07 common option and lever assumptions" begin
    d=Instance("options",:retail,ones(1,1),[1.],fill(3.,1,1),ones(1,1),ones(1,1),1.,zeros(1));f=Foil([(1,1,1)])
    ud=load_uc(joinpath(@__DIR__,"..","data","pglib_uc","rts_2020-07-06.json"),["113_CT_1"];T=1,start=15,ramps=false,secant=true)
    invalid=[Options(mode=:strong,margin=0.),Options(epsilon=-1.),Options(lambda_time=-1.),Options(lambda_param=-1.),Options(cost_bound=1.1),Options(tolerance=0.),Options(time_limit=NaN),Options(k_param=-1),Options(max_iterations=-1)]
    for o in invalid
        @test_throws ArgumentError explain(d,f;options=o)
        @test_throws ArgumentError AuditXOPT.naive_explain(d,f;options=o)
        @test_throws ArgumentError literature_cg(d,f;options=o)
        @test_throws ArgumentError explain_levers(d,f;options=o)
        @test_throws ArgumentError explain_by_enumeration(d,f;options=o)
        @test_throws ArgumentError uc_explain(ud,f;options=o)
        @test_throws ArgumentError uc_explain_by_enumeration(ud,f;options=o)
        @test_throws ArgumentError verify(d,f,Result();options=o)
        @test_throws ArgumentError verify_levers(d,f,Dict("status"=>"UNKNOWN");options=o)
        @test_throws ArgumentError uc_verify(ud,f,Dict("status"=>"UNKNOWN");options=o)
    end
    for b in (-.1,1.1,NaN)
        @test_throws ArgumentError explain_levers(d,f;levers=Levers(unit=true,bound=b))
        @test_throws ArgumentError uc_explain(ud,f;levers=UCLevers(marginal=true,bound=b))
    end
end
@testset "Verifier strong comparison uses requested tolerance" begin
    d=Instance("strict_comparison",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));f=Foil([(1,2,1)])
    r=Result(status="SOLVER_VALIDATED",delta=[0. -2.],y=ones(1,2),q=ones(1,2),state=zeros(1,2))
    o=Options(mode=:strong,margin=5e-6,tolerance=1e-6)
    @test !verify(d,f,r;options=o)["valid"]
end
@testset "UCX2 shares safety checks" begin
    d=UCX2.load_uc(joinpath(@__DIR__,"..","data","pglib_uc","rts_2020-07-06.json"),["113_CT_1"];T=1,start=15,ramps=false,secant=true);f=Foil([(1,1,1)])
    @test_throws ArgumentError UCX2.uc_explain(d,f;options=Options(mode=:strong,margin=0.))
    @test_throws ArgumentError UCX2.uc_verify(d,f,Dict("status"=>"UNKNOWN");options=Options(mode=:strong,margin=0.))
    z=UCX2.uc_forward(d;delta=fill(.1,1,1),zeta=fill(.1,1,1))
    r=Dict{String,Any}("status"=>"SOLVER_VALIDATED","u"=>z.u,"p"=>z.p,"r"=>z.r,"delta"=>fill(.1,1,1),"zeta"=>fill(.1,1,1),"foil_cost"=>z.objective)
    @test !UCX2.uc_verify(d,f,r;options=Options(k_param=1),levers=UCX2.UCLevers(marginal=true))["valid"]
    r["u"]=fill(NaN,1,1);@test !UCX2.uc_verify(d,f,r;levers=UCX2.UCLevers(marginal=true))["valid"]
    @test UCX2.uc_explain_by_enumeration(d,f;options=Options(time_limit=0.))["status"]=="TIME_LIMIT"
end
@testset "A08 enumeration global deadline" begin
    d=Instance("deadline",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));f=Foil([(1,2,1)])
    ud=load_uc(joinpath(@__DIR__,"..","data","pglib_uc","rts_2020-07-06.json"),["113_CT_1"];T=1,start=15,ramps=false,secant=true);uf=Foil([(1,1,1)])
    for limit in (0.,1e-9)
        for r in (explain_by_enumeration(d,f;options=Options(time_limit=limit)),uc_explain_by_enumeration(ud,uf;options=Options(time_limit=limit)))
            @test r["status"]=="TIME_LIMIT"
            @test !r["enumeration_complete"]
            @test r["lower_bound"]==0.
            @test isnothing(r["objective"])
            @test r["seconds"]<2.
        end
    end
end
end

if get(ENV,"XOPT_REGRESSION_GROUP","all") in ("all","uc")
@testset "A02 bounded UC competitor duals reproduce audited optimum" begin
    a=JSON3.read(read(joinpath(@__DIR__,"fixtures","uc_regression.json"),String));d=uc_restore(a.instance)
    f=Foil([Tuple(Int.(x)) for x in a.foil]);o=Options(mode=:strong,margin=Float64(a.margin),time_limit=90.);lev=UCLevers(noload=false,marginal=true)
    r=uc_explain(d,f;options=o,levers=lev,cuts=:dual)
    @test r["status"]=="SOLVER_VALIDATED"
    @test r["objective"]≈Float64(a.expected_objective) atol=1e-7
    @test uc_verify(d,f,r;options=o,levers=lev)["valid"]
    # The bound used by each competitor cut must follow the caller's lever bound.
    for bound in (.2,.95)
        l=UCLevers(noload=false,marginal=true,bound=bound);M=UCX.uc_master(d,f,o,l,30.)
        before=num_variables(M.m);UCX.uc_dual_cut!(M,d,ones(3,4),-o.margin);added=all_variables(M.m)[before+1:end]
        cb=UCX.uc_dual_bound(d,l).price
        @test all(has_lower_bound(v)&&has_upper_bound(v) for v in added)
        @test all(has_upper_bound(v)&&upper_bound(v)<=cb for v in added)
        @test all(has_lower_bound(v)&&lower_bound(v)>=-cb for v in added)
    end
end
end

end
