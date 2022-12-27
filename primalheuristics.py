import gurobipy as gp
from gurobipy import GRB
from tqdm import tqdm
from readmodel import ModelData
from scipy.sparse import coo_matrix
import math
import datetime
import random
import numpy as np

class FeasibilityPump():
    def __init__(self, mip_model) -> None:
        self.mip_model = mip_model
        self.vtype = [v.VType for v in self.mip_model.getVars()]
        self.int_var = [i for i in range(len(self.vtype)) if self.vtype[i] == 'I' or self.vtype[i] == 'B']
        self.n_int = len(self.int_var)
        self.lp_model = self.mip_model.relax()
        self.eps = 10**(-6)
        self.model_sense = self.mip_model.ModelSense

    def dist_integer(self, x, x_int):
        return sum([abs(x[i] - x_int[i]) for i in range(len(x)) if i in self.int_var])
    
    def _round(self, x):
        return [round(x[i]) for i in range(len(x))]

    def _round_reverse(self, x_pump, x_int):
        diff = [abs(x_pump[i] - x_int[i]) for i in range(len(x_int))] 
        i = diff.index(max(diff))
        x_pump[i] = 1 - (x_pump[i] - math.floor(x_pump[i])) + math.floor(x_pump[i])
        x_round = self._round(x_pump)
        return x_round
    
    def _random_round(self, x):
        return [math.ceil(x[i]) if random.random() < x[i] else math.floor(x[i]) for i in range(len(x))]

    def build_objective(self, x_int, alpha):
        self.t = self.pump_model.addVars(self.n_int, lb = -GRB.INFINITY, ub = GRB.INFINITY, name = 't')
        v = self.pump_model.getVars()
        for i, idx in enumerate(self.int_var):
            self.pump_model.addConstr(self.t[i] >= v[idx] - x_int[idx])
            self.pump_model.addConstr(self.t[i] >= x_int[idx] - v[idx])
        
        self.obj = self.pump_model.getObjective().copy()
        self.obj_distance = gp.quicksum(self.t[i] for i in range(self.n_int))
        self.pump_model.setObjective((1-alpha)*self.obj_distance + alpha*self.obj)
    
    def get_solution(self):
        v = self.pump_model.getVars()
        return [v[i].x for i in range(len(v))]
    
    def _moniter(self, obj_values):
        self.objective_pump.append(obj_values)
    
    def run(self, MAX_ITER, alpha = 0, beta = 1):
        self.lp_model.setParam("OutputFlag", False)
        self.lp_model.optimize()
        self.obj_lb = self.lp_model.ObjVal

        self.x_lp = [v.x for v in self.lp_model.getVars()]
        self.x_int = self._round(self.x_lp)
        if self.dist_integer(self.x_lp, self.x_int) == 0:
            print("integer solution is obtained")
            return self.x_lp

        self.iter = 0
        ts = datetime.datetime.now()
        
        for self.iter in range(MAX_ITER):
            self.pump_model = self.lp_model.copy()
            self.alpha = alpha*beta**(self.iter - 1)
            self.build_objective(self.x_int, self.alpha)
            self.pump_model.optimize()
            self.pump_model.setParam("OutputFlag", False)
            self.x_pump = self.get_solution()
            
            dist = self.dist_integer(self.x_pump, self.x_int)
            if dist <= self.eps:
                cpu_time = (datetime.datetime.now() - ts).seconds
                print("********  Feasbility Pump  ********")
                print("Solved in {} iterations and {} seconds".format(self.iter, cpu_time))
                print("objective function: {}".format(self.obj.getValue()))
                return self.x_pump, self.obj.getValue(), self.obj_distance.getValue(), cpu_time, True
            # self.x_int = self._round(self.x_pump)
            self.x_int = self._random_round(self.x_pump)

            if self.iter >= 1:
                if self.x_int == self.x_int_last:
                    self.x_int = self._round_reverse(self.x_pump, self.x_int)
            
            self.x_int_last = self.x_int.copy()
        
        cpu_time = (datetime.datetime.now() - ts).seconds
        print("********  Feasbility Pump  ********")
        print("Not Solved in {} iterations and {} seconds".format(self.iter, cpu_time))
        return self.x_pump, self.obj.getValue(), self.obj_distance.getValue(), cpu_time, False
                        
class LocalBranch():
    def __init__(self, mip_model, feas_solution) -> None:
        self.mip_model = mip_model
        self.vtype = [v.VType for v in self.mip_model.getVars()]
        self.bin_var = [i for i in range(len(self.vtype)) if self.vtype[i] == 'B']
        self.n_bin = len(self.bin_var)
        self.lp_model = self.mip_model.relax()
        self.eps = 10**(-6)
        self.feas_solution = feas_solution
        self.model_sense = self.mip_model.ModelSense
    
    def add_constrs_local(self, feas_solution, r):
        v = self.mip_model.getVars()
        self.mip_model.addConstr(gp.quicksum(v[idx]*(1 - feas_solution[idx])+ (1 - v[idx])*feas_solution[idx] for idx in self.bin_var) <= r)
    
    def run(self, r, timelimit):
        self.add_constrs_local(self.feas_solution, r)
        self.mip_model.Params.TIME_LIMIT = timelimit
        ts = datetime.datetime.now()
        self.mip_model.optimize()
        cpu_time = (datetime.datetime.now() - ts).seconds
        return self.mip_model.ObjVal, cpu_time

class LVS():
    def __init__(self, mip_model, feas_solution) -> None:
        self.mip_model = mip_model
        self.vtype = [v.VType for v in self.mip_model.getVars()]
        self.int_var = [i for i in range(len(self.vtype)) if self.vtype[i] == 'I' or self.vtype[i] == 'B']
        self.n_int = len(self.int_var)
        self.lp_model = self.mip_model.relax()
        self.eps = 10**(-6)
        self.feas_solution = feas_solution
        self.model_sense, self.A = self.mip_model.ModelSense, coo_matrix(self.mip_model.getA())

    def get_active_var(self):
        return random.sample(self.int_var, 1)[0]

    def interrelated_vars(self, A, idx):
        interelated_rows = A.row[np.where(A.col==idx)[0]]
        interelated_cols = []
        for row in interelated_rows:
            t = list(A.col[np.where(A.row == row)[0]])
            interelated_cols.extend(t)
        interelated_cols = list(set(interelated_cols))    
        return interelated_cols
    
    def add_constrs_fixed(self, optimized_vars):
        v = self.fixed_model.getVars()
        self.fixed_model.addConstrs((v[i] == self.feas_solution[i]) for i in self.int_var if i not in optimized_vars)
    
    def update_fixed(self, optimized_vars):
        v = self.fixed_model.getVars()
        for idx in optimized_vars:
            self.feas_solution[idx] = v[idx].x 
    
    def run(self, MAX_ITER, timelimit):
        self.iter, ts = 0, datetime.datetime.now()

        while self.iter <= MAX_ITER:
            idx = self.get_active_var()
            self.optimized_vars = self.interrelated_vars(self.A, idx)
            self.fixed_model = self.mip_model.copy()
            self.add_constrs_fixed(self.optimized_vars)
            self.fixed_model.Params.TIME_LIMIT = timelimit
            self.fixed_model.optimize()
            self.update_fixed(self.optimized_vars)
            self.iter += 1
        cpu_time = (datetime.datetime.now() - ts).seconds
        return self.fixed_model.ObjVal, cpu_time 
        
    def write_model(self):
        self.mip_model.write("./model/{}".format())

class RINS():
    def __init__(self) -> None:
        pass

    

        

