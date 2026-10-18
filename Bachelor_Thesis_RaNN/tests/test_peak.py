"""峰值制造解的一致性；特意检查β不同导致的新增通量跳跃。"""
import unittest
import numpy as np
from src.pde_models import PeakInterfaceProblem,StraightInterfaceProblem
from src.local_rann import outer_boundary


class PeakTests(unittest.TestCase):
    def test_peak_derivatives_and_pde(self):
        p=np.array([[.43,.51],[.52,.57],[.33,.65]])
        for width in [.12,.06]:
            model=PeakInterfaceProblem(1000,1,"jumps",width=width)
            value,gradient,lap=model.bump(p);step=1e-5;numeric=np.zeros(len(p))
            for dim in [0,1]:
                shift=np.zeros_like(p);shift[:,dim]=step
                plus=model.bump(p+shift)[0];minus=model.bump(p-shift)[0]
                np.testing.assert_allclose((plus-minus)/(2*step),gradient[:,dim],rtol=2e-6,atol=1e-7)
                numeric+=(plus-2*value+minus)/step**2
            np.testing.assert_allclose(numeric,lap,rtol=3e-6,atol=2e-4)
            for side in [0,1]:
                u,f,_=model.data(p,side);numeric=np.zeros(len(p))
                for dim in [0,1]:
                    shift=np.zeros_like(p);shift[:,dim]=step
                    numeric+=(model.data(p+shift,side)[0]-2*u+model.data(p-shift,side)[0])/step**2
                np.testing.assert_allclose(-model.parameters(side)[0]*numeric,f,rtol=4e-6,atol=.01)

    def test_peak_interface_and_boundary(self):
        p=np.column_stack((np.full(41,.5),np.linspace(.01,.99,41)))
        for betas in [(1,1),(1000,1),(1,1000)]:
            model=PeakInterfaceProblem(*betas,"jumps",width=.06)
            u1,_,grad1=model.data(p,0);u2,_,grad2=model.data(p,1);gu,gq=model.jumps(p)
            np.testing.assert_allclose(u2-u1,gu,atol=1e-14)
            np.testing.assert_allclose(betas[1]*grad2[:,0]-betas[0]*grad1[:,0],gq,rtol=1e-12,atol=1e-11)
            for side in [0,1]:np.testing.assert_allclose(model.data(outer_boundary()[side],side)[0],0,atol=1e-14)
            if betas[0]!=betas[1]:
                old=StraightInterfaceProblem(*betas,"jumps").jumps(p)[1]
                self.assertGreater(np.max(np.abs(gq-old)),100)


if __name__=="__main__":unittest.main()
