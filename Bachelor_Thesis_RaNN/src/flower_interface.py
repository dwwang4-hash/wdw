"""Li-Wang预印本Example4.1花形模型与物理一致的强形式系统。"""
from dataclasses import dataclass
from time import perf_counter
import numpy as np
from scipy.integrate import cumulative_trapezoid
from .fd_features import PhysicalTanhFeatures,FiniteDifferenceFeatures
from .least_squares import solve_least_squares


@dataclass(frozen=True)
class FlowerProblem:
    beta_inner: float=1.
    beta_outer: float=10.

    @property
    def center(self):return .02*np.sqrt(5)

    def classify(self,points):
        delta=np.asarray(points)-self.center
        theta=np.arctan2(delta[:,1],delta[:,0])
        radius=.4+.2*np.sin(20*theta)
        return np.linalg.norm(delta,axis=1)<radius

    def geometry(self,theta):
        radius=.4+.2*np.sin(20*theta);dr=4*np.cos(20*theta)
        cosine=np.cos(theta);sine=np.sin(theta)
        points=self.center+radius[:,None]*np.column_stack((cosine,sine))
        tangent=np.column_stack((dr*cosine-radius*sine,dr*sine+radius*cosine))
        normal=np.column_stack((tangent[:,1],-tangent[:,0]))/np.linalg.norm(tangent,axis=1)[:,None]
        return points,normal,tangent

    def data(self,points,side):
        x,y=np.asarray(points).T
        if side==0:
            exponential=np.exp(x*y);u=exponential/self.beta_inner
            forcing=-(x*x+y*y)*exponential
            gradient=np.column_stack((y*u,x*u))
        elif side==1:
            u=np.sin(x)*np.sin(y)/self.beta_outer
            forcing=2*np.sin(x)*np.sin(y)
            gradient=np.column_stack((np.cos(x)*np.sin(y),np.sin(x)*np.cos(y)))/self.beta_outer
        else:raise ValueError("side只能为0或1")
        return u,forcing,gradient

    def jumps(self,points,normals):
        u1,_,g1=self.data(points,0);u2,_,g2=self.data(points,1)
        return u2-u1,np.sum((self.beta_outer*g2-self.beta_inner*g1)*normals,axis=1)


def flower_collocation(problem,total,seed,interface_sampling="theta"):
    if total%20:raise ValueError("当前总点数须为20的倍数，以保持3:1:1和四边等点数")
    rng=np.random.default_rng(np.random.SeedSequence([seed,910]))
    points=rng.uniform(-1,1,(3*total//5,2));mask=problem.classify(points)
    uniform=rng.uniform(0,1,total//5)
    if interface_sampling=="theta":theta=2*np.pi*uniform
    elif interface_sampling=="arclength":
        grid=np.linspace(0,2*np.pi,65537)
        speed=np.sqrt((.4+.2*np.sin(20*grid))**2+(4*np.cos(20*grid))**2)
        arc=cumulative_trapezoid(speed,grid,initial=0);theta=np.interp(uniform*arc[-1],arc,grid)
    else:raise ValueError("未知界面采样")
    interface,normals,_=problem.geometry(theta)
    t=rng.uniform(-1,1,total//20)
    boundary=np.vstack((np.column_stack((t,np.full_like(t,-1))),np.column_stack((t,np.ones_like(t))),
                        np.column_stack((np.full_like(t,-1),t)),np.column_stack((np.ones_like(t),t))))
    return [points[mask],points[~mask]],interface,normals,boundary


def solve_flower(count,total,seed,derivative="fd",h_second=5e-4,rcond=1e-12,initialization="per_domain",interface_sampling="theta"):
    start=perf_counter();problem=FlowerProblem()
    ranges=[1.6,.7]
    bases=[PhysicalTanhFeatures(count,seed,i,ranges[i]) if initialization=="per_domain" else PhysicalTanhFeatures(count,seed,i,1.6,.7) for i in [0,1]]
    features=[FiniteDifferenceFeatures(b,h_second=h_second) for b in bases] if derivative=="fd" else bases
    interior,interface,normals,boundary=flower_collocation(problem,total,seed,interface_sampling)
    blocks=[];targets=[]
    for side,beta in [(0,problem.beta_inner),(1,problem.beta_outer)]:
        _,_,lap=features[side].evaluate(interior[side]);a=np.zeros((len(lap),2*count));a[:,side*count:(side+1)*count]=-beta*lap
        blocks.append(a);targets.append(problem.data(interior[side],side)[1])
    p1,g1,_=features[0].evaluate(interface);p2,g2,_=features[1].evaluate(interface)
    gu,gq=problem.jumps(interface,normals)
    blocks.append(50*np.hstack((-p1,p2)));targets.append(50*gu)
    flux=np.hstack((-problem.beta_inner*np.einsum('njk,nk->nj',g1,normals),problem.beta_outer*np.einsum('njk,nk->nj',g2,normals)))
    blocks.append(50*flux);targets.append(50*gq)
    boundary_phi=bases[1].values(boundary)
    blocks.append(50*np.hstack((np.zeros_like(boundary_phi),boundary_phi)));targets.append(50*problem.data(boundary,1)[0])
    matrix=np.vstack(blocks);rhs=np.concatenate(targets)
    coeff,diagnostics=solve_least_squares(matrix,rhs,rcond)
    diagnostics.update({'total_seconds':perf_counter()-start,'n_points':total,'n_equations':total+len(interface),
                        'n_inner':len(interior[0]),'n_outer':len(interior[1])})
    return problem,bases,coeff,diagnostics


def flower_metrics(problem,bases,coeff,quadrature=100):
    from numpy.polynomial.legendre import leggauss
    from .metrics import rms
    count=bases[0].count
    axis,weights=leggauss(quadrature);x,y=np.meshgrid(axis,axis);wx,wy=np.meshgrid(weights,weights)
    points=np.column_stack((x.ravel(),y.ravel()));integration=(wx*wy).ravel();mask=problem.classify(points)
    exact=np.empty(len(points));prediction=np.empty(len(points));residual=np.empty(len(points))
    for side,chosen in [(0,mask),(1,~mask)]:
        phi,_,lap=bases[side].evaluate(points[chosen]);c=coeff[side*count:(side+1)*count]
        exact[chosen],forcing,_=problem.data(points[chosen],side);prediction[chosen]=phi@c
        residual[chosen]=-[problem.beta_inner,problem.beta_outer][side]*lap@c-forcing
    relative=np.sqrt(np.sum(integration*(prediction-exact)**2)/np.sum(integration*exact**2))
    gamma,normals,_=problem.geometry((np.arange(2048)+.5)*2*np.pi/2048)
    p1,g1,_=bases[0].evaluate(gamma);p2,g2,_=bases[1].evaluate(gamma);gu,gq=problem.jumps(gamma,normals)
    value=p2@coeff[count:]-p1@coeff[:count]-gu
    flux=problem.beta_outer*np.einsum('njk,j,nk->n',g2,coeff[count:],normals)-problem.beta_inner*np.einsum('njk,j,nk->n',g1,coeff[:count],normals)-gq
    return {'relative_l2':float(relative),'max_abs':float(np.max(np.abs(prediction-exact))),
            'validation_pde_rms':float(np.sqrt(np.sum(integration*residual**2)/4)),
            'interface_value_rms':rms(value),'interface_flux_rms':rms(flux)}
