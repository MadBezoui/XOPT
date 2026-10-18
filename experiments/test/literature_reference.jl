using Test,JuMP
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","literature_cg.jl"))
@testset "Published cost-CG scheme versus exhaustive reference" begin
    d=Instance("analytic",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1))
    f=Foil([(1,2,1)])
    for (mode,eps,margin,truth) in [(:weak,0.,.02,2/3),(:weak,.5,.02,.5),(:strong,0.,.1,.7)]
        opt=Options(mode=mode,epsilon=eps,margin=margin,lambda_time=0.)
        r=literature_cg(d,f;options=opt)
        @test r.status=="SOLVER_VALIDATED"
        @test r.objective≈truth atol=1e-6
        @test verify(d,f,r;options=opt)["valid"]
    end
    d=make_instance("compound",:retail,[1.0 .7 1.2;.8 1.1 .6];seed=81)
    f=Foil([(1,2,1),(2,3,1)])
    for mode in [:weak,:strong]
        opt=Options(mode=mode,margin=.05)
        r=literature_cg(d,f;options=opt);e=explain(d,f;options=opt,method=:enumerate)
        @test r.status==e.status
        @test r.objective≈e.objective atol=1e-5
        @test verify(d,f,r;options=opt)["valid"]
    end
end
