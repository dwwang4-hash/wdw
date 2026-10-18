"""残差驱动的增量采样与预算分配；联合策略是候选方案，不声明原创。"""
from time import perf_counter
import numpy as np
from .local_rann import random_collocation, interior_points, interface_points, solve_local
from .metrics import rms


def sampling_collocation(seed, n_per_side, n_interface, uniform=False):
    # 每组独立流使B最终点包含C/D初始点；不改变已经执行的exp02随机机制。
    interior=[interior_points(n_per_side,side,np.random.default_rng(np.random.SeedSequence([seed,100,side])),uniform) for side in [0,1]]
    interface=interface_points(n_interface,None if uniform else np.random.default_rng(np.random.SeedSequence([seed,100,2])))
    return interior,interface


def allocate_budget(scores, budget, minimum=(16,16,8), costs=(1,1,1)):
    """先保最低配额，剩余预算按指标分配；成本可区分点数和标量方程数。"""
    scores=np.asarray(scores,dtype=float);counts=np.array(minimum,dtype=int);costs=np.asarray(costs,dtype=int)
    if not np.all(np.isfinite(scores)) or np.any(scores<0):
        raise ValueError("分配指标必须有限且非负")
    if np.any(costs<1) or np.any(counts<0) or np.sum(counts*costs)>budget:
        raise ValueError("预算不足或成本非法")
    weights=scores+1e-14
    if np.max(scores)<1e-14:weights=np.ones_like(scores)
    remaining=budget-int(np.sum(counts*costs))
    targets=remaining*weights/weights.sum()/costs
    extras=np.floor(targets).astype(int);counts+=extras
    remaining=budget-int(np.sum(counts*costs))
    # 最大余数/欠配额迭代；成本1组保证全部预算可用。
    while remaining:
        feasible=np.flatnonzero(costs<=remaining)
        if not len(feasible):raise ValueError("成本组合无法用尽预算")
        deficits=(targets-extras)*costs
        index=feasible[np.argmax(deficits[feasible])]
        counts[index]+=1;extras[index]+=1;remaining-=int(costs[index])
    return counts


def select_candidates(points, indicator, count, rng, used=None, exploration=.2):
    """无放回抽样；候选池独立于最终验证网格，不使用精确解误差。"""
    if not 0<=exploration<=1:raise ValueError("探索比例必须在[0,1]")
    available=np.ones(len(points),dtype=bool) if used is None else ~used
    indices=np.flatnonzero(available)
    if count>len(indices):raise ValueError("候选池不足，不重复采样")
    scores=np.abs(np.asarray(indicator))[indices]
    probabilities=np.ones(len(indices))/len(indices)
    if np.sum(scores)>1e-14:
        probabilities=exploration*probabilities+(1-exploration)*scores/np.sum(scores)
    chosen=rng.choice(indices,count,replace=False,p=probabilities)
    if used is not None:used[chosen]=True
    return points[chosen]


def compare_sampling(problem, method, seed, budget_mode="points", count=64, scale=2., rounds=3, exploration=.2, indicator_scope="all"):
    """共享特征/初始点/候选池；A/B一次求解，C/D增量重求解。

    初始128内部点/侧+32界面点；静态每轮新增(80,80,32)。
    points模式每轮192点，equations模式每轮224标量行。
    D_minus_pde / D_minus_interface 用于指标消融，仍固定总预算。
    """
    allowed={"A","B","C","D","D_minus_pde","D_minus_interface"}
    if method not in allowed or budget_mode not in {"points","equations"}:raise ValueError("未知策略/预算类型")
    if indicator_scope not in {"all","unused"}:raise ValueError("指标池范围只能为all或unused")
    start=perf_counter()
    if method in {"A","B"}:
        interior,interface=sampling_collocation(seed,128+80*rounds,32+32*rounds,uniform=method=="A")
        solution=solve_local(problem,count,seed,interior,interface,scale=scale)
        return solution,[{"iteration":0,"add_left":0,"add_right":0,"add_interface":0,"n_left":len(interior[0]),"n_right":len(interior[1]),"n_interface":len(interface)}],perf_counter()-start
    interior,interface=sampling_collocation(seed,128,32)
    pool_rng=np.random.default_rng(np.random.SeedSequence([seed,300]))
    candidate_interior=[interior_points(2048,i,pool_rng) for i in [0,1]]
    candidate_interface=interface_points(1024,pool_rng)
    used=[np.zeros(2048,dtype=bool),np.zeros(2048,dtype=bool),np.zeros(1024,dtype=bool)]
    sample_rng=np.random.default_rng(np.random.SeedSequence([seed,400]))
    solution=solve_local(problem,count,seed,interior,interface,scale=scale)
    trace=[{"iteration":0,"add_left":0,"add_right":0,"add_interface":0,"n_left":128,"n_right":128,"n_interface":32,"eta_left":float("nan"),"eta_right":float("nan"),"eta_interface":float("nan")}]
    for iteration in range(1,rounds+1):
        pde,value,flux=solution.residuals(candidate_interior,candidate_interface)
        normalized=[pde[0]/problem.beta_left,pde[1]/problem.beta_right]
        interface_score=np.sqrt(value**2+(flux/max(problem.beta_left,problem.beta_right))**2)
        # 原版all保持不变；新变体unused不把已选训练点计入组指标。
        score_arrays=[normalized[0],normalized[1],interface_score]
        scores=np.array([rms(v[~used[i]]) if indicator_scope=="unused" else rms(v) for i,v in enumerate(score_arrays)])
        allocation_scores=scores.copy()
        if method=="D_minus_pde":allocation_scores[:2]=0
        if method=="D_minus_interface":allocation_scores[2]=0
        costs=(1,1,1) if budget_mode=="points" else (1,1,2)
        budget=192 if budget_mode=="points" else 224
        allocation=np.array([80,80,32]) if method=="C" else allocate_budget(allocation_scores,budget,costs=costs)
        for side in [0,1]:
            point_indicator=np.zeros_like(normalized[side]) if method=="D_minus_pde" else normalized[side]
            additions=select_candidates(candidate_interior[side],point_indicator,int(allocation[side]),sample_rng,used[side],exploration)
            interior[side]=np.vstack((interior[side],additions))
        point_indicator=np.zeros_like(interface_score) if method in {"C","D_minus_interface"} else interface_score
        additions=select_candidates(candidate_interface,point_indicator,int(allocation[2]),sample_rng,used[2],exploration)
        interface=np.vstack((interface,additions))
        solution=solve_local(problem,count,seed,interior,interface,scale=scale,features=solution.features)
        trace.append({"iteration":iteration,"add_left":int(allocation[0]),"add_right":int(allocation[1]),"add_interface":int(allocation[2]),
                      "n_left":len(interior[0]),"n_right":len(interior[1]),"n_interface":len(interface),
                      "eta_left":scores[0],"eta_right":scores[1],"eta_interface":scores[2]})
    return solution,trace,perf_counter()-start
