using Test
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","levers.jl"));using .LeverXOPT
include(joinpath(@__DIR__,"..","src","enumerate_levers.jl"));using .EnumLevers
@testset "Recourse-cost levers" begin
    d=make_instance("lever_test",:retail,[1. .2 1.4 .6;.5 1. .3 1.2];seed=3)
    nom=forward(d);f=Foil([(1,3,1-round(Int,nom.y[1,3]))])
    for mode in [:weak,:strong]
        o=Options(mode=mode,margin=.02,time_limit=120.)
        # With recourse levers switched off, the lever master reproduces the primary method.
        r0=explain(d,f;options=o);r1=explain_levers(d,f;options=o,levers=Levers(fixed=true))
        @test r0.status==r1["status"]
        r0.status=="SOLVER_VALIDATED" && @test isapprox(r0.objective,r1["objective"];atol=1e-6)
    end
    small=make_instance("lever_small",:retail,[1. .3 .8 1.1];seed=5);nf=forward(small);sf=Foil([(1,3,1-round(Int,nf.y[1,3]))])
    for mode in [:weak,:strong],lev in [Levers(fixed=false,unit=true,holding=true),Levers(fixed=true,unit=true,holding=true)]
        o=Options(mode=mode,margin=.02,time_limit=120.)
        e=explain_by_enumeration(small,sf;options=o,levers=lev)
        for cuts in [:dual,:trajectory]
            r=explain_levers(small,sf;options=o,levers=lev,cuts=cuts)
            if e["status"]=="INFEASIBLE"
                @test r["status"]=="SOLVER_INFEASIBLE"
            else
                @test r["status"]=="SOLVER_VALIDATED"
                @test isapprox(r["objective"],e["objective"];atol=1e-6)
                v=verify_levers(small,sf,r;options=o,levers=lev)
                @test v["valid"]
                @test v["kkt_gap"]<=1e-6
            end
        end
    end
    # Dual bounds of the lemma for the retail network.
    b=lever_dual_bound(d,Levers(fixed=true,unit=true,holding=true))
    @test b.N==1+4+2*4
    @test isapprox(b.dual,(b.N-1)*b.cmax;rtol=1e-5)
end
