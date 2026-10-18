"""离散验证点上的误差度量，不把训练残差当作解误差。"""
import numpy as np


def errors(predicted, exact):
    delta = np.asarray(predicted) - np.asarray(exact)
    denominator = np.linalg.norm(exact)
    if denominator == 0:
        raise ValueError("参考解范数为零，相对误差无定义")
    return {"relative_l2": float(np.linalg.norm(delta)/denominator),
            "max_abs": float(np.max(np.abs(delta)))}


def rms(values):
    return float(np.sqrt(np.mean(np.asarray(values)**2)))
