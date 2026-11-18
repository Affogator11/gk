# -*- coding: utf-8 -*-
"""种子数据：数学学科知识点树、示例题库、细目表模板。

题库内容为演示用示例题（答案经人工核对），真实项目应替换为审核过的真题库。
"""
from __future__ import annotations

import json
import sqlite3

# ---------------------------------------------------------------- 知识点树
KNOWLEDGE = [
    ("M1",   "集合与常用逻辑用语", None, 1, 1),
    ("M1.1", "集合的运算",         "M1", 2, 1),
    ("M1.2", "充分必要条件",       "M1", 2, 2),
    ("M2",   "函数",               None, 1, 2),
    ("M2.1", "函数的概念与性质",   "M2", 2, 1),
    ("M2.2", "指数函数与对数函数", "M2", 2, 2),
    ("M2.3", "三角函数",           "M2", 2, 3),
    ("M2.4", "函数与方程",         "M2", 2, 4),
    ("M3",   "导数及其应用",       None, 1, 3),
    ("M3.1", "导数的概念与运算",   "M3", 2, 1),
    ("M3.2", "导数与单调性极值",   "M3", 2, 2),
    ("M3.3", "导数的综合应用",     "M3", 2, 3),
    ("M4",   "数列",               None, 1, 4),
    ("M4.1", "等差数列与等比数列", "M4", 2, 1),
    ("M4.2", "数列求和",           "M4", 2, 2),
    ("M5",   "不等式",             None, 1, 5),
    ("M5.1", "一元二次不等式",     "M5", 2, 1),
    ("M5.2", "基本不等式",         "M5", 2, 2),
    ("M6",   "立体几何",           None, 1, 6),
    ("M6.1", "空间几何体",         "M6", 2, 1),
    ("M6.2", "点线面位置关系",     "M6", 2, 2),
    ("M6.3", "空间向量与角",       "M6", 2, 3),
    ("M7",   "解析几何",           None, 1, 7),
    ("M7.1", "直线与圆",           "M7", 2, 1),
    ("M7.2", "椭圆",               "M7", 2, 2),
    ("M7.3", "双曲线与抛物线",     "M7", 2, 3),
    ("M8",   "概率与统计",         None, 1, 8),
    ("M8.1", "古典概型",           "M8", 2, 1),
    ("M8.2", "随机变量及其分布",   "M8", 2, 2),
    ("M8.3", "统计与抽样",         "M8", 2, 3),
    ("M9",   "平面向量与复数",     None, 1, 9),
    ("M9.1", "平面向量",           "M9", 2, 1),
    ("M9.2", "复数",               "M9", 2, 2),
]

QUESTIONS: list[dict] = []


def add(qtype, stem, answer, analysis, kp, diff, cog, score=5, options=None,
        year=2024, region="模拟", tags=None):
    QUESTIONS.append({
        "qtype": qtype, "stem": stem, "options": options, "answer": answer,
        "analysis": analysis, "score": score, "difficulty": diff,
        "cognitive": cog, "knowledge_code": kp, "year": year, "region": region,
        "tags": tags or [],
    })


# ---------------------------------------------------------------- 单选题 / 填空题
add("single", "已知集合 A={1,2,3}，B={2,3,4}，则 A∩B 中元素的个数为（　）",
    "A", "交集取公共元素，A∩B={2,3}，共 2 个元素。", "M1.1", 0.78, "understand",
    options=["A. 2", "B. 3", "C. 4", "D. 1"])

add("single", "已知集合 A={x | -1<x<3}，B={x | x≥2}，则 A∩B=（　）",
    "B", "在数轴上取交集：A∩B={x | 2≤x<3}。", "M1.1", 0.62, "apply",
    options=["A. (-1,2)", "B. [2,3)", "C. (2,3)", "D. [2,3]"])

add("blank", "已知集合 A={x | x²-3x+2<0}，B={x | x≥a}，若 A⊆B，则实数 a 的取值范围是______。",
    "a≤1", "由 x²-3x+2<0 得 1<x<2，即 A=(1,2)。A⊆B 要求 a≤1。", "M1.1", 0.5, "analyze")

add("single", "“x>2”是“x>1”的（　）",
    "A", "x>2 一定推出 x>1，但 x>1 推不出 x>2（如 x=1.5），故为充分不必要条件。", "M1.2", 0.78, "understand",
    options=["A. 充分不必要条件", "B. 必要不充分条件", "C. 充要条件", "D. 既不充分也不必要条件"])

add("single", "“x²=1”是“x=1”的（　）",
    "B", "x=1 可推出 x²=1，但 x²=1 还有 x=-1，故为必要不充分条件。", "M1.2", 0.68, "understand",
    options=["A. 充分不必要条件", "B. 必要不充分条件", "C. 充要条件", "D. 既不充分也不必要条件"])

add("blank", "已知 p 是 q 的充分不必要条件，q 是 r 的充要条件，则 p 是 r 的______条件。",
    "充分不必要", "充分性传递成立，必要性不传递（q 与 r 等价，p 不必要 q），故为充分不必要条件。", "M1.2", 0.45, "analyze")

add("single", "设 f(x) 是定义在 R 上的奇函数，当 x>0 时 f(x)=x²-2x，则 f(-1)=（　）",
    "C", "f(1)=1-2=-1，由奇函数性质 f(-1)=-f(1)=1。", "M2.1", 0.55, "apply",
    options=["A. -1", "B. 3", "C. 1", "D. -3"])

add("blank", "函数 f(x)=ln(x+1) 的定义域是______。",
    "(-1,+∞)", "对数真数大于 0：x+1>0，即 x>-1。", "M2.1", 0.8, "understand")

add("single", "已知函数 f(x)=x²-2x+3 在区间 [0,m] 上单调递减，则 m 的取值范围是（　）",
    "C", "对称轴 x=1，在 (-∞,1] 上递减，故 0<m≤1。", "M2.1", 0.45, "analyze",
    options=["A. m≥1", "B. m≤2", "C. 0<m≤1", "D. m>0"])

add("blank", "计算：log₂8 + (1/2)⁻¹ = ______。",
    "5", "log₂8=3，(1/2)⁻¹=2，和为 5。", "M2.2", 0.75, "apply")

add("single", "已知 2ᵃ=3，2ᵇ=5，则 2ᵃ⁺ᵇ=（　）",
    "D", "2ᵃ⁺ᵇ=2ᵃ·2ᵇ=3×5=15。", "M2.2", 0.62, "apply",
    options=["A. 8", "B. 3/5", "C. 2", "D. 15"])

add("single", "函数 y=log₁/₂(x²-2x) 的单调递增区间是（　）",
    "A", "定义域为 x<0 或 x>2。内层 u=x²-2x 在 (-∞,1) 递减，外层 log₁/₂ 递减，复合后递增，结合定义域得 (-∞,0)。", "M2.2", 0.35, "analyze",
    options=["A. (-∞,0)", "B. (2,+∞)", "C. (1,+∞)", "D. (-∞,1)"])

add("single", "已知 sinα=3/5，α∈(π/2,π)，则 cosα=（　）",
    "B", "α 在第二象限，cosα<0，cosα=-√(1-9/25)=-4/5。", "M2.3", 0.7, "apply",
    options=["A. 4/5", "B. -4/5", "C. 3/5", "D. -3/5"])

add("single", "函数 f(x)=2sin(2x+π/6) 的最小正周期是（　）",
    "B", "T=2π/ω=2π/2=π。", "M2.3", 0.72, "understand",
    options=["A. 2π", "B. π", "C. 4π", "D. π/2"])

add("blank", "函数 f(x)=sinx+√3cosx 的最大值是______。",
    "2", "f(x)=2sin(x+π/3)，故最大值为 2。", "M2.3", 0.5, "apply")

add("single", "函数 f(x)=lnx+x-3 的零点所在的区间是（　）",
    "C", "f(2)=ln2-1<0，f(3)=ln3>0，由零点存在定理知零点在 (2,3)。", "M2.4", 0.5, "analyze",
    options=["A. (0,1)", "B. (1,2)", "C. (2,3)", "D. (3,4)"])

add("blank", "已知 f(x)=x³-3x+1，则 f'(1)=______。",
    "0", "f'(x)=3x²-3，f'(1)=3-3=0。", "M3.1", 0.72, "apply")

add("single", "已知 f(x)=x·lnx，则 f'(e)=（　）",
    "B", "f'(x)=lnx+1，f'(e)=1+1=2。", "M3.1", 0.6, "apply",
    options=["A. 1", "B. 2", "C. e", "D. e+1"])

add("single", "曲线 y=x³ 在点 (1,1) 处的切线方程为（　）",
    "A", "y'=3x²，k=3，切线 y-1=3(x-1)，即 y=3x-2。", "M3.1", 0.55, "apply",
    options=["A. y=3x-2", "B. y=3x+2", "C. y=x", "D. y=2x-1"])

add("blank", "函数 f(x)=x³-3x 的极大值是______。",
    "2", "f'(x)=3x²-3=3(x-1)(x+1)，x=-1 处由增转减，取极大值 f(-1)=2。", "M3.2", 0.55, "apply")

add("single", "函数 f(x)=x³-3x 在区间 [-2,2] 上的最小值是（　）",
    "A", "极小值 f(1)=-2，端点 f(-2)=-2、f(2)=2，故最小值为 -2。", "M3.2", 0.42, "analyze",
    options=["A. -2", "B. -4", "C. 0", "D. 2"])

add("single", "函数 f(x)=xeˣ 的单调递增区间是（　）",
    "C", "f'(x)=(x+1)eˣ，当 x>-1 时 f'(x)>0，故增区间为 (-1,+∞)。", "M3.2", 0.5, "apply",
    options=["A. (-∞,-1)", "B. (-∞,0)", "C. (-1,+∞)", "D. (0,+∞)"])

add("blank", "等差数列 {aₙ} 中，a₁=2，d=3，则 a₁₀=______。",
    "29", "a₁₀=a₁+9d=2+27=29。", "M4.1", 0.7, "apply")

add("single", "等比数列 {aₙ} 中，a₁=1，q=2，则 S₅=（　）",
    "C", "S₅=(1-2⁵)/(1-2)=31。", "M4.1", 0.72, "apply",
    options=["A. 15", "B. 16", "C. 31", "D. 32"])

add("blank", "等差数列 {aₙ} 中，a₃+a₈=10，则 S₁₀=______。",
    "50", "S₁₀=10(a₁+a₁₀)/2=5(a₃+a₈)=50。", "M4.1", 0.45, "analyze")

add("blank", "求和：1/(1×2)+1/(2×3)+…+1/(n(n+1))=______。",
    "n/(n+1)", "裂项：1/(k(k+1))=1/k-1/(k+1)，相消得 1-1/(n+1)=n/(n+1)。", "M4.2", 0.5, "apply")

add("single", "数列 1×2+2×2²+3×2³+…+n·2ⁿ 的和为（　）",
    "B", "错位相减法可得 Sₙ=(n-1)·2ⁿ⁺¹+2。", "M4.2", 0.35, "analyze",
    options=["A. n·2ⁿ⁺¹+2", "B. (n-1)·2ⁿ⁺¹+2", "C. (n+1)·2ⁿ⁺¹-2", "D. n·2ⁿ"])

add("single", "不等式 x²-5x+6<0 的解集是（　）",
    "B", "因式分解 (x-2)(x-3)<0，得 2<x<3。", "M5.1", 0.8, "apply",
    options=["A. (1,6)", "B. (2,3)", "C. (-∞,2)∪(3,+∞)", "D. [2,3]"])

add("blank", "若 a>1，则不等式 ax²-(a+1)x+1<0 的解集是______。",
    "(1/a,1)", "因式分解 (ax-1)(x-1)<0，因 a>1 有 1/a<1，故解集为 (1/a,1)。", "M5.1", 0.4, "analyze")

add("blank", "若 x>0，则 x+4/x 的最小值为______。",
    "4", "由基本不等式 x+4/x≥2√4=4，当且仅当 x=2 时取等号。", "M5.2", 0.75, "apply")

add("single", "若 x>0，y>0，且 x+y=1，则 1/x+4/y 的最小值为（　）",
    "D", "1/x+4/y=(x+y)(1/x+4/y)=5+y/x+4x/y≥5+4=9。", "M5.2", 0.4, "analyze",
    options=["A. 5", "B. 6", "C. 8", "D. 9"])

add("blank", "棱长为 2 的正方体的外接球表面积为______。",
    "12π", "体对角线为直径，2R=2√3，R=√3，S=4πR²=12π。", "M6.1", 0.55, "apply")

add("single", "底面半径为 3、高为 4 的圆锥的体积是（　）",
    "B", "V=(1/3)πr²h=(1/3)π×9×4=12π。", "M6.1", 0.72, "apply",
    options=["A. 36π", "B. 12π", "C. 16π", "D. 48π"])

add("single", "正方体 ABCD-A₁B₁C₁D₁ 中，异面直线 A₁B 与 AD₁ 所成的角为（　）",
    "C", "A₁B∥D₁C，∠AD₁C 为正三角形内角，故为 60°。", "M6.2", 0.6, "analyze",
    options=["A. 30°", "B. 45°", "C. 60°", "D. 90°"])

add("single", "正方体 ABCD-A₁B₁C₁D₁ 中，异面直线 A₁B 与 B₁C 所成角的余弦值为（　）",
    "B", "建系得 A₁B=(1,0,-1)，B₁C=(0,1,-1)，cosθ=|1|/(√2·√2)=1/2。", "M6.3", 0.45, "analyze",
    options=["A. √3/3", "B. 1/2", "C. √2/2", "D. √3/2"])

add("single", "圆 x²+y²-4x+2y=0 的圆心和半径分别是（　）",
    "C", "配方得 (x-2)²+(y+1)²=5，圆心 (2,-1)，半径 √5。", "M7.1", 0.7, "apply",
    options=["A. (2,1)，√5", "B. (-2,1)，5", "C. (2,-1)，√5", "D. (2,-1)，5"])

add("single", "直线 x-y+1=0 被圆 (x-1)²+y²=4 截得的弦长为（　）",
    "B", "圆心到直线距离 d=√2，弦长 2√(4-2)=2√2。", "M7.1", 0.5, "analyze",
    options=["A. 2", "B. 2√2", "C. 4", "D. √2"])

add("blank", "过点 (1,2) 且与圆 x²+y²=1 相切的直线方程为______。",
    "3x-4y+5=0", "设切线 y-2=k(x-1)，由圆心距等于半径解得 k=3/4，整理得 3x-4y+5=0。", "M7.1", 0.45, "analyze")

add("single", "椭圆 x²/25+y²/9=1 的离心率为（　）",
    "D", "a=5，b=3，c=4，e=c/a=4/5。", "M7.2", 0.7, "apply",
    options=["A. 3/5", "B. 3/4", "C. √7/5", "D. 4/5"])

add("blank", "焦点在 x 轴上、焦距为 2 且经过点 (0,√3) 的椭圆标准方程为______。",
    "x²/4+y²/3=1", "c=1，过 (0,√3) 得 b=√3，a²=b²+c²=4。", "M7.2", 0.55, "analyze")

add("single", "双曲线 x²/9-y²/16=1 的渐近线方程为（　）",
    "A", "渐近线 y=±(b/a)x=±(4/3)x。", "M7.3", 0.65, "apply",
    options=["A. y=±(4/3)x", "B. y=±(3/4)x", "C. y=±(16/9)x", "D. y=±(9/16)x"])

add("blank", "抛物线 y²=8x 的准线方程为______。",
    "x=-2", "2p=8，p=4，准线 x=-p/2=-2。", "M7.3", 0.75, "apply")

add("single", "从 1,2,3,4,5 中任取两个不同的数，其和为偶数的概率是（　）",
    "B", "总取法 C(5,2)=10，和为偶数有 C(3,2)+C(2,2)=4 种，概率 2/5。", "M8.1", 0.65, "apply",
    options=["A. 1/5", "B. 2/5", "C. 3/5", "D. 1/2"])

add("single", "同时掷两枚均匀骰子，点数之和为 7 的概率是（　）",
    "C", "基本事件 36 个，和为 7 有 6 个，概率 1/6。", "M8.1", 0.7, "apply",
    options=["A. 1/12", "B. 1/9", "C. 1/6", "D. 1/4"])

add("blank", "已知 X~B(4,0.5)，则 E(X)=______。",
    "2", "二项分布期望 E(X)=np=4×0.5=2。", "M8.2", 0.6, "apply")

add("single", "已知随机变量 X 服从正态分布 N(2,σ²)，且 P(X<4)=0.8，则 P(0<X<2)=（　）",
    "B", "由对称性 P(X>2)=0.5，P(2<X<4)=0.3，故 P(0<X<2)=0.3。", "M8.2", 0.42, "analyze",
    options=["A. 0.2", "B. 0.3", "C. 0.4", "D. 0.5"])

add("blank", "数据 2,3,3,4,8 的中位数是______。",
    "3", "排序后中间位置的数是 3。", "M8.3", 0.8, "understand")

add("single", "数据 2,4,4,6,9 的平均数和方差分别是（　）",
    "C", "平均数为 5，方差 [(9+1+1+1+16)/5]=5.6。", "M8.3", 0.55, "apply",
    options=["A. 5，4", "B. 4，5", "C. 5，5.6", "D. 5，6"])

add("blank", "已知向量 a=(1,2)，b=(3,-1)，则 a·b=______。",
    "1", "数量积 1×3+2×(-1)=1。", "M9.1", 0.7, "apply")

add("single", "已知向量 a=(1,2)，b=(m,1)，若 a⊥b，则 m=（　）",
    "A", "垂直则数量积为 0：m+2=0，m=-2。", "M9.1", 0.6, "apply",
    options=["A. -2", "B. 2", "C. 1/2", "D. -1/2"])

add("single", "复数 (1+i)/(1-i) 的值为（　）",
    "B", "分子分母同乘 (1+i)：(1+i)²/2=2i/2=i。", "M9.2", 0.7, "apply",
    options=["A. 1", "B. i", "C. -i", "D. -1"])

add("blank", "复数 (1+2i)(2-i)=______。",
    "4+3i", "展开 2-i+4i-2i²=4+3i。", "M9.2", 0.6, "apply")

# ---------------------------------------------------------------- 多选题
add("multi", "下列关于函数 f(x)=x³-3x 的说法中，正确的是（　）",
    "AB", "f'(x)=3(x-1)(x+1)，在 (-1,1) 上递减，x=-1 取极大值 2，x=1 取极小值 -2，f(x) 为奇函数。", "M3.2", 0.45, "analyze",
    options=["A. f(x) 在 (-1,1) 上单调递减", "B. f(x) 的极大值为 2",
             "C. f(x) 的最小值为 -2", "D. f(x) 是偶函数"])

add("multi", "已知等差数列 {aₙ} 的公差 d>0，a₁=1，且 a₂、a₄、a₈ 成等比数列，则（　）",
    "AC", "由 a₄²=a₂a₈ 得 (1+3d)²=(1+d)(1+7d)，解得 d=1，故 aₙ=n，Sₙ=n(n+1)/2。", "M4.1", 0.38, "analyze",
    options=["A. aₙ=n", "B. aₙ=2n-1", "C. Sₙ=n(n+1)/2", "D. Sₙ=n²"])

add("multi", "关于椭圆 x²/25+y²/9=1，下列说法正确的是（　）",
    "ABD", "a=5，b=3，c=4；长轴长为 10，离心率 4/5，焦距 8。", "M7.2", 0.42, "analyze",
    options=["A. 长轴长为 10", "B. 焦距为 8",
             "C. 离心率为 3/5", "D. 短轴长为 6"])

add("multi", "关于函数 f(x)=sin(2x+π/6)，下列说法正确的是（　）",
    "ACD", "周期 T=π；对称轴 2x+π/6=π/2+kπ；最大值 1。", "M2.3", 0.4, "analyze",
    options=["A. 最小正周期为 π", "B. 最小正周期为 2π",
             "C. 最大值为 1", "D. 图象关于直线 x=π/6 对称"])

add("multi", "下列命题中，正确的是（　）",
    "BC", "A 错：x=0 满足 x²=0 但不是正数；D 错：a=b=0 时不成立。", "M1.2", 0.5, "analyze",
    options=["A. “x>0”是“x²>0”的充要条件",
             "B. “x>0”是“x²>0”的充分不必要条件",
             "C. “a>b”是“a+c>b+c”的充要条件",
             "D. “a>b”是“a²>b²”的充分条件"])

add("multi", "某班 50 名学生的一次测验成绩近似服从正态分布，则下列说法合理的是（　）",
    "AB", "正态分布关于均值对称，均值附近人数最多，可用样本估计总体。", "M8.3", 0.5, "understand",
    options=["A. 可用样本平均数估计总体均值", "B. 成绩在均值附近的人数最多",
             "C. 成绩分布一定关于 0 对称", "D. 标准差越大说明成绩越集中"])

# ---------------------------------------------------------------- 解答题
add("solve",
    "已知等差数列 {aₙ} 满足 a₁=1，a₃+a₅=14。\n（1）求数列 {aₙ} 的通项公式；\n（2）设 bₙ=1/(aₙaₙ₊₁)，求数列 {bₙ} 的前 n 项和 Tₙ。",
    "（1）aₙ=2n-1；（2）Tₙ=n/(2n+1)",
    "（1）设公差为 d，则 a₃+a₅=(1+2d)+(1+4d)=2+6d=14，得 d=2，故 aₙ=2n-1。\n"
    "（2）bₙ=1/[(2n-1)(2n+1)]=(1/2)[1/(2n-1)-1/(2n+1)]，裂项相消得 Tₙ=(1/2)[1-1/(2n+1)]=n/(2n+1)。",
    "M4.2", 0.42, "apply", score=15, year=2024)

add("solve",
    "已知函数 f(x)=2sin(2x+π/6)。\n（1）求 f(x) 的最小正周期和单调递增区间；\n（2）求 f(x) 在区间 [0,π/2] 上的值域。",
    "（1）T=π，增区间 [-π/3+kπ, π/6+kπ](k∈Z)；（2）[-1,2]",
    "（1）T=2π/2=π；令 -π/2+2kπ≤2x+π/6≤π/2+2kπ，解得 -π/3+kπ≤x≤π/6+kπ。\n"
    "（2）x∈[0,π/2] 时 2x+π/6∈[π/6,7π/6]，sin 值域为 [-1/2,1]，故 f(x)∈[-1,2]。",
    "M2.3", 0.45, "apply", score=13)

add("solve",
    "正方体 ABCD-A₁B₁C₁D₁ 的棱长为 2。\n（1）求异面直线 A₁B 与 AD₁ 所成的角；\n（2）求三棱锥 A₁-ABD 的体积。",
    "（1）60°；（2）4/3",
    "（1）A₁B∥D₁C，∠AD₁C 为正三角形内角，故为 60°。\n"
    "（2）V=(1/3)·S△ABD·AA₁=(1/3)·(1/2·2·2)·2=4/3。",
    "M6.2", 0.5, "apply", score=15)

add("solve",
    "已知椭圆 C: x²/4+y²=1，直线 l 过点 (1,0) 且与椭圆交于 A、B 两点。\n（1）求椭圆 C 的离心率；\n（2）求 |AB| 的最小值。",
    "（1）√3/2；（2）1",
    "（1）a=2，b=1，c=√3，e=c/a=√3/2。\n"
    "（2）当 l⊥x 轴时弦最短，为通径 2b²/a=1。",
    "M7.2", 0.32, "analyze", score=17)

add("solve",
    "某工厂生产的一种零件合格率为 0.9，现从产品中随机抽取 3 件。\n（1）求恰有 2 件合格的概率；\n（2）设合格品件数为 X，求 E(X) 与 D(X)。",
    "（1）0.243；（2）E(X)=2.7，D(X)=0.27",
    "（1）X~B(3,0.9)，P(X=2)=C(3,2)×0.9²×0.1=0.243。\n"
    "（2）E(X)=np=2.7，D(X)=np(1-p)=3×0.9×0.1=0.27。",
    "M8.2", 0.55, "apply", score=15)

add("solve",
    "已知函数 f(x)=lnx-ax（a∈R）。\n（1）讨论 f(x) 的单调性；\n（2）当 a=1 时，求 f(x) 的最大值。",
    "（1）a≤0 时在 (0,+∞) 递增；a>0 时在 (0,1/a) 递增、(1/a,+∞) 递减；（2）-1",
    "（1）f'(x)=1/x-a。a≤0 时 f'(x)>0 恒成立；a>0 时 f'(x)>0⇔x<1/a。\n"
    "（2）a=1 时最大值为 f(1)=0-1=-1。",
    "M3.3", 0.38, "analyze", score=17)

add("solve",
    "已知函数 f(x)=x³+ax²+bx 在 x=1 处取得极值 -2。\n（1）求 a、b 的值；\n（2）求 f(x) 在区间 [-2,2] 上的最大值与最小值。",
    "（1）a=0，b=-3；（2）最大值为 2，最小值为 -2",
    "（1）f'(x)=3x²+2ax+b。由 f'(1)=0、f(1)=-2 得 3+2a+b=0 且 1+a+b=-2，解得 a=0，b=-3。\n"
    "（2）f(x)=x³-3x，端点值 f(-2)=-2、f(2)=2，极值 f(-1)=2、f(1)=-2，故最大值为 2，最小值为 -2。",
    "M3.3", 0.35, "analyze", score=17)


# ---------------------------------------------------------------- 细目表模板
def _cells(weights: dict[str, float], total: float) -> list[dict]:
    raw = sum(weights.values())
    out = []
    for code, w in weights.items():
        out.append({"knowledge_code": code, "score": round(w / raw * total, 1)})
    return out


BLUEPRINTS = [
    {
        "name": "新高考 I 卷 · 数学",
        "paper_type": "新高考I卷",
        "total_score": 150,
        "duration_min": 120,
        "target_difficulty": 0.55,
        "sections": [
            {"key": "single", "label": "一、单项选择题", "qtype": "single", "count": 8, "score": 5,
             "hint": "本题共 8 小题，每小题 5 分，共 40 分。"},
            {"key": "multi", "label": "二、多项选择题", "qtype": "multi", "count": 3, "score": 6,
             "hint": "本题共 3 小题，每小题 6 分，共 18 分。全部选对得 6 分，部分选对得部分分。"},
            {"key": "blank", "label": "三、填空题", "qtype": "blank", "count": 3, "score": 5,
             "hint": "本题共 3 小题，每小题 5 分，共 15 分。"},
            {"key": "solve", "label": "四、解答题", "qtype": "solve", "count": 5,
             "scores": [13, 15, 15, 17, 17], "hint": "本题共 5 小题，共 77 分。解答应写出文字说明、证明过程或演算步骤。"},
        ],
        "cells": _cells({
            "M1.1": 5, "M1.2": 5, "M2.1": 10, "M2.2": 5, "M2.3": 15,
            "M3.2": 7, "M3.3": 15, "M4.1": 10, "M4.2": 7, "M6.2": 10,
            "M6.3": 12, "M7.1": 10, "M7.2": 10, "M7.3": 7, "M8.1": 10,
            "M8.2": 7, "M9.1": 5, "M9.2": 5,
        }, 150),
    },
    {
        "name": "全国甲卷（理）· 数学",
        "paper_type": "全国甲卷",
        "total_score": 150,
        "duration_min": 120,
        "target_difficulty": 0.55,
        "sections": [
            {"key": "single", "label": "一、选择题", "qtype": "single", "count": 12, "score": 5,
             "hint": "本题共 12 小题，每小题 5 分，共 60 分。"},
            {"key": "blank", "label": "二、填空题", "qtype": "blank", "count": 4, "score": 5,
             "hint": "本题共 4 小题，每小题 5 分，共 20 分。"},
            {"key": "solve", "label": "三、解答题", "qtype": "solve", "count": 6,
             "scores": [10, 12, 12, 12, 12, 12], "hint": "本题共 6 小题，共 70 分。"},
        ],
        "cells": _cells({
            "M1.1": 5, "M1.2": 5, "M2.1": 12, "M2.2": 8, "M2.3": 15,
            "M3.2": 10, "M3.3": 12, "M4.1": 12, "M4.2": 8, "M6.1": 5,
            "M6.2": 10, "M6.3": 10, "M7.1": 10, "M7.2": 10, "M7.3": 8,
            "M8.1": 8, "M8.2": 8, "M9.1": 6, "M9.2": 6,
        }, 150),
    },
    {
        "name": "基础检测卷（100 分）",
        "paper_type": "单元检测",
        "total_score": 100,
        "duration_min": 90,
        "target_difficulty": 0.72,
        "sections": [
            {"key": "single", "label": "一、选择题", "qtype": "single", "count": 8, "score": 4,
             "hint": "本题共 8 小题，每小题 4 分，共 32 分。"},
            {"key": "blank", "label": "二、填空题", "qtype": "blank", "count": 4, "score": 5,
             "hint": "本题共 4 小题，每小题 5 分，共 20 分。"},
            {"key": "solve", "label": "三、解答题", "qtype": "solve", "count": 4,
             "scores": [10, 12, 12, 14], "hint": "本题共 4 小题，共 48 分。"},
        ],
        "cells": _cells({
            "M1.1": 8, "M1.2": 8, "M2.1": 12, "M2.2": 8, "M2.3": 14,
            "M3.1": 8, "M3.2": 10, "M4.1": 12, "M5.1": 6, "M5.2": 6,
            "M7.1": 8, "M9.1": 5, "M9.2": 5,
        }, 100),
    },
]


def seed(conn: sqlite3.Connection) -> dict:
    for code, name, parent, level, sort in KNOWLEDGE:
        conn.execute(
            "INSERT OR IGNORE INTO knowledge_points(code,name,parent_code,level,sort,subject) VALUES(?,?,?,?,?,'math')",
            (code, name, parent, level, sort),
        )

    existing = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    if existing == 0:
        for q in QUESTIONS:
            conn.execute(
                """INSERT INTO questions(qtype,stem,options,answer,analysis,score,difficulty,
                       cognitive,knowledge_code,source,year,region,time_min,tags)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (q["qtype"], q["stem"], json.dumps(q["options"], ensure_ascii=False) if q["options"] else None,
                 q["answer"], q["analysis"], q["score"], q["difficulty"], q["cognitive"],
                 q["knowledge_code"], "知卷示例题库", q["year"], q["region"],
                 round(3 + (1 - q["difficulty"]) * 5, 1),
                 json.dumps(q["tags"], ensure_ascii=False)),
            )

    if conn.execute("SELECT COUNT(*) FROM blueprints").fetchone()[0] == 0:
        for b in BLUEPRINTS:
            conn.execute(
                """INSERT INTO blueprints(name,subject,paper_type,total_score,duration_min,
                       target_difficulty,sections,cells) VALUES(?,?,?,?,?,?,?,?)""",
                (b["name"], "math", b["paper_type"], b["total_score"], b["duration_min"],
                 b["target_difficulty"], json.dumps(b["sections"], ensure_ascii=False),
                 json.dumps(b["cells"], ensure_ascii=False)),
            )

    conn.commit()
    qn = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    bn = conn.execute("SELECT COUNT(*) FROM blueprints").fetchone()[0]
    return {"questions": qn, "blueprints": bn}
