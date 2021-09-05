# gurobi_bug
Gurobi fails to give optimal, order of constraints affects solution optimality.  Tested for Gurobi 8.1.1, Gurobi 9.1.2.

bug 1. with different order of constraints, gurobi gives solutions of different objective value.

bug 2. with more constraints, we expect worse solution, but gurobi gives better solution.


MacBook-Pro:$ python gurobi-bug.py 
--------
Academic license - for non-commercial use only
('obj=', 6.0)
('obj=', 7.0)
('obj=', 6.0)
('obj=', 7.0)
--------
('obj=', 7.0)
('obj=', 6.0)
--------
