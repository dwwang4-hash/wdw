"""零 Dirichlet Poisson 方程的五点差分法，稀疏直接求解。"""
from time import perf_counter
import numpy as np
from scipy.sparse import diags, eye, kron
from scipy.sparse.linalg import spsolve
from .pde_models import poisson_forcing


def solve_poisson(n):
    """n 是每个坐标方向的内部节点数；h=1/(n+1)。"""
    if n < 2:
        raise ValueError("每个方向至少需要两个内部节点")
    start = perf_counter()
    h = 1 / (n + 1)
    axis = np.arange(1, n + 1) * h
    xx, yy = np.meshgrid(axis, axis, indexing="xy")
    points = np.column_stack((xx.ravel(), yy.ravel()))
    one_d = diags([-np.ones(n-1), 2*np.ones(n), -np.ones(n-1)], [-1, 0, 1], format="csr") / h**2
    matrix = kron(eye(n, format="csr"), one_d) + kron(one_d, eye(n, format="csr"))
    rhs = poisson_forcing(points)
    values = spsolve(matrix.tocsr(), rhs)
    elapsed = perf_counter() - start
    residual = np.linalg.norm(matrix @ values-rhs) / np.linalg.norm(rhs)
    return points, values, h, elapsed, residual
