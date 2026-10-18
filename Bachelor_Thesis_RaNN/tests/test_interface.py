"""非零跳跃、β通量、局部链式法则和矩阵组装的独立核查。"""
import unittest
import numpy as np
from src.pde_models import StraightInterfaceProblem
from src.random_features import LocalTanhFeatures
from src.local_rann import assemble, random_collocation, outer_boundary, solve_local, validation_metrics


class AnalyticBasis:
    """用可精确表达制造解的基函数核查组装，不依赖随机近似能力。"""
    count=3

    def evaluate(self, points):
        x,y=np.asarray(points).T
        q=x*(1-x); p=q*(x-.5); sy=np.sin(np.pi*y); cy=np.cos(np.pi*y)
        bx=np.column_stack((np.sin(np.pi*x),q,p))
        dx=np.column_stack((np.pi*np.cos(np.pi*x),1-2*x,-3*x*x+3*x-.5))
        ddx=np.column_stack((-np.pi**2*np.sin(np.pi*x),np.full_like(x,-2),3-6*x))
        phi=bx*sy[:,None]
        grad=np.stack((dx*sy[:,None],np.pi*bx*cy[:,None]),axis=2)
        return phi,grad,(ddx-np.pi**2*bx)*sy[:,None]


class InterfaceTests(unittest.TestCase):
    def test_nonzero_jump_manufacturing(self):
        model=StraightInterfaceProblem(100,1,"jumps")
        p=np.array([[.5,.25],[.5,.6]])
        u1,_,g1=model.data(p,0);u2,_,g2=model.data(p,1)
        gu,gq=model.jumps(p)
        np.testing.assert_allclose(u2-u1,gu,atol=1e-14)
        np.testing.assert_allclose(g2[:,0]-100*g1[:,0],gq,atol=5e-14)
        self.assertGreater(np.min(np.abs(gu)),.05)
        self.assertGreater(np.min(np.abs(gq)),.03)
        for side in [0,1]:
            points=np.array([[.21+.5*side,.32],[.13+.5*side,.71]])
            u,f,_=model.data(points,side);h=1e-4;lap=np.zeros(len(points))
            for dim in [0,1]:
                shift=np.zeros_like(points);shift[:,dim]=h
                lap+=(model.data(points+shift,side)[0]-2*u+model.data(points-shift,side)[0])/h**2
            np.testing.assert_allclose(-model.parameters(side)[0]*lap,f,rtol=5e-7)
            np.testing.assert_allclose(model.data(outer_boundary()[side],side)[0],0,atol=1e-14)

    def test_local_chain_rule(self):
        p=np.array([[.2,.3],[.32,.71]])
        features=LocalTanhFeatures(9,23,0)
        phi,grad,lap=features.evaluate(p);h=1e-4;nlap=np.zeros_like(phi)
        for dim in [0,1]:
            shift=np.zeros_like(p);shift[:,dim]=h
            plus=features.evaluate(p+shift)[0];minus=features.evaluate(p-shift)[0]
            np.testing.assert_allclose((plus-minus)/(2*h),grad[:,:,dim],rtol=3e-6,atol=3e-8)
            nlap+=(plus-2*phi+minus)/h**2
        np.testing.assert_allclose(nlap,lap,rtol=3e-5,atol=2e-7)

    def test_manufactured_exact_system(self):
        features=[AnalyticBasis(),AnalyticBasis()]
        interior,interface=random_collocation(11,60,21)
        boundary=outer_boundary(13)
        for scaling in ["raw","balanced"]:
            for betas in [(1,100),(100,1)]:
                problem=StraightInterfaceProblem(*betas,"jumps")
                exact_coeff=np.concatenate([[1,a,t/beta] for beta,a,t in [problem.parameters(i) for i in [0,1]]])
                matrix,rhs=assemble(problem,features,interior,interface,boundary,scaling)
                np.testing.assert_allclose(matrix@exact_coeff,rhs,rtol=1e-12,atol=2e-12)
                sol=solve_local(problem,interior=interior,interface=interface,features=features,boundary=boundary,scaling=scaling)
                np.testing.assert_allclose(np.concatenate(sol.coefficients),exact_coeff,rtol=1e-10,atol=2e-12)
                self.assertLess(validation_metrics(sol)["relative_l2"],1e-11)

    def test_poisson_limit(self):
        from src.pde_models import poisson_exact,poisson_forcing
        p=np.array([[.2,.3],[.7,.6]])
        model=StraightInterfaceProblem(1,1,"poisson")
        np.testing.assert_allclose(model.data(p,0)[0],poisson_exact(p))
        np.testing.assert_allclose(model.data(p,1)[1],poisson_forcing(p))


if __name__=="__main__":unittest.main()
