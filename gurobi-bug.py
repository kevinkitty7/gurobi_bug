#!/usr/bin/python
# -*- coding: utf-8 -*-
import time 
from gurobipy import *

#------------------------------------------
def countindex(): # for gurobi, no. constraints
	global _cnt 
	_cnt = _cnt + 1
	return _cnt

#------------------------------------------
def ilp_1(force=[], verbose=False): #opt : ilp formulate by tardy; force is on-time jobs
	global y, v, _cnt, opt, sch
	_cnt = 0 #no. of constr.
	m = Model("mip")
	m.params.outputFlag = 0
	y = {} # y[j, i] job j is at position i
	v = {} # v[j] = 0: j is tardy
	for j in range(n):
		v[j] = m.addVar(vtype=GRB.BINARY, name="v_%d" % (j))
		for i in range(n):
			y[j, i] = m.addVar(vtype=GRB.BINARY, name="y_%d_%d" % (j,i))	
	m.update()

	for j in set(force):
		m.addConstr( v[j] == 1, "c_%d" % (countindex()))
	m.update()

	for j in range(n):
		m.addConstr(quicksum([y[j,i] for i in range(n)]) == 1, "c_%d" % (countindex()))
		m.addConstr(quicksum([y[i,j] for i in range(n)]) == 1, "c_%d" % (countindex()))
	for t, j in enumerate(c):
		m.addConstr(y[j, t + k[t] ] == 1, "c_%d" % (countindex()))
	for j1 in range(n):
		for j in range(j1):
			if j in c or j1 in c: continue
			if p[j1] <= p[j]: #j<j1
				m.addConstr( v[j] <= v[j1], "c_%d" % (countindex()))

	# greedy for Lmax
	M = sum(p)
	T = sum(p)
	for i in range(n)[::-1]:
		#alg: for d[j] >= T, find max p[j] at [i]; if j is tardy, d[j]=\infty
		#compare [i] with previous [i1]
		for i1 in range(i):
			#avoid violation: pj1 > pj and d[j1] >= T
			for j in range(n): # at [i]
				if j in c: continue # compute special job later
				for j1 in range(n): # at[i1]
					if j1 in c: continue # compute special job later
					if j==j1: continue
					if p[j1] > p[j]:
						# j1 cannot be late: as otherwise j1 can be at position i
						m.addConstr( y[j1,i1] + y[j,i] + 1 - v[j1] <= 2, "c_%d" % (countindex()))
						# j1 on time: then d[j1] < T.
						m.addConstr( (y[j1,i1] + y[j,i] + v[j1] - 3) * d[j1] + d[j1] <= T-1, "c_%d" % (countindex()))
		# on-time constr.
		for j in range(n): # j at [i]
			m.addConstr( T - (2 - (y[j,i] + v[j])) * (M - d[j]) <= d[j], "c_%d" % (countindex()))

		pj = quicksum([y[j,i] * p[j] for j in range(n)])
		T = T - pj

	for j in set(force):
		m.addConstr( v[j] == 1, "c_%d" % (countindex()))
	m.update()

	expr = quicksum([v[j] for j in range(n)])
	m.setObjective(expr, GRB.MAXIMIZE)#MINIMIZE

	m.optimize()
	####m.computeIIS()
	#m.write('mymodel.lp')
	if m.status != GRB.status.OPTIMAL:
		if verbose: print('infeasible!')
		opt = 0
		return False, []
	obj = m.objVal
	opt = round(obj)
	print('..',obj)
	#------------------------------------------
	sch = []
	for i in range(n):  
		li = []
		for j in range(n):
			if y[j,i].X >= 0.001: 
				sch.append(j)
	on_c, on_all = [], []
	for idx,j in enumerate(c):
		if v[j].X >= 0.001:
			on_c.append(idx)
	for j in range(n):
		if v[j].X >= 0.001:
			on_all.append(j)
	if verbose:
		print('opt:' , (opt, on_all))
		print_on(sch)
	return True, on_c

#------------------------------------------
def ilp(constr_before=False, force=[]):
	#return ilp_1(force=force)

	global _cnt
	_cnt = 0 #no. of constr.
	m = Model("mip")
	m.params.outputFlag = 0
	y = {} # y[j, i] = 1:  j is at position i
	v = {} # v[j] = 1: j is selected, to be maximized.
	# --- add var -------------
	for j in range(n):
		v[j] = m.addVar(vtype=GRB.BINARY, name="v_%d" % (j))
		for i in range(n):
			y[j, i] = m.addVar(vtype=GRB.BINARY, name="y_%d_%d" % (j,i))

	# --- add constr -------------

	#-# extra constraints. {bug disapper when add it early.} {force} {gurobi bug: more constr. better solution.}
	if constr_before:
		for j in force: m.addConstr( v[j] == 1, "c_%d" % (countindex()))
	m.update()

	#-# constraints
	for j in range(n):
		m.addConstr(quicksum([y[j,i] for i in range(n)]) == 1, "1c_%d" % (countindex()))
		m.addConstr(quicksum([y[i,j] for i in range(n)]) == 1, "1*c_%d" % (countindex()))
	for t, j in enumerate(c):
		m.addConstr(y[j, t + k[t] ] == 1, "2c_%d" % (countindex()))
	for j1 in range(n):
		for j in range(j1):
			if j in c or j1 in c: continue
			if p[j1] <= p[j]: # j < j1, dominance
				m.addConstr( v[j] <= v[j1], "3c_%d" % (countindex()))
	
	# greedy
	M = sum(p)
	T = sum(p)
	for i in range(n)[::-1]:
		# alg: for all d[j] >= T, find max p[j] => [i]; {if j is not selected, d[j]=infty}
		for i1 in range(i): # compare [i] with previous [i1]
			for j in range(n): # j at [i]
				if j in c: continue
				for j1 in range(n): # j1 at[i1]
					if j1 in c: continue
					if j == j1: continue
					## violation to void: pj1 > pj and d[j1] >= T
					if p[j1] > p[j]: # max should be j1 not j.
						# j1 cannot be late: as otherwise j1 can be at position i
						m.addConstr( y[j1,i1] + y[j,i] + 1 - v[j1] <= 2, "4c_%d" % (countindex()))
						# j1 on time: then d[j1] < T.
						m.addConstr( (y[j1,i1] + y[j,i] + v[j1] - 3) * d[j1] + d[j1] <= T-1, "4*c_%d" % (countindex()))
		# on-time constr.
		for j in range(n): # j at [i]
			m.addConstr( T - (2 - (y[j,i] + v[j])) * (M - d[j]) <= d[j], "5c_%d" % (countindex()))

		pj = quicksum([y[j,i] * p[j] for j in range(n)])
		T = T - pj


	#-# extra constraints. {bug disapper when add it early.} {force} {gurobi bug: more constr. better solution.}
	if not constr_before:
		for j in force: m.addConstr( v[j] == 1, "c_%d" % (countindex()))
	m.update()


	#-# max selected j 
	expr = quicksum([v[j] for j in range(n)])
	m.setObjective(expr, GRB.MAXIMIZE)

	m.optimize()
	####m.computeIIS()
	#m.write('mymodel.lp')
	if m.status != GRB.status.OPTIMAL:
		print('infeasible!')
		return 0
	obj = m.objVal
	print('obj=', obj)
	return obj
#------------------------------------------
def kT_test_0():
	global n, p, d, c, k
	##gurobi bug: reason {order of constr.}: 
	##force=c does not give optimal opt=7.
	c,k,p,d=([0], [4], [1, 2, 3, 2, 1, 3, 2, 1, 1], [9, 1, 1, 2, 4, 6, 8, 10, 12])
	n = len(p)

	print('c,k,p,d=' + str((list(c),list(k),list(p),list(d))))

	print('--------')
	ilp(force= c, constr_before=False) 	# this give opt=6
	ilp(force= c, constr_before=True) 	# this give opt=7
	ilp(force= c, constr_before=False) 	# this give opt=6
	ilp(force= c, constr_before=True) 	# this give opt=7
	print('--------')
	# 'force' now has more constraints, expected worse, but gurobi gives better solution.
	for bf in [True,False]:
		print("+++------- add constr.---" + ("in the begining" if bf else "at the end"))
		ilp(force= c + [3, 4, 5, 6, 7, 8], constr_before=bf)
		ilp(force= c, constr_before=bf)
	print('-----++++')

	
	for bf in [True,False]:
		print("------- add constr.---" + ("in the begining" if bf else "at the end"))
		for nc in range(2):
			for t in range(9,13):  # expect larger t gives larger objective.
				j = c[0]
				d[j] = t
				#print('t=',t)
				if nc==0: 
					ilp(force=c, constr_before=bf)
				else: # bug: more constraints lead to better solution!
					ilp(force= c + [3, 4, 5, 6, 7, 8], constr_before=bf)
			print('>>>')

#------------------------------------------
if __name__ == "__main__":
	kT_test_0()
