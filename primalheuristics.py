import gurobipy as gp
from gurobipy import GRB
from tqdm import tqdm
import math
import datetime
import random

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
            self.x_int = self._round(self.x_pump)

            if self.iter >= 1:
                if self.x_int == self.x_int_last:
                    self.x_int = self._round_reverse(self.x_pump, self.x_int)
            
            self.x_int_last = self.x_int.copy()
        
        cpu_time = (datetime.datetime.now() - ts).seconds
        print("********  Feasbility Pump  ********")
        print("Not Solved in {} iterations and {} seconds".format(self.iter, cpu_time))
        return self.x_pump, self.obj.getValue(), self.obj_distance.getValue(), cpu_time, False
                        
class LocalBranch():
    def __init__(self) -> None:
        pass

class LVS():
    def __init__(self) -> None:
        pass
