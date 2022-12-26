import pandas as pd
import datetime

BENCHMARK_PATH = "./" + "benchmark/MIPLIB2017/{}"

class PostResults():
    def __init__(self) -> None:
        self.benchmark_stat = pd.read_csv(BENCHMARK_PATH.format("The Benchmark Set.csv"))
        self.benchmark_stat = self.benchmark_stat[['Instance  Ins.', 'Status  Sta.', 'Variables  Var.', 'Binaries  Bin.', 'Integers  Int.', 'Continuous  Con.', 'Objective  Obj.']]
        self.benchmark_stat.columns = ['instance', 'status', 'variables','binarys', 'integers', 'continuous', 'objective']
    
    def set_data(self, pump_results):
        self.pump_results = pd.DataFrame(pump_results, columns=['instance','objective fp','distance', 'CPU time(s)', 'is feas'])
        print(self.pump_results)
    
    def merge_data(self):
        self.df1 = pd.merge(self.pump_results, self.benchmark_stat, on = "instance")
        obj, obj_fp, is_feas = list(self.df1['objective']), list(self.df1['objective fp']), list(self.df1['is feas'])
        gap = ['--' for i in range(len(obj))]
        for i in range(len(gap)):
            if is_feas[i]:
                gap[i] = 100*(float(obj_fp[i]) - float(obj[i])) / abs(float(obj[i]))

        self.df1['gap(%)'] = gap

    def save_data(self, n_start, n_end):
        ts = datetime.datetime.now()
        ts = ts.strftime('%Y%m%d%H%M%S')
        self.df1.to_csv("./log/{}_{}_{}".format('fp', ts, str(n_start), str(n_end)))