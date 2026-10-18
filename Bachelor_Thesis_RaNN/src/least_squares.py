"""SVD 最小二乘与可解释的奇异值诊断，避免正规方程。"""
import numpy as np
from scipy.linalg import lstsq, svdvals


def solve_least_squares(matrix, rhs, rcond=1e-12, ridge=0.0):
    if ridge < 0:
        raise ValueError("正则化系数不可为负")
    original_s = svdvals(matrix)
    a, b = matrix, rhs
    if ridge:
        a = np.vstack((matrix, np.sqrt(ridge)*np.eye(matrix.shape[1])))
        b = np.concatenate((rhs, np.zeros(matrix.shape[1])))
    coeff, _, rank, singular = lstsq(a, b, cond=rcond, lapack_driver="gelsd")
    cutoff = rcond * original_s[0]
    kept = original_s[original_s > cutoff]
    return coeff, {
        "rank": int(rank), "data_rank": int(kept.size),
        "condition_raw": float(original_s[0]/original_s[-1]) if original_s[-1] else float("inf"),
        "condition_retained": float(original_s[0]/kept[-1]),
        "singular_max": float(original_s[0]), "singular_min": float(original_s[-1]),
        "singular_min_retained": float(kept[-1]),
        "weighted_training_rms": float(np.sqrt(np.mean((matrix @ coeff-rhs)**2))),
    }
