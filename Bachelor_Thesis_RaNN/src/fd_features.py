"""固定特征的物理坐标中心差分，不对不连续的分片总解跨界面差分。"""
import numpy as np


class PhysicalTanhFeatures:
    """原物理坐标z=w·x+b；没有前期单位子域映射或坐标平移。"""
    def __init__(self,count,seed,side,weight_range,bias_range=None):
        self.count=count
        rng=np.random.default_rng(np.random.SeedSequence([seed,side,900]))
        self.weights=rng.uniform(-weight_range,weight_range,(count,2))
        bias_range=weight_range if bias_range is None else bias_range
        self.biases=rng.uniform(-bias_range,bias_range,count)

    def values(self,points):return np.tanh(np.asarray(points)@self.weights.T+self.biases)

    def evaluate(self,points):
        phi=self.values(points);first=1-phi**2;second=-2*phi*first
        return phi,first[:,:,None]*self.weights[None,:,:],second*np.sum(self.weights**2,axis=1)


class FiniteDifferenceFeatures:
    def __init__(self,base,h_first=1e-6,h_second=5e-4):
        if h_first<=0 or h_second<=0:raise ValueError("差分步长必须为正")
        self.base=base;self.count=base.count;self.h_first=h_first;self.h_second=h_second

    def evaluate(self,points):
        points=np.asarray(points);phi=self.base.values(points)
        grad=np.empty((*phi.shape,2));lap=np.zeros_like(phi)
        for dim in [0,1]:
            offset=np.zeros_like(points);offset[:,dim]=self.h_first
            grad[:,:,dim]=(self.base.values(points+offset)-self.base.values(points-offset))/(2*self.h_first)
            offset[:,dim]=self.h_second
            lap+=(self.base.values(points+offset)-2*phi+self.base.values(points-offset))/self.h_second**2
        return phi,grad,lap
