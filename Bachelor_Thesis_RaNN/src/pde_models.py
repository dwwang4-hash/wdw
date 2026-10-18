"""制造解与数据；输入点数组的形状统一为 (n, 2)。"""
import numpy as np
from dataclasses import dataclass


def poisson_exact(points):
    x, y = np.asarray(points).T
    return np.sin(np.pi * x) * np.sin(np.pi * y)


def poisson_forcing(points):
    # -Δ[sin(πx)sin(πy)] = 2π² sin(πx)sin(πy)。
    return 2 * np.pi**2 * poisson_exact(points)


def interface_data(points, beta):
    """直线界面制造解，须分别传入每侧的正常数 beta。

    u_i=[sin(πx)+p(x)/β_i]sin(πy), p=x(1-x)(x-1/2)。
    法向从左指向右；[u]=u2-u1=0，[β∂_x u]=0。
    返回 u, f, ∂_x u；外边界全为零。
    """
    if beta <= 0:
        raise ValueError("扩散系数必须为正")
    x, y = np.asarray(points).T
    p = x * (1 - x) * (x - 0.5)
    dp = -3 * x**2 + 3 * x - 0.5
    ddp = 3 - 6 * x
    sy = np.sin(np.pi * y)
    u = (np.sin(np.pi * x) + p / beta) * sy
    f = (2 * beta * np.pi**2 * np.sin(np.pi * x) - ddp + np.pi**2 * p) * sy
    ux = (np.pi * np.cos(np.pi * x) + dp / beta) * sy
    return u, f, ux


@dataclass(frozen=True)
class StraightInterfaceProblem:
    """法向(1,0)，跳跃右减左；分片光滑且外边界全零。

    u_i=[sin(πx)+a_i q(x)+t_i p(x)/β_i] sin(πy)。
    q=x(1-x), p=q(x)(x-1/2)。非零跳跃模型在右侧取a=.4,t=1.2。
    """
    beta_left: float = 1.0
    beta_right: float = 10.0
    variant: str = "continuous"

    def __post_init__(self):
        if min(self.beta_left, self.beta_right) <= 0:
            raise ValueError("β必须为正")
        if self.variant not in {"poisson", "continuous", "jumps"}:
            raise ValueError("未知制造解模型")

    def parameters(self, side):
        if side not in {0, 1}:
            raise ValueError("side必须为0（左）或1（右）")
        beta = [self.beta_left, self.beta_right][side]
        a = .4 if self.variant == "jumps" and side == 1 else 0.0
        t = 0.0 if self.variant == "poisson" else (1.2 if self.variant == "jumps" and side == 1 else 1.0)
        return beta, a, t

    def data(self, points, side):
        beta, a, t = self.parameters(side)
        x, y = np.asarray(points).T
        q = x*(1-x); p = q*(x-.5)
        sy = np.sin(np.pi*y)
        base = np.sin(np.pi*x)+a*q+t*p/beta
        u = base*sy
        forcing = (2*beta*np.pi**2*np.sin(np.pi*x)+beta*a*(2+np.pi**2*q)
                   -t*(3-6*x)+t*np.pi**2*p)*sy
        ux = (np.pi*np.cos(np.pi*x)+a*(1-2*x)+t*(-3*x*x+3*x-.5)/beta)*sy
        uy = np.pi*base*np.cos(np.pi*y)
        return u, forcing, np.column_stack((ux, uy))

    def jumps(self, points):
        _, a1, t1 = self.parameters(0)
        _, a2, t2 = self.parameters(1)
        sy = np.sin(np.pi*np.asarray(points)[:, 1])
        return .25*(a2-a1)*sy, .25*(t2-t1)*sy


@dataclass(frozen=True)
class PeakInterfaceProblem(StraightInterfaceProblem):
    """独立快变化模型：原分片解加同一局部峰，仍为零外边界。

    h=16 A x(1-x)y(1-y)exp(-[(x-cx)²+(y-cy)²]/width²)。
    值跳跃不变，通量跳跃增加(β右-β左)h_x，不能沿用旧通量。
    """
    width: float = .12
    amplitude: float = .75
    center_x: float = .46
    center_y: float = .55

    def __post_init__(self):
        super().__post_init__()
        if self.width <= 0 or not np.isfinite(self.width):
            raise ValueError("峰宽必须有限且为正")

    def bump(self, points):
        x,y=np.asarray(points).T
        alpha=1/self.width**2;dx=x-self.center_x;dy=y-self.center_y
        qx=x*(1-x);qy=y*(1-y);px=1-2*x;py=1-2*y
        factor=16*self.amplitude*np.exp(-alpha*(dx**2+dy**2))
        value=factor*qx*qy
        grad=np.column_stack((factor*(px-2*alpha*dx*qx)*qy,
                              factor*qx*(py-2*alpha*dy*qy)))
        dxx=factor*(-2-4*alpha*dx*px+(4*alpha**2*dx**2-2*alpha)*qx)*qy
        dyy=factor*qx*(-2-4*alpha*dy*py+(4*alpha**2*dy**2-2*alpha)*qy)
        return value,grad,dxx+dyy

    def data(self, points, side):
        u,f,grad=super().data(points,side)
        bump,bump_grad,bump_lap=self.bump(points)
        return u+bump,f-self.parameters(side)[0]*bump_lap,grad+bump_grad

    def jumps(self, points):
        gu,gq=super().jumps(points)
        return gu,gq+(self.beta_right-self.beta_left)*self.bump(points)[1][:,0]
