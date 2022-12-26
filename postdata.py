import pandas as pd
import datetime

BENCHMARK_PATH = "./" + "benchmark/MIPLIB2017/{}"

class PostResults():
    def __init__(self) -> None:
        self.benchmark_stat = pd.read_csv(BENCHMARK_PATH.format("The Benchmark Set.csv"))
        self.benchmark_stat = self.benchmark_stat[['Instance  Ins.', 'Status  Sta.', 'Variables  Var.', 'Binaries  Bin.', 'Integers  Int.', 'Continuous  Con.', 'Objective  Obj.']]
        self.benchmark_stat.columns = ['instance', 'status', 'variables','binarys', 'integers', 'continuous', 'objective']
    
    def set_data(self, pump_results, local_branch_results):
        self.pump_results = pd.DataFrame(pump_results, columns=['instance','objective fp','distance', 'CPU time(s)', 'is feas'])
        self.local_branch_results = pd.DataFrame(local_branch_results, columns=['instance', 'objective local', 'CPU time(s)'])
    
    def merge_data(self):
        self._merge_data1()
        self._merge_data2()
    
    def _merge_data1(self):
        self.df1 = pd.merge(self.pump_results, self.benchmark_stat, on = "instance")
        obj, obj_fp, is_feas = list(self.df1['objective']), list(self.df1['objective fp']), list(self.df1['is feas'])
        gap = ['--' for i in range(len(obj))]
        for i in range(len(gap)):
            if is_feas[i]:
                gap[i] = 100*(float(obj_fp[i]) - float(obj[i])) / abs(float(obj[i]))

        self.df1['gap(%)'] = gap
        self.df1 = self.df1[['instance', 'objective fp', 'objective', 'gap(%)', 'distance', 'CPU time(s)', 'is feas', 'status', 'variables','binarys', 'integers', 'continuous']]
    
    def _merge_data2(self):
        self.df2 = pd.merge(self.local_branch_results, self.benchmark_stat, on = "instance")
        obj, obj_local = list(self.df2['objective']), list(self.df2['objective local'])
        gap = [100*(float(obj_local[i]) - float(obj[i])) / abs(float(obj[i])) for i in range(len(obj))]
        self.df2['gap(%)'] = gap
        self.df2 = self.df2[['instance', 'objective local', 'objective', 'gap(%)', 'CPU time(s)', 'status', 'variables','binarys', 'integers', 'continuous']]

    def save_data(self, n_start, n_end):
        ts = datetime.datetime.now()
        ts = ts.strftime('%Y%m%d%H%M%S')
        self.df1.to_csv("./log/{}_{}_{}_{}.csv".format('FP', ts, str(n_start), str(n_end)))
        self.df2.to_csv("./log/{}_{}_{}_{}.csv".format('LocalBranch', ts, str(n_start), str(n_end)))