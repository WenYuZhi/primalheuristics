
import gurobipy as gp
import os

BENCHMARK_PATH = "./" + "benchmark/MIPLIB2017/"

class ModelData:
    def __init__(self) -> None:
        self.file_info = [(f, os.path.getsize(BENCHMARK_PATH + f)) for f in os.listdir(BENCHMARK_PATH) if ".mps" in f]
        self.file_info = sorted(self.file_info, key = lambda x: x[1])
        
    def load(self, n_start, n_end, presolve = False):
        self.model = []
        self.read_file = [self.file_info[i][0] for i in range(n_start, n_end)]
        for f in self.read_file:
            self.m = gp.read(BENCHMARK_PATH + f)
            if presolve:
                self.m = self.m.presolve()
                self.m.update()
            self.model.append(self.m)
        self.read_file = [f.replace(".mps","") for f in self.read_file]
        return self.model, self.read_file
    
    def read_model(self, file_name):
        return gp.read(BENCHMARK_PATH + file_name)
