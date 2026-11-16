"""Numerical stability audit for a FIXED foil witness under box uncertainty in binary costs.
At rho, |eta_j| <= rho*f0_j; recourse and capacities remain fixed.
The returned interval estimates the clipped witness radius within solver tolerances, not the maximal
radius attainable by changing the foil witness after observing eta.
"""
function witness_radius(d,foil,r;capacity=d.capacity,rho_max=.5,atol=1e-5,time_limit=30.)
    r.status=="SOLVER_VALIDATED" || return Dict("status"=>"NOT_VALIDATED")
    start=time();lo=0.;hi=rho_max;evals=0;tol=1e-7
    cost=d.fixed.+r.delta
    witness=sum(cost.*r.y)+sum(d.unit.*r.q)+sum(d.holding.*r.state)
    function evaluate(rho)
        remain=time_limit-(time()-start)
        z=forward(d;cost=cost.-rho.*d.fixed.*(1 .-2 .*r.y),capacity=capacity,foil=foil,complement=true,limit=remain)
        constant=rho*sum(d.fixed.*r.y)+witness
        z.status=="INFEASIBLE" && return (safe=true,violation=false,status=z.status)
        z.status!="OPTIMAL" && return (safe=false,violation=false,status=z.status)
        (safe=z.bound-constant>=-tol,violation=z.objective-constant < -tol,status=z.status)
    end
    a=evaluate(0.);evals+=1
    a.violation && return Dict("status"=>"NO_DOMINANCE","lower"=>0.,"upper"=>0.,"seconds"=>time()-start)
    !a.safe && return Dict("status"=>a.status,"lower"=>0.,"upper"=>hi,"seconds"=>time()-start)
    a=evaluate(hi);evals+=1
    a.safe && return Dict("status"=>"NUMERICAL_CLIPPED","lower"=>hi,"upper"=>hi,"seconds"=>time()-start,"evaluations"=>evals)
    !a.violation && return Dict("status"=>a.status,"lower"=>lo,"upper"=>hi,"seconds"=>time()-start)
    while hi-lo>atol
        mid=(lo+hi)/2;a=evaluate(mid);evals+=1
        if a.safe;lo=mid
        elseif a.violation;hi=mid
        else;return Dict("status"=>a.status,"lower"=>lo,"upper"=>hi,"seconds"=>time()-start);end
    end
    Dict("status"=>"NUMERICAL_BRACKET","lower"=>lo,"upper"=>hi,"seconds"=>time()-start,"evaluations"=>evals)
end
