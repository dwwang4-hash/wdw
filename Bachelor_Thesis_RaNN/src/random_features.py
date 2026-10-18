"""固定 tanh 隐藏特征及其解析导数，不训练隐藏参数。"""
import numpy as np


class TanhFeatures:
    def __init__(self, count, seed, scale=4.0):
        if count < 1 or scale <= 0:
            raise ValueError("特征数和随机权重范围必须为正")
        rng = np.random.default_rng(seed)
        self.weights = rng.uniform(-scale, scale, (count, 2))
        self.biases = rng.uniform(-scale, scale, count)

    def evaluate(self, points):
        # 坐标平移不改变导数；若以后进行尺度缩放，必须加入链式法则。
        z = (np.asarray(points) - 0.5) @ self.weights.T + self.biases
        values = np.tanh(z)
        first = 1 - values**2
        second = -2 * values * first
        gradient = first[:, :, None] * self.weights[None, :, :]
        laplacian = second * np.sum(self.weights**2, axis=1)
        return values, gradient, laplacian


class LocalTanhFeatures(TanhFeatures):
    """把每个子域仿射映射到单位方形；导数转换回物理坐标。"""
    def __init__(self, count, seed, side, scale=2.0):
        super().__init__(count, np.random.SeedSequence([seed, side, 200]), scale)
        self.count = count
        self.origin = np.array([.5*side, 0.0])
        self.length = np.array([.5, 1.0])

    def evaluate(self, points):
        mapped = (np.asarray(points)-self.origin)/self.length
        values, gradient, _ = super().evaluate(mapped)
        physical_weights = self.weights/self.length
        second = -2*values*(1-values**2)
        return values, gradient/self.length, second*np.sum(physical_weights**2, axis=1)
