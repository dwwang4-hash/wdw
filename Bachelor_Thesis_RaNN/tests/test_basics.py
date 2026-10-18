"""用 unittest 运行，无额外测试依赖。检验公式、符号与独立离散性质。"""
import unittest
import numpy as np
from src.pde_models import poisson_exact, poisson_forcing, interface_data
from src.baseline_fdm import solve_poisson
from src.random_features import TanhFeatures
from src.least_squares import solve_least_squares


class BasicTests(unittest.TestCase):
    def test_manufactured_poisson(self):
        points=np.array([[.21,.34],[.43,.67],[.71,.23]])
        step=1e-4
        lap=np.zeros(len(points))
        for k in range(2):
            shift=np.zeros_like(points); shift[:,k]=step
            lap += (poisson_exact(points+shift)-2*poisson_exact(points)+poisson_exact(points-shift))/step**2
        np.testing.assert_allclose(-lap,poisson_forcing(points),rtol=2e-7)
        np.testing.assert_allclose(poisson_exact([[0,.2],[1,.6],[.2,0],[.4,1]]),0,atol=1e-15)

    def test_fdm_discrete_eigenvalue_and_order(self):
        errs=[]
        for n in [15,31,63]:
            points,u,h,_,res=solve_poisson(n)
            # 正弦恰为离散特征向量；该表达式独立验证右端项和矩阵符号。
            lam=8/h**2*np.sin(np.pi*h/2)**2
            exact=poisson_exact(points)
            np.testing.assert_allclose(u,(2*np.pi**2/lam)*exact,rtol=2e-12,atol=2e-14)
            self.assertLess(res,1e-11)
            errs.append(np.linalg.norm(u-exact)/np.linalg.norm(exact))
        self.assertTrue(all(3.9<a/b<4.1 for a,b in zip(errs[:-1],errs[1:])))

    def test_tanh_derivatives(self):
        features=TanhFeatures(7,11)
        p=np.array([[.31,.43],[.63,.72]])
        values,grad,lap=features.evaluate(p)
        step=1e-4; numeric_lap=np.zeros_like(values)
        for k in range(2):
            shift=np.zeros_like(p); shift[:,k]=step
            plus=features.evaluate(p+shift)[0]; minus=features.evaluate(p-shift)[0]
            np.testing.assert_allclose((plus-minus)/(2*step),grad[:,:,k],rtol=2e-6,atol=2e-8)
            numeric_lap += (plus-2*values+minus)/step**2
        np.testing.assert_allclose(numeric_lap,lap,rtol=2e-5,atol=1e-7)

    def test_interface_manufacturing(self):
        y=np.linspace(0,1,31); p=np.column_stack((np.full_like(y,.5),y))
        u1,_,ux1=interface_data(p,1); u2,_,ux2=interface_data(p,100)
        np.testing.assert_allclose(u2-u1,0,atol=1e-14)
        np.testing.assert_allclose(100*ux2-ux1,0,atol=5e-14)
        for beta in [1,100]:
            b=np.array([[0,.31],[1,.62],[.2,0],[.7,1]])
            np.testing.assert_allclose(interface_data(b,beta)[0],0,atol=1e-14)
            q=np.array([[.21,.37],[.72,.63]])
            u,f,_=interface_data(q,beta); step=1e-4; lap=np.zeros(len(q))
            for k in range(2):
                shift=np.zeros_like(q); shift[:,k]=step
                lap+=(interface_data(q+shift,beta)[0]-2*u+interface_data(q-shift,beta)[0])/step**2
            np.testing.assert_allclose(-beta*lap,f,rtol=5e-7)

    def test_svd_known_solution_and_deficiency(self):
        a=np.array([[1.,0],[0,1],[1,1]])
        c,info=solve_least_squares(a,a@np.array([2.,-3.]))
        np.testing.assert_allclose(c,[2,-3],atol=1e-14); self.assertEqual(info["rank"],2)
        c,info=solve_least_squares(np.ones((4,2)),np.ones(4))
        np.testing.assert_allclose(c,[.5,.5],atol=1e-14); self.assertEqual(info["rank"],1)


if __name__ == "__main__":
    unittest.main()
