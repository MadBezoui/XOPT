using Test
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","anytime.jl"));using .AnytimeXOPT
@testset "Coordinate baseline rejects invalid capacity intervention cost" begin
 d=Instance("cost-boundary",:retail,ones(1,2),fill(2.,2),fill(3.,1,2),zeros(1,2),ones(1,2),1.,zeros(1));f=Foil([(1,2,1)])
 for capcost in (NaN,Inf,-.1)
  @test_throws ArgumentError coordinate_baseline(d,f;capcost=capcost)
 end
end
