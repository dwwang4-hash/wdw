"""双子域强形式LRNN独立实现，不冒充原文FD或DG复现。"""
from dataclasses import dataclass
from time import perf_counter
import numpy as np
from .random_features import LocalTanhFeatures
from .least_squares import solve_least_squares
from .metrics import errors, rms


def interior_points(count, side, rng=None, uniform=False):
    if uniform:
        # 实验网格点数选复合数，取完整矩形网格，避免截断最后一行造成偏置。
        nx = max(k for k in range(1, int(np.sqrt(count))+1) if count % k == 0)
        ny = count//nx
        x, y = np.meshgrid((np.arange(nx)+.5)/nx, (np.arange(ny)+.5)/ny)
        p = np.column_stack((x.ravel(), y.ravel()))[:count]
    else:
        p = rng.uniform(0, 1, (count, 2))
    p[:, 0] = .5*p[:, 0]+.5*side
    return p


def interface_points(count, rng=None):
    y = (np.arange(count)+.5)/count if rng is None else rng.uniform(0, 1, count)
    return np.column_stack((np.full(count, .5), y))


def outer_boundary(per_segment=40):
    """每侧三条外边界，按所属子域分组；不含角点/界面端点。"""
    t = (np.arange(per_segment)+.5)/per_segment
    result = []
    for side in [0, 1]:
        x = .5*t+.5*side
        result.append(np.vstack((np.column_stack((x, np.zeros_like(t))),
                                 np.column_stack((x, np.ones_like(t))),
                                 np.column_stack((np.full_like(t, side), t)))))
    return result


def random_collocation(seed, n_per_side=512, n_interface=80, uniform=False):
    rng = np.random.default_rng(np.random.SeedSequence([seed, 100]))
    return [interior_points(n_per_side, i, rng, uniform) for i in [0, 1]], interface_points(n_interface, None if uniform else rng)


def assemble(problem, features, interior, interface, boundary, scaling="balanced", boundary_weight=50., interface_weight=50.):
    if scaling not in {"raw", "balanced"}:
        raise ValueError("scaling只能为raw或balanced")
    sizes = [f.count for f in features]
    total = sum(sizes); blocks = []; targets = []

    def add(local, rhs, group_weight=1., physical_scale=1.):
        factor = np.sqrt(group_weight/len(rhs))/physical_scale
        blocks.append(local*factor); targets.append(rhs*factor)

    for side in [0, 1]:
        beta = problem.parameters(side)[0]
        _, _, lap = features[side].evaluate(interior[side])
        block = np.zeros((len(lap), total))
        offset = 0 if side == 0 else sizes[0]
        block[:, offset:offset+sizes[side]] = -beta*lap
        add(block, problem.data(interior[side], side)[1], physical_scale=beta if scaling == "balanced" else 1.)
        phi, _, _ = features[side].evaluate(boundary[side])
        block = np.zeros((len(phi), total)); block[:, offset:offset+sizes[side]] = phi
        add(block, problem.data(boundary[side], side)[0], boundary_weight)
    phi1, grad1, _ = features[0].evaluate(interface)
    phi2, grad2, _ = features[1].evaluate(interface)
    jump_u, jump_flux = problem.jumps(interface)
    add(np.hstack((-phi1, phi2)), jump_u, interface_weight)
    flux = np.hstack((-problem.beta_left*grad1[:, :, 0], problem.beta_right*grad2[:, :, 0]))
    add(flux, jump_flux, interface_weight, max(problem.beta_left, problem.beta_right) if scaling == "balanced" else 1.)
    return np.vstack(blocks), np.concatenate(targets)


@dataclass
class LocalSolution:
    problem: object
    features: list
    coefficients: list
    diagnostics: dict

    def evaluate(self, points, side):
        phi, grad, lap = self.features[side].evaluate(points)
        coeff = self.coefficients[side]
        return phi@coeff, np.einsum("njk,j->nk", grad, coeff), lap@coeff

    def residuals(self, interior, interface):
        pde = []
        for side in [0, 1]:
            beta = self.problem.parameters(side)[0]
            pde.append(-beta*self.evaluate(interior[side], side)[2]-self.problem.data(interior[side], side)[1])
        u1, grad1, _ = self.evaluate(interface, 0)
        u2, grad2, _ = self.evaluate(interface, 1)
        gu, gq = self.problem.jumps(interface)
        return pde, u2-u1-gu, self.problem.beta_right*grad2[:, 0]-self.problem.beta_left*grad1[:, 0]-gq


def solve_local(problem, count=128, seed=11, interior=None, interface=None, scaling="balanced", scale=2.,
                boundary_weight=50., interface_weight=50., ridge=0., rcond=1e-12, features=None, boundary=None):
    start = perf_counter()
    if interior is None or interface is None:
        if interior is not None or interface is not None:
            raise ValueError("内部点与界面点须同时提供")
        interior, interface = random_collocation(seed)
    features = features if features is not None else [LocalTanhFeatures(count, seed, side, scale) for side in [0, 1]]
    boundary = boundary if boundary is not None else outer_boundary()
    matrix, rhs = assemble(problem, features, interior, interface, boundary, scaling, boundary_weight, interface_weight)
    coeff, info = solve_least_squares(matrix, rhs, rcond, ridge)
    info.update({"solve_seconds":perf_counter()-start,"n_points":sum(map(len, interior))+len(interface)+sum(map(len, boundary)),
                 "n_equations":len(rhs),"n_interior_left":len(interior[0]),"n_interior_right":len(interior[1]),"n_interface":len(interface)})
    split = features[0].count
    return LocalSolution(problem, features, [coeff[:split], coeff[split:]], info)


def validation_metrics(solution, interior=None, interface=None):
    if interior is None:
        interior = [interior_points(83*83, side, uniform=True) for side in [0, 1]]
    if interface is None:
        interface = interface_points(257)
    predicted = []; exact = []; result = {}
    for side in [0, 1]:
        predicted.append(solution.evaluate(interior[side], side)[0]); exact.append(solution.problem.data(interior[side], side)[0])
        result[f"relative_l2_side{side+1}"] = errors(predicted[-1], exact[-1])["relative_l2"]
    result.update(errors(np.concatenate(predicted), np.concatenate(exact)))
    pde, value, flux = solution.residuals(interior, interface)
    for side in [0, 1]:
        result[f"validation_pde_rms_side{side+1}"] = rms(pde[side])
        result[f"validation_pde_normalized_side{side+1}"] = rms(pde[side])/solution.problem.parameters(side)[0]
    result.update({"interface_value_rms":rms(value),"interface_value_max":float(np.max(np.abs(value))),
                   "interface_flux_rms":rms(flux),"interface_flux_max":float(np.max(np.abs(flux))),
                   "interface_flux_normalized":rms(flux)/max(solution.problem.beta_left, solution.problem.beta_right)})
    b = outer_boundary(83)
    result["boundary_rms"] = rms(np.concatenate([solution.evaluate(b[i], i)[0]-solution.problem.data(b[i], i)[0] for i in [0, 1]]))
    result["coefficient_norm"] = float(np.linalg.norm(np.concatenate(solution.coefficients)))
    return result
