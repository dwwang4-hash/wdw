"""Poisson 强形式随机特征配置法；不是 Petrov–Galerkin 或 LRNN-DG 复现。"""
from time import perf_counter
import numpy as np
from .random_features import TanhFeatures
from .least_squares import solve_least_squares
from .pde_models import poisson_forcing


def boundary_points(per_edge=80):
    t = (np.arange(per_edge)+0.5)/per_edge
    return np.vstack((np.column_stack((t, np.zeros_like(t))),
                      np.column_stack((t, np.ones_like(t))),
                      np.column_stack((np.zeros_like(t), t)),
                      np.column_stack((np.ones_like(t), t))))


def solve_poisson_rann(count, seed, n_interior=1024, scale=4.0, boundary_weight=10.0, rcond=1e-12):
    start = perf_counter()
    # 独立随机流使同一 seed 的配置点不随特征数改变。
    interior = np.random.default_rng(np.random.SeedSequence([seed, 100])).uniform(0, 1, (n_interior, 2))
    boundary = boundary_points()
    features = TanhFeatures(count, seed, scale)
    _, _, lap = features.evaluate(interior)
    phi, _, _ = features.evaluate(boundary)
    # 离散均方目标：mean(PDE²)+λ_b mean(boundary²)。λ_b 为无量纲数值权重。
    matrix = np.vstack((-lap/np.sqrt(n_interior), np.sqrt(boundary_weight/len(boundary))*phi))
    rhs = np.concatenate((poisson_forcing(interior)/np.sqrt(n_interior), np.zeros(len(boundary))))
    coeff, info = solve_least_squares(matrix, rhs, rcond)
    info.update({"train_pde_rms": float(np.sqrt(np.mean((-lap@coeff-poisson_forcing(interior))**2))),
                 "train_boundary_rms": float(np.sqrt(np.mean((phi@coeff)**2))),
                 "solve_seconds": perf_counter()-start})
    return features, coeff, info
