using Test
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","anytime.jl"));using .AnytimeXOPT
@testset "Anytime incumbent, bounds and exhaustive agreement" begin
 d=Instance("analytic",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));f=Foil([(1,2,1)])
 for o in [Options(lambda_time=0.,time_limit=60.),Options(mode=:strong,margin=.1,lambda_time=0.,time_limit=60.),Options(epsilon=.5,lambda_time=0.,time_limit=60.)]
  exact=explain(d,f;options=o,method=:enumerate)
  for init in [false,true]
   a=anytime_explain(d,f;options=o,initialize=init)
   @test a["status"]=="SOLVER_VALIDATED"
   @test a["upper_bound"]≈exact.objective atol=1e-5
   @test a["lower_bound"]<=exact.objective+1e-5
   @test a["absolute_gap"]<=1e-5
   @test a["verification"]["valid"]
  end
 end
 o=Options(max_iterations=0,time_limit=60.,lambda_time=0.)
 a=anytime_explain(d,f;options=o)
 @test a["status"]=="FEASIBLE_ITERATION_LIMIT"
 @test a["upper_bound"]≈2/3 atol=1e-6
 @test a["lower_bound"]==0.
 @test a["absolute_gap"]≈2/3 atol=1e-6
 @test a["result"]["status"]=="FEASIBLE_VALIDATED"
 @test a["verification"]["valid"]
 @test a["first_feasible_seconds"]<=a["seconds"]
 @test anytime_explain(d,f;options=with_options(o;time_limit=0.))["status"]=="TIME_LIMIT"
 @test isnothing(anytime_explain(d,f;options=o,initialize=false)["result"])
 @test coordinate_baseline(d,f;options=with_options(o;k_time=0)).status=="SUPPORT_BOUND_EXCEEDED"
 @test coordinate_baseline(d,f;options=with_options(o;cost_bound=.1)).status=="EDIT_BOUND_EXCEEDED"
end
@testset "Compound requests fall back safely" begin
 d=make_instance("compound",:retail,[1. .7 1.2;.8 1.1 .6];seed=81);f=Foil([(1,2,1),(2,3,1)])
 o=Options(time_limit=60.)
 @test coordinate_baseline(d,f;options=o).status=="NOT_APPLICABLE"
 r=anytime_explain(d,f;options=o)
 e=explain(d,f;options=o,method=:enumerate)
 @test r["status"]==e.status
 @test r["upper_bound"]≈e.objective atol=1e-5
end
@testset "Capacity restoration and menu lower bounds" begin
 d=Instance("capacity_control",:retail,reshape([1.,.25],1,2),[1.05,1.05],fill(3.,1,2),fill(.25,1,2),fill(.2,1,2),1.,[0.]);f=Foil([(1,2,0)])
 o=Options(time_limit=60.,lambda_time=0.)
 @test forward(d;foil=f).status=="INFEASIBLE"
 inc=[zeros(2),[.2625,0.],[0.,.2625]]
 r=anytime_menu(d,f,inc;options=o)
 @test r["status"]=="SOLVER_VALIDATED"
 @test r["scenario"]==2
 @test r["upper_bound"]≈.25 atol=1e-6
 @test r["absolute_gap"]<=1e-5
 @test r["verification"]["valid"]
 # A retained nominal incumbent cannot certify unresolved lower-cost scenarios.
 d2=Instance("a",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));f2=Foil([(1,2,1)])
 rr=anytime_menu(d2,f2,[zeros(2),[.02,0.]];options=Options(max_iterations=0,time_limit=60.,lambda_time=0.))
 @test rr["status"]=="FEASIBLE_UNRESOLVED"
 @test rr["lower_bound"]==0.
 @test rr["upper_bound"]>0.
 empty=anytime_menu(d2,f2,[zeros(2),[.02,0.]];options=Options(time_limit=0.))
 @test empty["scenario_statuses"]==["UNVISITED","UNVISITED"]
 @test empty["lower_bound"]==0.
 @test isnothing(empty["upper_bound"])
end
