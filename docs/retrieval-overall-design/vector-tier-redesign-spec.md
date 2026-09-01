# Spec: 向量检索 confidence-gated 分层权重设计

> **关联**：`docs/retrieval-overall-design/spec.md`（整体双循环架构）、`docs/hybrid-semantic-search/spec.md`（向量层 + fuzzy 层原始设计）
> **改动范围**：`graphify/hybrid_scorer.py`、`graphify/serve.py`、`graphify/hooks.py`、`.default-graphifyrc`、`tests/test_hybrid_search.py`
> **不改动**：`_score_query` 的 3 层词法 if/elif/elif 逻辑、trigram 预筛选、fuzzy tier、embedding 生成与存储

---

## 1. 背景与问题

### 1.1 当前设计：线性乘法导致"装饰性权重"

当前向量 tier 用**线性乘法**计算 bonus：

```python
_VECTOR_SIMILARITY_BONUS = 5.0
bonus = _VECTOR_SIMILARITY_BONUS × cosine_sim    # max = 5.0
```

量级对比：

| 通路 | 常量 | 最大贡献 | 占 EXACT 比例 |
|---|---|---|---|
| EXACT | 1000 × IDF | ~1000 | 100% |
| PREFIX | 100 × IDF | ~100 | 10% |
| **VECTOR（当前）** | **5.0 × sim** | **5.0** | **0.5%** |
| SUBSTRING | 1 × IDF | ~1 | 0.1% |
| FUZZY | 2.0 × JaroWinkler | ~2.0 | 0.2% |
| SOURCE | 0.5 × IDF | ~0.5 | 0.05% |

**问题**：VECTOR 最大只有 5.0，占 EXACT 的 0.5%。意味着只要词法有任何命中（哪怕是 SOURCE 的 0.5），vector 的贡献都可以被忽略。vector 实际只在"词法全零"时起作用——退化为 rescue-only。

### 1.2 业界对比：没有任何主流系统用 rescue-only

| 系统 | vector 权重 | vector 角色 | 融合方法 |
|---|---|---|---|
| **graphify（当前）** | max 5.0（0.5% of EXACT） | **rescue-only** | 线性加法 |
| llm_wiki | 50%（RRF 等权） | co-equal | RRF k=60 |
| Elasticsearch | 50%（默认等权） | co-equal | RRF k=60 |
| Weaviate | 75%（默认 α=0.75） | **dominant** | 归一化加权和 |
| Vespa | 50%（对称） | co-equal | reciprocal_rank_fusion |

Vespa 文档直接诊断了 graphify 的问题：

> "BM25 scores are not normalized (unbound) and the closeness score is normalized (0-1), **the BM25 scores will dominate the closeness score.**"

recalso.hashnode.dev 的分析定性：

> "If your BM25 scores run 4 to 18 and your cosine scores run 0.3 to 0.9, the lexical arm is doing roughly twenty times the work of the semantic arm, and **your 0.5 is decorative**."

graphify 的比例是 200:1（1000:5），比这个例子严重 10 倍。

### 1.3 核心洞察：权重应按 confidence (sim) 分层

线性乘法 `5.0 × sim` 的根本问题是：**sim=0.95（高置信）和 sim=0.51（弱相关）的权重比只有 5:3.3=1.5:1**，差距太小。而词法层 EXACT:PREFIX:SUBSTRING 是 1000:100:1，层次分明。

向量权重应该**映射到词法量级阶梯**：
- sim ≥ 0.85（高置信）→ PREFIX 级（~100），让语义查询能真正主导排序
- sim ~0.7（中等）→ SUBSTRING~PREFIX 之间（~10-20）
- sim ~0.5（弱相关）→ SUBSTRING~FUZZY 级（~2-5）
- sim < 0.4（噪声）→ 不贡献

---

## 2. 设计目标

| 目标 | 描述 |
|---|---|
| **G1 分层映射** | 向量权重按 sim 值分段映射到词法量级阶梯，而非线性乘法 |
| **G2 always-on** | vector 对所有 sim > 阈值的节点贡献分数，不限于"词法全零"时才触发 |
| **G3 精确查询安全** | 精确符号查询（EXACT 命中）仍由词法主导，vector 不干扰 |
| **G4 语义查询主导** | 自然语言查询（词法弱/零命中）时，高 sim 的 vector 能真正主导排序 |
| **G5 一致性增强** | 词法 + vector 双路命中的节点得分高于单路命中（保留 hybrid 的核心价值） |
| **G6 可配置阈值** | sim 分段阈值可通过 graphifyrc 配置，适配不同 embedding 模型的 sim 分布 |
| **G7 向后兼容** | 无 embedding sidecar 时降级为纯词法，行为不变 |
| **G8 测试可验证** | 每个分层的行为有对应测试用例 |

---

## 3. 分层映射设计

### 3.1 5 级 confidence 分层

| Tier | sim 范围 | tier_weight | 最大贡献 | 对应词法层 | 语义 |
|---|---|---|---|---|---|
| **T1** | sim ≥ 0.85 | **80** | 80×1.0=**80** | PREFIX 级 | 高置信语义匹配——"向量非常确定相关" |
| **T2** | 0.70 ≤ sim < 0.85 | **20** | 20×0.85=**17** | SUBSTRING~PREFIX 之间 | 中等语义匹配 |
| **T3** | 0.55 ≤ sim < 0.70 | **5** | 5×0.70=**3.5** | SUBSTRING 级 | 弱语义匹配 |
| **T4** | 0.40 ≤ sim < 0.55 | **1** | 1×0.55=**0.55** | FUZZY/SOURCE 级 | 边缘相关 |
| **T5** | sim < 0.40 | **0** | 0 | 不贡献 | 噪声，丢弃 |

### 3.2 分层公式

```
vector_bonus(sim) = tier_weight(sim) × sim

其中 tier_weight(sim) 是分段常量函数：
  sim ≥ 0.85  → 80
  0.70 ≤ sim < 0.85 → 20
  0.55 ≤ sim < 0.70 → 5
  0.40 ≤ sim < 0.55 → 1
  sim < 0.40  → 0
```

### 3.3 为什么仍然乘以 sim

在每个 tier 内部，bonus 仍然是 `tier_weight × sim`（不是只乘 tier_weight）。理由：

- **段内连续性**：sim=0.90 在 T1 内，bonus=80×0.90=72；sim=0.85 也在 T1，bonus=80×0.85=68。段内 sim 越高贡献越大，保留 magnitude 信号
- **段间跳变是 feature**：sim=0.85 时 bonus=68（T1），sim=0.84 时 bonus=20×0.84=16.8（T2）。跳变 4 倍——这是"从高置信降到中等置信"的合理惩罚
- **与 RRF 的对比**：RRF 完全丢弃 magnitude（sim=0.95 和 sim=0.51 如果都排第一，得相同分数）。分层方案保留 magnitude 信号，比 RRF 更精细

### 3.4 量级层级图（更新后）

```
EXACT        = 1000  ─────────────────────  词法精确层
PREFIX       = 100   ─────────────────      词法前缀层
VECTOR_T1    = 80×sim ≈ 68-80  ──────────  高置信语义（sim≥0.85）
SUBSTRING    = 1     ─                    词法子串层
VECTOR_T2    = 20×sim ≈ 14-17  ───────     中等语义（sim 0.70-0.85）
FUZZY        = 2     ─                    模糊容错层
VECTOR_T3    = 5×sim  ≈ 2.75-3.5  ──      弱语义（sim 0.55-0.70）
SOURCE       = 0.5   ─                    源文件层
VECTOR_T4    = 1×sim  ≈ 0.4-0.55  ─       边缘相关（sim 0.40-0.55）
VECTOR_T5    = 0     ─                    噪声（sim < 0.40），不贡献
```

**层次仍然分明**：EXACT > PREFIX > VECTOR_T1 > SUBSTRING > VECTOR_T2 > FUZZY > VECTOR_T3 > SOURCE > VECTOR_T4

### 3.5 关键场景验证

#### 场景 1：精确符号查询 `"UserService"`

```
节点 UserService:
  词法: EXACT = 1000 × IDF
  向量: T1(80) × 0.95 = 76
  总分: 1000×IDF + 76 ≈ 1076

节点 AuthService:
  词法: 0（无词法重叠）
  向量: T2(20) × 0.80 = 16
  总分: 16

结果: UserService(1076) >> AuthService(16) ✅ 精确查询由词法主导
```

#### 场景 2：自然语言查询 `"how does login work"`

```
节点 AuthService:
  词法: 0（login/auth 无词法重叠）
  向量: T1(80) × 0.90 = 72
  总分: 72

节点 Logger:
  词法: SUBSTRING("log" ∈ "logger") = 1 × IDF
  向量: T4(1) × 0.45 = 0.45
  总分: 1×IDF + 0.45 ≈ 1.45

结果: AuthService(72) >> Logger(1.45) ✅ 语义查询由向量主导
```

**当前设计（5.0×sim）会失败**：AuthService 得 5.0×0.90=4.5，Logger 得 1×IDF+5.0×0.45≈3.5。差距只有 1.0，排序优势不够——如果 Logger 的 IDF 稍高，Logger 就会排到 AuthService 前面。

#### 场景 3：双路一致增强 `"auth service"`

```
节点 AuthService:
  词法: EXACT("auth") + SUBSTRING("service") ≈ 1000×IDF + 1×IDF
  向量: T1(80) × 0.92 = 73.6
  总分: 1001×IDF + 73.6

节点 UserAuthService:
  词法: PREFIX("auth") + SUBSTRING("service") ≈ 100×IDF + 1×IDF
  向量: T1(80) × 0.88 = 70.4
  总分: 101×IDF + 70.4

结果: AuthService(双路高分) > UserAuthService(词法低+向量高) ✅ 一致性增强保留
```

#### 场景 4：Issue #2 的 Q1 `"当前事件分域的方案是什么"`

```
节点 Domain（分域）:
  词法: bigram "分域" SUBSTRING 命中 = 1.0 × IDF=6.48 = 6.48
  向量: T3(5) × 0.66 = 3.3（sim=0.66 落在 T3）
  总分: 6.48 + 3.3 = 9.78

节点 EventDomainMapping:
  词法: 0
  向量: T3(5) × 0.6635 = 3.32
  总分: 3.32

结果: Domain(9.78) > EventDomainMapping(3.32) ✅
```

**与当前设计对比**：当前 Domain 得 6.48 + 5.0×0.66=3.3 = 9.78（相同），EventDomainMapping 得 3.32（相同）。这个场景下分层方案与当前方案结果一致——因为 sim=0.66 落在 T3，tier_weight=5，与当前 `_VECTOR_SIMILARITY_BONUS=5.0` 恰好相同。

**差异出现在高 sim 场景**：如果 EventDomainMapping 的 sim=0.90，当前设计得 5.0×0.90=4.5（仍 < Domain 的 6.48），分层设计得 80×0.90=72（远 > Domain 的 6.48+3.3=9.78）——高置信语义匹配能正确主导排序。

---

## 4. 阈值设计依据

### 4.1 为什么选 0.85 / 0.70 / 0.55 / 0.40

阈值选择基于常见 embedding 模型的 sim 分布特征：

| sim 范围 | 语义关系 | 依据 |
|---|---|---|
| ≥ 0.85 | 近乎同义/强语义匹配 | OpenAI text-embedding-3-small 对同义不同形的 query-doc 对（如 "login" vs "authentication service"）通常落在 0.85-0.95 |
| 0.70-0.85 | 相关但非同义 | 同领域不同功能的节点（如 "AuthService" vs "TokenService"）通常落在 0.70-0.85 |
| 0.55-0.70 | 弱相关 | 同一子系统但功能差异大的节点 |
| 0.40-0.55 | 边缘/巧合 | 可能是 embedding 模型的噪声区间 |
| < 0.40 | 噪声 | 大多数 embedding 模型的 sim 在 0.4 以下不具备语义参考价值 |

### 4.2 不同模型的 sim 分布差异

不同 embedding 模型的 sim 绝对值分布不同：

| 模型 | 典型相关 sim | 典型弱相关 sim | 建议调整 |
|---|---|---|---|
| OpenAI text-embedding-3-small | 0.75-0.95 | 0.45-0.65 | 默认阈值适用 |
| sentence-transformers paraphrase-multilingual-MiniLM-L12-v2 | 0.50-0.80 | 0.25-0.45 | 阈值应降低 |
| BGE-large-zh-v1.5 | 0.60-0.85 | 0.30-0.50 | 阈值应降低 |
| Ollama nomic-embed-text | 0.55-0.80 | 0.30-0.50 | 阈值应降低 |

**默认阈值面向 OpenAI 兼容模型**。使用 sentence-transformers 等模型时，建议通过 graphifyrc 降低阈值（见 §6）。

### 4.3 为什么不选 RRF

RRF 的优势是零配置、scale-invariant。但它有一个关键缺陷：**完全丢弃 magnitude 信号**。

| 场景 | RRF | 分层方案 |
|---|---|---|
| sim=0.95 和 sim=0.51 都排第一 | 得相同分数 1/61 | sim=0.95 得 76，sim=0.51 得 2.55——差 30 倍 |
| 词法全零时两个 vector 候选 | rank 决定排序，magnitude 不参与 | sim 高的显著高于 sim 低的 |

在 graphify 的场景下（代码图谱 + 自然语言查询），magnitude 信号有价值——"向量非常确定相关"（sim=0.95）和"向量弱相关"（sim=0.51）应该有显著不同的权重。RRF 丢弃了这个信号。

**结论**：分层方案在保留排序信号方面优于 RRF，在避免 scale 不兼容方面优于线性加权。

---

## 5. 叠加公式

### 5.1 更新后的叠加公式

```
total = EXACT × IDF × coverage²      (词法精确层)
      + PREFIX × IDF × coverage²     (词法前缀层)
      + SUBSTRING × IDF              (子串层，不乘 coverage)
      + SOURCE × IDF                 (源文件层，不乘 coverage)
      + FUZZY × IDF                  (模糊层)
      + tier_weight(sim) × sim       (向量层，confidence-gated)
```

### 5.2 向量层不乘 IDF / coverage²

| 乘法因子 | 是否作用于向量层 | 理由 |
|---|---|---|
| IDF | **不乘** | vector sim 是对整个 query 字符串一次性 embed 计算的，不是 per-term 的。没有 per-term IDF 可乘 |
| coverage² | **不乘** | coverage = matched_terms / total_terms 是 per-term 概念。vector 是全 query 级别的一次相似度计算，不存在"匹配了几个 term" |

### 5.3 与 coverage² 的交互

coverage² 只作用于 EXACT 和 PREFIX 两个词法层。向量层不乘 coverage²，理由：

- 向量 sim 是"query 整体与节点 desc 的语义相似度"，不是"query 的某个 term 命中了节点的 label"
- 如果乘 coverage²，当 query 有 5 个 term 只有 1 个 term 命中 label 时，coverage=1/5，coverage²=1/25，vector bonus 会被压到 1/25——这不合理，因为 vector sim 衡量的是整体语义相关度，不受 per-term label 匹配数影响

---

## 6. 可配置性

### 6.1 graphifyrc 配置

新增 `vector_sim_tiers` 配置项，格式为逗号分隔的 4 个阈值（降序）：

```ini
# .graph/graphifyrc

# 向量检索 confidence-gated 分层权重阈值
# 格式: t1,t2,t3,t4（降序，0 < t4 < t3 < t2 < t1 ≤ 1.0）
# 对应 5 个 tier: [t1, 1.0] / [t2, t1) / [t3, t2) / [t4, t3) / [0, t4)
# 默认: 0.85,0.70,0.55,0.40（适配 OpenAI text-embedding-3-small）
#
# sentence-transformers 用户建议降低阈值:
# vector_sim_tiers = 0.65,0.50,0.35,0.20
vector_sim_tiers = 0.85,0.70,0.55,0.40
```

### 6.2 tier_weight 的可配置性

tier_weight（80/20/5/1/0）**暂不可配置**，理由：

- tier_weight 是映射到词法量级阶梯的设计，与 EXACT=1000/PREFIX=100/SUBSTRING=1 的关系是固定的
- 暴露 tier_weight 配置会让调参空间过大，且容易破坏量级层次
- 如果未来需要调参，可以通过 benchmark fixture 验证后开放

### 6.3 默认值表

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `vector_sim_tiers` | `0.85,0.70,0.55,0.40` | 4 个 sim 阈值，适配 OpenAI 兼容模型 |

---

## 7. 实现变更

### 7.1 `graphify/hybrid_scorer.py`

#### 替换常量为分层函数

**删除**：
```python
_VECTOR_SIMILARITY_BONUS = 5.0
```

**新增**：
```python
# Confidence-gated tier weights for vector similarity.
# Each tier maps to a band in the lexical scoring hierarchy:
#   T1 (sim ≥ 0.85): 80  — PREFIX-level (semantic high-confidence)
#   T2 (0.70-0.85): 20  — between SUBSTRING and PREFIX
#   T3 (0.55-0.70): 5   — SUBSTRING-level
#   T4 (0.40-0.55): 1   — FUZZY/SOURCE-level
#   T5 (< 0.40):    0   — noise, discarded
#
# The bonus is tier_weight × sim (not tier_weight alone) so magnitude
# is preserved within each tier and there's a deliberate jump at tier
# boundaries (confidence-level transitions).
#
# See docs/retrieval-overall-design/vector-tier-redesign-spec.md

# Default sim thresholds (configurable via graphifyrc vector_sim_tiers).
# Adapted for OpenAI-compatible embedding models. Lower these for
# sentence-transformers / BGE models (see spec §4.2).
_DEFAULT_VECTOR_SIM_TIERS = (0.85, 0.70, 0.55, 0.40)
_VECTOR_TIER_WEIGHTS = (80.0, 20.0, 5.0, 1.0, 0.0)


def _vector_tier_weight(sim: float, tiers: tuple[float, ...] = _DEFAULT_VECTOR_SIM_TIERS) -> float:
    """Return the tier_weight for a cosine similarity value.

    Tiers (configurable via graphifyrc vector_sim_tiers):
        sim ≥ tiers[0]      → 80.0  (T1: high-confidence, PREFIX-level)
        tiers[1] ≤ sim < tiers[0] → 20.0  (T2: medium, SUBSTRING~PREFIX)
        tiers[2] ≤ sim < tiers[1] → 5.0   (T3: weak, SUBSTRING-level)
        tiers[3] ≤ sim < tiers[2] → 1.0   (T4: marginal, FUZZY-level)
        sim < tiers[3]      → 0.0   (T5: noise, discarded)

    The caller multiplies this by sim to get the final bonus:
        bonus = _vector_tier_weight(sim) × sim
    """
    if sim >= tiers[0]:
        return _VECTOR_TIER_WEIGHTS[0]
    if sim >= tiers[1]:
        return _VECTOR_TIER_WEIGHTS[1]
    if sim >= tiers[2]:
        return _VECTOR_TIER_WEIGHTS[2]
    if sim >= tiers[3]:
        return _VECTOR_TIER_WEIGHTS[3]
    return _VECTOR_TIER_WEIGHTS[4]
```

#### 更新 `HybridScorer`

```python
class HybridScorer:
    def __init__(
        self,
        graph_dir: str | Path | None = None,
        *,
        embed_backend: str | None = None,
        embed_model: str | None = None,
    ) -> None:
        # ... 既有初始化 ...
        # NEW: load vector_sim_tiers from graphifyrc
        self._vector_sim_tiers = self._load_vector_sim_tiers()

    def _load_vector_sim_tiers(self) -> tuple[float, ...]:
        """Load vector_sim_tiers from graphifyrc, falling back to defaults."""
        rc_cfg = _load_embed_config_from_graphifyrc(self._graph_dir)
        raw = rc_cfg.get("vector_sim_tiers", "").strip()
        if not raw:
            return _DEFAULT_VECTOR_SIM_TIERS
        try:
            parts = [float(x.strip()) for x in raw.split(",")]
            if len(parts) != 4:
                raise ValueError(f"expected 4 values, got {len(parts)}")
            if not (0 < parts[3] < parts[2] < parts[1] < parts[0] <= 1.0):
                raise ValueError(f"must be ascending in (0, 1.0]: {parts}")
            return tuple(parts)
        except (ValueError, TypeError) as exc:
            # Fall back to defaults on parse error — don't crash queries
            return _DEFAULT_VECTOR_SIM_TIERS

    @staticmethod
    def vector_bonus(sim: float, tiers: tuple[float, ...] = _DEFAULT_VECTOR_SIM_TIERS) -> float:
        """Vector tier bonus for a cosine similarity value.

        Confidence-gated: tier_weight × sim. See spec §3.
        """
        return _vector_tier_weight(sim, tiers) * float(sim)
```

### 7.2 `graphify/serve.py`

#### `_score_query` post-loop Pass 2（L715-720）

**修改前**：
```python
if query_embedding_scores:
    for nid, vec_sim in query_embedding_scores.items():
        if vec_sim <= 0:
            continue
        bonus = _VECTOR_SIMILARITY_BONUS * vec_sim
        score_by_nid[nid] = score_by_nid.get(nid, 0.0) + bonus
```

**修改后**：
```python
if query_embedding_scores:
    # Get the tier config from the hybrid scorer if available
    tiers = (
        hybrid_scorer._vector_sim_tiers
        if hybrid_scorer is not None
        else _DEFAULT_VECTOR_SIM_TIERS
    )
    for nid, vec_sim in query_embedding_scores.items():
        if vec_sim <= 0:
            continue
        bonus = _vector_tier_weight(vec_sim, tiers) * vec_sim
        score_by_nid[nid] = score_by_nid.get(nid, 0.0) + bonus
```

#### import 变更

```python
# 修改前:
from graphify.hybrid_scorer import HybridScorer, _VECTOR_SIMILARITY_BONUS

# 修改后:
from graphify.hybrid_scorer import (
    HybridScorer,
    _vector_tier_weight,
    _DEFAULT_VECTOR_SIM_TIERS,
)
```

### 7.3 `graphify/hooks.py`

#### `_parse_graphifyrc_file` 新增 `vector_sim_tiers` 解析

```python
elif key == "vector_sim_tiers":
    # Comma-separated 4 floats, e.g. "0.85,0.70,0.55,0.40"
    # Validation (ascending order, 4 values, in (0, 1.0]) is deferred
    # to HybridScorer._load_vector_sim_tiers at query time — here we
    # just store the raw string.
    cfg["vector_sim_tiers"] = val
```

### 7.4 `.default-graphifyrc`

```ini
# --- Vector Tier Confidence-Gated Weighting -------------------------------
# Sim thresholds for the 5 confidence tiers of vector retrieval.
# Format: t1,t2,t3,t4 (descending, 0 < t4 < t3 < t2 < t1 ≤ 1.0)
#   T1 [t1, 1.0]     → weight 80  (PREFIX-level, high-confidence semantic)
#   T2 [t2, t1)      → weight 20  (medium semantic)
#   T3 [t3, t2)      → weight 5   (SUBSTRING-level, weak semantic)
#   T4 [t4, t3)      → weight 1   (FUZZY-level, marginal)
#   T5 [0, t4)       → weight 0   (noise, discarded)
#
# Defaults below suit OpenAI-compatible models (text-embedding-3-small etc).
# For sentence-transformers / BGE models, lower thresholds, e.g.:
#   vector_sim_tiers = 0.65,0.50,0.35,0.20
# vector_sim_tiers = 0.85,0.70,0.55,0.40
```

### 7.5 `tests/test_hybrid_search.py`

#### 更新测试期望

```python
class TestBonusConstants:
    def test_vector_tier_weight_mapping(self) -> None:
        """Spec §3.1: tier_weight maps sim to lexical hierarchy."""
        from graphify.hybrid_scorer import _vector_tier_weight, _DEFAULT_VECTOR_SIM_TIERS

        # T1: sim >= 0.85 → 80
        assert _vector_tier_weight(0.90) == 80.0
        assert _vector_tier_weight(0.85) == 80.0
        assert _vector_tier_weight(1.00) == 80.0

        # T2: 0.70 <= sim < 0.85 → 20
        assert _vector_tier_weight(0.80) == 20.0
        assert _vector_tier_weight(0.70) == 20.0

        # T3: 0.55 <= sim < 0.70 → 5
        assert _vector_tier_weight(0.60) == 5.0
        assert _vector_tier_weight(0.55) == 5.0

        # T4: 0.40 <= sim < 0.55 → 1
        assert _vector_tier_weight(0.45) == 1.0
        assert _vector_tier_weight(0.40) == 1.0

        # T5: sim < 0.40 → 0
        assert _vector_tier_weight(0.30) == 0.0
        assert _vector_tier_weight(0.0) == 0.0

    def test_vector_bonus_formula(self) -> None:
        """Spec §3.2: bonus = tier_weight × sim (not tier_weight alone)."""
        # T1: 80 × 0.90 = 72.0
        assert HybridScorer.vector_bonus(0.90) == pytest.approx(80.0 * 0.90)
        # T2: 20 × 0.75 = 15.0
        assert HybridScorer.vector_bonus(0.75) == pytest.approx(20.0 * 0.75)
        # T3: 5 × 0.60 = 3.0
        assert HybridScorer.vector_bonus(0.60) == pytest.approx(5.0 * 0.60)
        # T4: 1 × 0.45 = 0.45
        assert HybridScorer.vector_bonus(0.45) == pytest.approx(1.0 * 0.45)
        # T5: 0 × sim = 0
        assert HybridScorer.vector_bonus(0.30) == 0.0
        assert HybridScorer.vector_bonus(0.0) == 0.0

    def test_high_confidence_vector_dominates_weak_lexical(self) -> None:
        """Spec §3.5 场景 2: semantic query where vector should dominate."""
        G = _build_small_graph()
        # 'login' has zero lexical overlap with AuthService
        # But sim=0.90 (T1) should give 80×0.90=72, dominating any
        # incidental SUBSTRING hit on other nodes
        query_emb = {"authservice": 0.90, "userservice": 0.30, "throttleservice": 0.05}
        scored = _score_query(
            G, ["login"],
            collect_per_term_seeds=False,
            query_embedding_scores=query_emb, semantic=True,
        )
        assert scored.ranked[0][1] == "authservice"
        # Bonus = 80 × 0.90 = 72.0 (T1 high-confidence)
        assert scored.ranked[0][0] == pytest.approx(72.0, rel=0.01)

    def test_medium_confidence_vector_below_prefix(self) -> None:
        """Spec §3.1: T2 (sim 0.70-0.85) bonus stays below PREFIX(100)."""
        G = _build_small_graph()
        # sim=0.75 → T2, bonus = 20 × 0.75 = 15.0
        query_emb = {"authservice": 0.75}
        scored = _score_query(
            G, ["login"],
            collect_per_term_seeds=False,
            query_embedding_scores=query_emb, semantic=True,
        )
        assert scored.ranked[0][0] == pytest.approx(15.0, rel=0.01)

    def test_noise_sim_does_not_contribute(self) -> None:
        """Spec §3.1 T5: sim < 0.40 contributes 0."""
        G = _build_small_graph()
        query_emb = {"authservice": 0.35, "userservice": 0.20}
        scored = _score_query(
            G, ["login"],
            collect_per_term_seeds=False,
            query_embedding_scores=query_emb, semantic=True,
        )
        # Both below T4 threshold (0.40) → 0 bonus → no results
        assert not scored.ranked

    def test_precise_query_still_exact_dominated(self) -> None:
        """Spec §3.5 场景 1: EXACT(1000) still dominates VECTOR_T1(80)."""
        G = _build_small_graph()
        query_emb = {"userservice": 0.95, "authservice": 0.10}
        scored = _score_query(
            G, ["userservice"],
            collect_per_term_seeds=False,
            query_embedding_scores=query_emb, semantic=True,
        )
        # UserService top-1 (EXACT dominates)
        assert scored.ranked[0][1] == "userservice"
        # Score = EXACT(1000×IDF) + vector(80×0.95=76) > pure lexical
        pure = _score_query(G, ["userservice"], collect_per_term_seeds=False)
        assert scored.ranked[0][0] > pure.ranked[0][0]

    def test_agreement_boost_preserved(self) -> None:
        """Spec §3.5 场景 3: lexical + vector double-hit scores higher."""
        G = _build_small_graph()
        # 'user' matches 'userservice' via PREFIX (100×IDF)
        # AND vector sim=0.90 (T1, 80×0.90=72)
        query_emb = {"userservice": 0.90, "authservice": 0.10}
        scored = _score_query(
            G, ["user"],
            collect_per_term_seeds=False,
            query_embedding_scores=query_emb, semantic=True,
        )
        assert scored.ranked[0][1] == "userservice"
        # Score includes both PREFIX + VECTOR_T1 (agreement boost)
        pure = _score_query(G, ["user"], collect_per_term_seeds=False)
        assert scored.ranked[0][0] > pure.ranked[0][0]  # vector added
```

---

## 8. 非目标

- **不改动 3 层词法逻辑**（EXACT/PREFIX/SUBSTRING 的 if/elif/elif 不变）
- **不改动 trigram 预筛选**
- **不改动 fuzzy tier**（`_FUZZY_MATCH_BONUS=2.0` 保持不变）
- **不改动 coverage² 公式**（仍只作用于 EXACT/PREFIX）
- **不引入 RRF**（分层方案保留 magnitude 信号，比 RRF 更适合 graphify 场景）
- **不改动 embedding 生成与存储**（`.npy` / `.index.json` / `.meta.json` 格式不变）
- **不开放 tier_weight 可配置**（80/20/5/1/0 固定，只开放 sim 阈值可配置）

---

## 9. 验收标准

| ID | 标准 | 验证方式 |
|---|---|---|
| AC1 | `_vector_tier_weight(0.90)` 返回 80.0（T1） | 单元测试 |
| AC2 | `_vector_tier_weight(0.75)` 返回 20.0（T2） | 单元测试 |
| AC3 | `_vector_tier_weight(0.60)` 返回 5.0（T3） | 单元测试 |
| AC4 | `_vector_tier_weight(0.45)` 返回 1.0（T4） | 单元测试 |
| AC5 | `_vector_tier_weight(0.30)` 返回 0.0（T5） | 单元测试 |
| AC6 | `HybridScorer.vector_bonus(0.90)` == 80.0 × 0.90 = 72.0 | 单元测试 |
| AC7 | `HybridScorer.vector_bonus(0.30)` == 0.0（噪声不贡献） | 单元测试 |
| AC8 | 精确查询 `"UserService"` 仍排第一（EXACT 主导） | 集成测试 |
| AC9 | 语义查询 `"login"`（sim=0.90）的 AuthService 得分 ≈ 72.0，高于任何词法弱命中 | 集成测试 |
| AC10 | sim < 0.40 的节点不进入候选（bonus=0） | 集成测试 |
| AC11 | `vector_sim_tiers` 配置在 graphifyrc 中生效 | 配置测试 |
| AC12 | 配置格式错误时回退到默认阈值，不崩溃 | 配置测试 |
| AC13 | 无 embedding sidecar 时降级为纯词法，行为不变 | 集成测试 |
| AC14 | `semantic=false` 时完全跳过向量层 | 集成测试 |
| AC15 | 双路命中（词法 + 高 sim vector）的节点得分高于单路命中 | 集成测试 |

---

## 10. 风险

| 风险 | 缓解 |
|---|---|
| 阈值不适配 sentence-transformers（sim 分布更低） | `vector_sim_tiers` 可配置；文档给出 sentence-transformers 建议值（0.65/0.50/0.35/0.20） |
| T1 权重 80 在某些场景压过 PREFIX(100) | 80 < 100，PREFIX 仍高于 T1；且 PREFIX 乘 coverage² 后对多词精确查询更强 |
| 分段边界跳变导致排序不稳定 | 边界跳变是 feature（confidence 级别转换）；sim 值在 0.85 附近波动是 embedding 模型本身的特性，不是分层方案引入的 |
| 高 sim 节点过多导致候选集膨胀 | T1(sim≥0.85) 在实际 embedding 模型中是少数；T4/T5 过滤掉了大部分低相关节点 |
| 与既有 benchmark fixture 的 sim 分布不匹配 | benchmark fixture 使用 sentence-transformers，需同步调整 `vector_sim_tiers` 或 fixture 的 expected sim 值 |

---

## 11. 实施顺序

1. `hybrid_scorer.py`：新增 `_vector_tier_weight()` + `_DEFAULT_VECTOR_SIM_TIERS` + `_VECTOR_TIER_WEIGHTS`；更新 `HybridScorer.vector_bonus()`；新增 `_load_vector_sim_tiers()`
2. `hooks.py`：`_parse_graphifyrc_file` 新增 `vector_sim_tiers` 解析
3. `.default-graphifyrc`：文档化 `vector_sim_tiers` 配置
4. `serve.py`：更新 import；更新 Pass 2 调用为 `_vector_tier_weight(sim, tiers) × sim`
5. `tests/test_hybrid_search.py`：更新 `TestBonusConstants` 和 `TestScoreQueryVectorTier`
6. 运行测试验证：`pytest tests/test_hybrid_search.py -q`
7. 运行 benchmark：`python tests/fixtures/search_benchmark/run_benchmark.py`

---

## 12. 关键设计决策记录

| 决策 | 选择 | 理由 |
|---|---|---|
| vector 权重是线性还是分层 | **分层** | 线性 `5.0×sim` 导致装饰性权重（0.5% of EXACT）；分层让高 sim 拿 PREFIX 级权重，低 sim 拿 FUZZY 级 |
| 分几层 | **5 层** | 5 层覆盖了从"高置信"到"噪声"的完整区间，且映射到词法量级阶梯（PREFIX/SUBSTRING/FUZZY/SOURCE/0） |
| 段内是否乘 sim | **乘** | 保留 magnitude 信号；段间跳变是 confidence 级别转换的 feature |
| 阈值默认值 | **0.85/0.70/0.55/0.40** | 适配 OpenAI 兼容模型；sentence-transformers 可通过 graphifyrc 降低 |
| tier_weight 是否可配置 | **不可配置** | tier_weight 与词法量级阶梯的关系是设计约束，暴露会破坏层次 |
| 是否引入 RRF | **不引入** | RRF 丢弃 magnitude 信号；分层方案在保留信号方面更优 |
| 向量层是否乘 IDF | **不乘** | vector sim 是全 query 级别的一次计算，不是 per-term |
| 向量层是否乘 coverage² | **不乘** | coverage 是 per-term 概念，vector 是整体语义相似度 |
| 向量层是 always-on 还是 rescue-only | **always-on** | 业界共识：rescue-only 丢失一致性增强信号；always-on 保留双路加成 |

---

## 13. 参考文献

- [Issue #2 评论](https://github.com/xuanxuancmd/graphify/issues/2#issuecomment-5488722635) — 原始双循环 + 7 通路设计
- `docs/retrieval-overall-design/spec.md` — 整体检索架构
- `docs/hybrid-semantic-search/spec.md` — 向量层原始设计（`_VECTOR_SIMILARITY_BONUS=5.0` 的来源）
- [llm_wiki search.rs](https://github.com/nashsu/llm_wiki/blob/caff7f2ac360b7c2fc926cafd1be86b0208ffe0d/src-tauri/src/commands/search.rs) — RRF k=60 co-equal 实现
- [Vespa hybrid tutorial](https://docs.vespa.ai/en/learn/tutorials/hybrid-search.html) — scale 不兼容的诊断
- [recalso.hashnode.dev](https://recalso.hashnode.dev/your-hybrid-retriever-is-fusing-scores-that-were-never-on-the-same-scale) — "装饰性权重"定性
- [VLDB 2025 Gao et al.](https://www.vldb.org/pvldb/vol19/p1715-gao.pdf) — "weakest link" 反模式
- [Weaviate hybrid docs](https://docs.weaviate.io/weaviate/concepts/search/hybrid-search) — α=0.75 默认向量主导
- `serve.py:290-293` — 词法常量定义
- `serve.py:715-720` — 当前 vector bonus 计算（`_VECTOR_SIMILARITY_BONUS × vec_sim`）
- `hybrid_scorer.py:33` — `_VECTOR_SIMILARITY_BONUS = 5.0`（将被替换）
