"""检查点/方程预算、无重复采样和静态-自适应配对特征。"""
import unittest
import numpy as np
from src.adaptive_sampling import allocate_budget,select_candidates,compare_sampling,sampling_collocation
from src.pde_models import StraightInterfaceProblem


class SamplingTests(unittest.TestCase):
    def test_random_baseline_contains_initial_points(self):
        initial,gamma=sampling_collocation(11,128,32)
        final,final_gamma=sampling_collocation(11,368,128)
        for side in [0,1]:np.testing.assert_array_equal(initial[side],final[side][:128])
        np.testing.assert_array_equal(gamma,final_gamma[:32])

    def test_budget_conservation(self):
        for scores in [(0,0,0),(1,0,0),(.1,.2,100),(1e-10,1e-9,1e-11)]:
            for costs,budget in [((1,1,1),192),((1,1,2),224)]:
                result=allocate_budget(scores,budget,costs=costs)
                self.assertEqual(int(np.dot(result,costs)),budget)
                self.assertTrue(np.all(result>=np.array([16,16,8])))

    def test_sampling_without_replacement(self):
        points=np.arange(100)[:,None];used=np.zeros(100,dtype=bool);rng=np.random.default_rng(11)
        first=select_candidates(points,np.zeros(100),30,rng,used)
        second=select_candidates(points,np.arange(100),30,rng,used)
        self.assertEqual(len(set(first.ravel())|set(second.ravel())),60)
        with self.assertRaises(ValueError):select_candidates(points,np.zeros(100),41,rng,used)

    def test_shared_features_and_scalar_budget(self):
        model=StraightInterfaceProblem(10,1,"jumps")
        a,_,_=compare_sampling(model,"B",11,"equations",count=12,rounds=1)
        d,trace,_=compare_sampling(model,"D",11,"equations",count=12,rounds=1)
        self.assertEqual(a.diagnostics["n_equations"],d.diagnostics["n_equations"])
        for side in [0,1]:np.testing.assert_array_equal(a.features[side].weights,d.features[side].weights)
        self.assertEqual(trace[-1]["add_left"]+trace[-1]["add_right"]+2*trace[-1]["add_interface"],224)


if __name__=="__main__":unittest.main()
