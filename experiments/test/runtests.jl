using Test
p=joinpath(@__DIR__,"..","src","XOPT.jl")
@testset "Research implementation exists" begin
    @test isfile(p)
end
include(p)
using .XOPT
@testset "Oracle incumbent cannot establish acceptance" begin
    # A witness tying an incumbent at 10 may still be worse than the unknown
    # optimum in [9.9, 10]. The lower bound prevents false acceptance.
    @test !XOPT.numerical_acceptance(10.,9.9,0.,1e-6)
    @test XOPT.numerical_acceptance(10.,10.,0.,1e-6)
    @test !XOPT.numerical_acceptance(9.98,9.99,-.02,1e-6)
    @test XOPT.numerical_acceptance(9.98,10.,-.02,1e-6)
    @test !XOPT.numerical_acceptance(10.,-Inf,0.,1e-6)
    @test !XOPT.numerical_acceptance(10.,NaN,0.,1e-6)
end
@testset "Analytical two-period benchmark" begin
    d=Instance("analytic",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1))
    foil=Foil([(1,2,1)])
    n=forward(d)
    @test n.status=="OPTIMAL"
    @test n.objective≈4. atol=1e-7
    for (mode,eps,margin,expected) in [(:weak,0.,0.,2/3),(:weak,.5,0.,.5),(:strong,0.,.1,.7)]
        opts=Options(mode=mode,epsilon=eps,margin=margin,lambda_time=0.,lambda_param=0.,time_limit=30.)
        a=explain(d,foil;options=opts)
        b=explain(d,foil;options=opts,method=:enumerate)
        @test a.status=="SOLVER_VALIDATED"
        @test b.status=="SOLVER_VALIDATED"
        @test a.objective≈expected atol=2e-6
        @test b.objective≈a.objective atol=2e-6
        @test verify(d,foil,a;options=opts)["valid"]
    end
    @test explain(d,foil;options=Options(k_time=0)).status=="SOLVER_INFEASIBLE"
    @test explain(d,foil;options=Options(time_limit=0.)).status=="TIME_LIMIT"
end
@testset "Complete pattern baseline across seeds and modes" begin
    using Random
    for family in [:retail,:hospital], seed in 1:4
        rng=MersenneTwister(seed)
        d=make_instance("test",family,0.5.+rand(rng,2,3);seed=seed)
        n=forward(d)
        @test n.status=="OPTIMAL"
        foil=Foil([(1,2,1-round(Int,n.y[1,2]))])
        for mode in [:weak,:strong]
            opts=Options(mode=mode,margin=.02,lambda_time=.01,time_limit=60.)
            a=explain(d,foil;options=opts)
            b=explain(d,foil;options=opts,method=:enumerate)
            @test a.status==b.status
            if a.status=="SOLVER_VALIDATED"
                @test a.objective≈b.objective atol=2e-5
                @test verify(d,foil,a;options=opts)["valid"]
            end
        end
    end
end
@testset "Capacity menu uses scenario-specific comparisons" begin
    d=Instance("capacity",:retail,ones(1,2),[1.,2.],fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1))
    foil=Foil([(1,2,0)])
    @test explain(d,foil).status=="SOLVER_INFEASIBLE"
    opts=Options(lambda_time=0.,lambda_param=0.)
    r=explain_menu(d,foil,[[0.,0.],[1.,0.]];options=opts)
    @test r["status"]=="SOLVER_VALIDATED"
    @test r["scenario"]==2
    @test r["objective"]≈1. atol=1e-6
end
@testset "Conjunction foil, complement and additive cuts" begin
    d=make_instance("conjunction",:retail,[1.0 0.7 1.2;0.8 1.1 0.6];seed=81)
    foil=Foil([(1,2,1),(2,3,1)])
    for opts in [Options(epsilon=.1,lambda_time=0.),Options(mode=:strong,margin=.05,lambda_time=0.)]
        a=explain(d,foil;options=opts)
        b=explain(d,foil;options=opts,method=:enumerate)
        @test a.status==b.status
        if a.status=="SOLVER_VALIDATED"
            @test a.objective≈b.objective atol=1e-5
            @test verify(d,foil,a;options=opts)["valid"]
            bad=forward(d;cost=d.fixed.+a.delta,foil=foil,complement=true)
            @test bad.status=="INFEASIBLE" || !(bad.y[1,2]==1 && bad.y[2,3]==1)
        end
    end
    @test_throws ArgumentError Foil([(1,1,1),(1,1,0)])
    @test_throws ArgumentError Foil([(1,1,2)])
end
