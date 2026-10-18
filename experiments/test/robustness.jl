using Test
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","robustness.jl"))
d=Instance("analytic",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));foil=Foil([(1,2,1)])
r=explain(d,foil;options=Options(mode=:strong,margin=.1,lambda_time=0.))
x=witness_radius(d,foil,r)
@test x["status"]=="NUMERICAL_BRACKET"
@test x["lower"]<=.1/3<=x["upper"]
@test x["upper"]-x["lower"]<=1e-5
println(x)
