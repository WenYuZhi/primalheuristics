from primalheuristics import FeasibilityPump
from primalheuristics import LocalBranch
from primalheuristics import LVS
from readmodel import ModelData
from postdata import PostResults
from tqdm import tqdm

n_start, n_end = 0, 10
model_data = ModelData()
mip_model, read_file = model_data.load(n_start = n_start, n_end = n_end)
pump_results, local_branch_results, lvs_results = [], [], []

for i in tqdm(range(len(mip_model))):
    feasibility_pump = FeasibilityPump(mip_model[i])
    x_s, obj, distance, cpu_time, is_feas = feasibility_pump.run(MAX_ITER=200)
    pump_results.append([read_file[i], obj, distance, cpu_time, is_feas])

    if is_feas:
        local_branch = LocalBranch(mip_model[i], x_s)
        obj_local, cpu_time = local_branch.run(r = 3, timelimit = 60)
        local_branch_results.append([read_file[i], obj_local, cpu_time])
    
        InterelatedSearch = LVS(mip_model[i], x_s)
        obj_local, cpu_time = InterelatedSearch.run(MAX_ITER=1, timelimit = 60)
        lvs_results.append([read_file[i], obj_local, cpu_time])

post_results = PostResults()
post_results.set_data(pump_results, local_branch_results, lvs_results)
post_results.merge_data()
post_results.save_data(n_start, n_end)
