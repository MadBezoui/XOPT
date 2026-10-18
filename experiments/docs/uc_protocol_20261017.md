# Unit commitment case study protocol (17 October 2026)

This protocol is fixed before the runs. Every attempt is retained, including unresolved ones.

## Data

Four days of the RTS-GMLC system from PGLib-UC (CC BY 4.0): 27 January, 3 April, 6 July and 27 October 2020. The files and their SHA-256 hashes are in `experiments/data/pglib_uc`. Generator costs, startup costs, minimum up and down times, ramp limits and initial states are the published values. Renewable output must be at least its published minimum and can be curtailed free of charge down to it. The system is rescaled so that the peak of the net load (demand minus available renewable output) over the horizon equals 80% of the capacity of the selected units. Demand, renewable output and reserves share this factor, and reserves may be covered by renewables. The hot-start cost is used as the startup cost. Initial commitments and the remaining minimum up and down times are the published ones, but initial outputs belong to the full system and are left free, so ramp limits apply from the second hour.

## Model

Single-bus unit commitment. The pattern is the commitment of each unit in each hour. Startups and shutdowns follow from it. The recourse is the dispatch above minimum output, with the published convex piecewise-linear cost curves. Activation levers edit the hourly no-load cost (the cost at minimum output) within 80% of its value. Recourse levers shift the marginal cost of every segment of a unit in an hour by at most 80% of its cheapest segment. Edits are normalised by these reference values. Recourse levers need the dispatch to be a network flow, so ramp limits are switched off in every configuration that uses them. Configuration F-R keeps ramp limits with activation levers only.

## Correctness study

Three unit sets (three small turbines with each cost curve replaced by its secant, and two pairs of units with their full curves), two four-hour windows (hours 1 to 4 and 15 to 18), the four days, net load peaking at 60% of the capacity, two single-literal queries per instance (one start, one stop when available), weak and strong modes, levers M and FM. Each case is solved by complete enumeration of commitments and of the vertices of each hourly dispatch polytope, with no LP duality and no optimality conditions, and by constraint generation with dual and with trajectory cuts. Limit 300 seconds per method.

## Benchmark

The ten units listed in `run_uc.jl`, hours 1 to 12 with the published initial states, the four days, four single-literal queries per day (two starts, two stops), weak and strong modes, and five configurations: F-R, F, M with dual cuts, FM with dual cuts and FM with trajectory cuts. The margin is 0.1% of the nominal cost. The limit is 300 seconds per run, one solver thread, six runs in parallel. Every validated explanation is checked afresh: physical feasibility, edit bounds, the foil cost against a direct recomputation, and a fresh oracle at the edited costs.
