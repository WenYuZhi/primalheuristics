from primalheuristics import FeasibilityPump
from readmodel import ModelData
from postdata import PostResults
from tqdm import tqdm

n_start, n_end = 0, 100
model_data = ModelData()
mip_model, read_file = model_data.load(n_start = n_start, n_end = n_end)
pump_results = []

for i in tqdm(range(len(mip_model))):
    feasibility_pump = FeasibilityPump(mip_model[i])
    x_s, obj, distance, cpu_time, is_feas = feasibility_pump.run(MAX_ITER=100)
    pump_results.append([read_file[i], obj, distance, cpu_time, is_feas])

post_results = PostResults()
post_results.set_data(pump_results)
post_results.merge_data()
post_results.save_data(n_start, n_end)
