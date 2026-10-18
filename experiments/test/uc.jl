using Test
include(joinpath(@__DIR__,"..","src","XOPT.jl"));using .XOPT
include(joinpath(@__DIR__,"..","src","uc.jl"));using .UCX
@testset "Unit commitment levers" begin
    f=joinpath(@__DIR__,"..","data","pglib_uc","rts_2020-07-06.json")
    d=load_uc(f,["113_CT_1","322_CT_5","101_CT_1"];T=4,start=15,ramps=false,secant=true)
    nom=uc_forward(d);@test nom.status=="OPTIMAL"
    # The combinatorial feasibility check agrees with the MILP model on every commitment.
    pats=[reshape(Float64.([(mask>>(j-1))&1 for j in 1:12]),3,4) for mask in 0:4095]
    @test all(UCX.pattern_feasible(d,u)==(uc_forward(d;pattern=u).status=="OPTIMAL") for u in pats)
    fo=Foil([(3,2,1-round(Int,nom.u[3,2]))])
    for mode in [:weak,:strong],lev in [UCLevers(noload=false,marginal=true),UCLevers(marginal=true)]
        o=Options(mode=mode,margin=1e-3*nom.objective,time_limit=120.)
        e=uc_explain_by_enumeration(d,fo;options=o,levers=lev)
        for cuts in [:dual,:trajectory]
            r=uc_explain(d,fo;options=o,levers=lev,cuts=cuts)
            if e["status"]=="INFEASIBLE"
                @test r["status"]=="SOLVER_INFEASIBLE"
            else
                @test r["status"]=="SOLVER_VALIDATED"
                @test isapprox(r["objective"],e["objective"];atol=1e-6)
                @test uc_verify(d,fo,r;options=o,levers=lev)["valid"]
            end
        end
    end
    # With activation levers only and fixed marginal costs, value cuts and the ramped model are accepted.
    dr=load_uc(f,["113_CT_1","322_CT_5","101_CT_1"];T=4,start=15,ramps=true,secant=true)
    r=uc_explain(dr,fo;options=Options(time_limit=120.),levers=UCLevers())
    @test r["status"] in ("SOLVER_VALIDATED","SOLVER_INFEASIBLE")
    @test_throws ArgumentError uc_explain(dr,fo;levers=UCLevers(marginal=true))
end
