import unittest
import numpy as np
from src.fd_features import PhysicalTanhFeatures,FiniteDifferenceFeatures
from src.flower_interface import FlowerProblem,flower_collocation


class FDFlowerTests(unittest.TestCase):
    def test_fd_order_and_gradient(self):
        base=PhysicalTanhFeatures(9,11,0,1.6,.7);points=np.array([[.21,.32],[-.32,.13]])
        exact,gradient,lap=base.evaluate(points)
        coarse=FiniteDifferenceFeatures(base,h_second=.01).evaluate(points)
        fine=FiniteDifferenceFeatures(base,h_second=.005).evaluate(points)
        ratio=np.linalg.norm(coarse[2]-lap)/np.linalg.norm(fine[2]-lap)
        self.assertTrue(3.8<ratio<4.2)
        np.testing.assert_allclose(fine[1],gradient,rtol=1e-7,atol=2e-10)
        np.testing.assert_array_equal(fine[0],exact)

    def test_flower_normal_and_model(self):
        model=FlowerProblem();theta=np.linspace(0,2*np.pi,103,endpoint=False)
        gamma,normal,tangent=model.geometry(theta)
        np.testing.assert_allclose(np.sum(normal*tangent,axis=1),0,atol=1e-14)
        np.testing.assert_allclose(np.linalg.norm(normal,axis=1),1,atol=1e-14)
        self.assertTrue(np.all(np.sum(normal*(gamma-model.center),axis=1)>0))
        p=np.array([[.13,.27],[-.34,.51]]);h=1e-4
        for side,beta in [(0,1),(1,10)]:
            u,f,_=model.data(p,side);lap=np.zeros(len(p))
            for dim in [0,1]:
                shift=np.zeros_like(p);shift[:,dim]=h
                lap+=(model.data(p+shift,side)[0]-2*u+model.data(p-shift,side)[0])/h**2
            np.testing.assert_allclose(-beta*lap,f,rtol=2e-6,atol=2e-7)
        self.assertTrue(model.classify([[model.center,model.center]])[0])
        self.assertFalse(np.any(model.classify([[1,.2],[-1,.3],[.2,1],[.3,-1]])))

    def test_collocation_counts(self):
        model=FlowerProblem()
        for sampling in ['theta','arclength']:
            interior,gamma,normals,boundary=flower_collocation(model,1000,11,sampling)
            self.assertEqual(sum(map(len,interior)),600);self.assertEqual(len(gamma),200);self.assertEqual(len(boundary),200)
            gu,gq=model.jumps(gamma,normals);u1,_,g1=model.data(gamma,0);u2,_,g2=model.data(gamma,1)
            np.testing.assert_allclose(u2-u1,gu)
            np.testing.assert_allclose(np.sum((10*g2-g1)*normals,axis=1),gq)


if __name__=='__main__':unittest.main()
