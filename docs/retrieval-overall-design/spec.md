# Spec: 检索整体方案设计（双循环 + 7 通路加法打分）

> **来源**：[xuanxuancmd/graphify#issuecomment-5488722635](https://github.com/xuanxuancmd/graphify/issues/2#issuecomment-5488722635)
> **关联**：`docs/hybrid-semantic-search/spec.md`（向量层 + fuzzy 层的详细设计与 embedding 存储）、`docs/hybrid-semantic-search/plan.md`（逐步实施清单）
> **适用范围**：`graphify query` / MCP `query_graph` / `_query_graph_text` / `_score_query`

---

## 1. 背景与问题

graphify 的查询检索分为两个阶段：**召回**（从全图 N 个节点里筛出与 query 相关的种子）与 **遍历**（BFS/DFS 从种子出发扩展子图）。召回质量决定了遍历是否有意义——BFS 再强大，找不到种子就是空跑。

召回的核心是 `_score_query`（`serve.py:462-629`），它给每个节点打一个分数，按分数排序取 top-K 作为种子。这个打分函数的设计直接决定了：

- **精确查询**（用户输入精确类名 `"UserService"`）能否正确排到第一
- **模糊查询**（`"how does login work?"`）能否召回语义相关但词形零重叠的节点
- **拼写错误**（`"UserServise"`）能否容错
- **性能**：N 个节点不能全量 O(N×Q) 暴力打分，需要预筛选

本 spec 描述整体检索方案：**双循环架构 + 7 通路加法打分 + coverage² 缩放**，覆盖从预筛选到最终排序的完整链路。

---

## 2. 整体架构：双循环检索

检索不是一次性遍历全图，而是分两个循环：

```
                        query 字符串
                             │
                             ▼
                ┌────────────────────────┐
                │  分词 + bigram (CJK)    │
                │  生成 query trigrams    │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │  trigram 预筛选         │  ← 性能优化：O(N) → O(候选集)
                │  用 query trigrams 与   │
                │  每个节点的 trigram 索引 │
                │  求交集，非空者进入主循环 │
                └───────────┬────────────┘
                            │
              ┌─────────────┴──────────────┐
              ▼                            ▼
   ┌────────────────────┐      ┌─────────────────────────┐
   │  主循环             │      │  后循环（救援）          │
   │  (trigram 放行的    │      │  (trigram 排除的节点)    │
   │   候选节点)         │      │                         │
   │                    │      │                         │
   │  通路 1-5：         │      │  通路 6 + 5'：           │
   │  EXACT / PREFIX /  │      │  VECTOR (语义救援) +     │
   │  SUBSTRING /       │      │  FUZZY rescue (拼写救援) │
   │  SOURCE / FUZZY    │      │                         │
   └─────────┬──────────┘      └────────────┬────────────┘
             │                               │
             └───────────────┬───────────────┘
                             ▼
                ┌────────────────────────┐
                │  合并分数 + 排序        │
                │  取 top-K 种子          │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │  BFS / DFS 遍历         │
                │  扩展子图 → 输出文本     │
                └────────────────────────┘
```

### 2.1 为什么分两个循环

**主循环**（trigram 预筛选后的节点）：trigram 索引保证候选节点与 query 至少有 1 个字符三元组重叠，是**可能有词法匹配**的节点。对这批节点跑 5 通路词法打分，是性能与召回的平衡——只评分可能匹配的节点，跳过显然无关的节点。

**后循环/救援循环**（trigram 预筛选排除的节点）：trigram 预筛选是保守的——它要求字符三元组重叠，但语义相关往往**字符零重叠**（如 `"login"` vs `AuthService`）。如果只靠主循环，这些语义相关节点永远不会被召回。后循环用向量相似度和模糊匹配把被 trigram 排除的语义相关节点**捞回来**。

> **关键洞察**：trigram 预筛选是性能优化手段，不是召回质量的保证。救援循环的存在恰恰说明预筛选会误杀——它的存在是为了弥补预筛选的召回损失。

---

## 3. 打分通路设计

### 3.1 主循环：5 通路词法打分（trigram 放行的候选节点）

| # | 通路 | 常量 | 量级 | 触发条件 |
|---|---|---|---|---|
| 1 | EXACT | 1000 × IDF | ~1000 | 查询词 == 节点标签 |
| 2 | PREFIX | 100 × IDF | ~100 | 节点标签以查询词开头 |
| 3 | SUBSTRING | 1 × IDF | ~1 | 查询词是节点标签子串 |
| 4 | SOURCE | 0.5 × IDF | ~0.5 | 查询词出现在 source_file 路径 |
| 5 | FUZZY | JaroWinkler × bonus × IDF | ~0-1 | 上述三层全未命中时，模糊匹配（容错拼写） |

**设计要点**：

- **EXACT(1000) >> PREFIX(100) >> SUBSTRING(1)**：层次清晰的量级阶梯，精确匹配压倒前缀，前缀压倒子串
- **SOURCE(0.5)**：文件路径命中是弱信号，低于 SUBSTRING，因为路径片段容易巧合
- **FUZZY**：仅当 EXACT/PREFIX/SUBSTRING 三层全未命中时触发，避免干扰精确匹配；用于容错拼写（如 `"UserServise"` → `"UserService"`）
- **IDF 加权**：稀有词命中得分高于通用词，防止 `"the"` 这种高频词精确匹配拿到不合理高分

### 3.2 后循环：2 通路救援打分（trigram 排除的节点）

| # | 通路 | 常量 | 量级 | 作用 |
|---|---|---|---|---|
| 6 | VECTOR | 5.0 × cosine_sim | 0~5 | 语义救援：零词法重叠也能召回 |
| 5' | FUZZY rescue | 同 FUZZY（JaroWinkler × bonus × IDF） | ~0-1 | 拼写容错救援：trigram 未放行的节点 |

**设计要点**：

- **VECTOR 是兜底**：只在词法全零时起决定作用，否则只是微调（5.0 vs 100/1000）。`_VECTOR_SIMILARITY_BONUS = 5.0` 介于 SUBSTRING(1) 和 PREFIX(100) 之间——足以把零分节点拉进候选，但不会压过词法命中的节点
- **FUZZY rescue**：与主循环的 FUZZY 同算法，但作用对象不同——主循环 FUZZY 作用于 trigram 放行的节点，rescue FUZZY 作用于 trigram 排除的节点。两者互补，覆盖所有节点的拼写容错
- **VECTOR 救援的触发条件**：`semantic != false` 且 embedding sidecar 存在且 query embed 成功。无 sidecar 时降级为纯词法，不报错

---

## 4. 叠加公式

所有通路是**加法叠加**，最终得分 = Σ(每路贡献)：

```
total = EXACT × IDF × coverage²      (词法精确层)
      + PREFIX × IDF × coverage²     (词法前缀层)
      + SUBSTRING × IDF              (子串层，不乘 coverage)
      + SOURCE × IDF                 (源文件层，不乘 coverage)
      + FUZZY × IDF                  (模糊层)
      + VECTOR_SIMILARITY_BONUS × cosine_sim  (向量层)
```

### 4.1 为什么是加法而非替换

| 方案 | 优点 | 缺点 |
|---|---|---|
| 替换词法为纯语义 | 召回最高 | 精确查询（用户输入精确类名）时排序不如 EXACT |
| **加法叠加（选）** | 精确查询时词法 EXACT 主导；模糊查询时语义/fuzzy 补偿 | 分数混合需调参 |
| 纯 fuzzy | 拼写容错 | 无语义理解 |

**加法的设计效果**：

- 精确查询 `"UserService"` → EXACT × 1000 主导，向量分 5.0 × 0.9 ≈ 4.5 可忽略
- 模糊查询 `"authentication"` → 词法 0，向量分 5.0 × 0.85 = 4.25 > 0，节点进入候选
- 拼写错误 `"UserServise"` → 词法 0，fuzzy 分 2.0 × 0.93 = 1.86 > 0，节点进入候选

### 4.2 EXACT/PREFIX 乘 coverage²，SUBSTRING/SOURCE 不乘

**coverage** = matched_terms / total_terms，是查询词中命中节点标签的比例。

- **EXACT/PREFIX 乘 coverage²**：防止单个高频词精确匹配压过多词部分命中。例如 query `"user auth service"` 有 3 个词，如果只有 `"service"` 精确匹配，coverage = 1/3，coverage² = 1/9，EXACT 分数被大幅压低，避免一个通用词精确命中就排到第一
- **SUBSTRING/SOURCE 不乘 coverage**：子串和源文件命中本身就是弱信号（量级 1 和 0.5），再乘 coverage 会压到接近零，失去意义。它们是"有就加分"的补偿信号

---

## 5. 量级层级设计

```
EXACT    ~1000   ┐
PREFIX   ~100    ┤  词法主力（主循环）
SUBSTRING ~1     ┤
SOURCE   ~0.5    ┤
FUZZY    ~0-1    ┘
                 ┼ ─ ─ ─ ─ 量级分界
VECTOR   0~5     ┐  救援（后循环）
FUZZY rescue ~0-1┘
```

**量级设计意图**：

1. **词法是主力**：EXACT(1000) >> PREFIX(100) >> SUBSTRING(1)，层次清晰。词法命中的节点天然排在前面
2. **向量是兜底**：VECTOR 最大 5.0，介于 SUBSTRING(1) 和 PREFIX(100) 之间。只在词法全零时起决定作用，否则只是微调（5.0 vs 100/1000）
3. **FUZZY 是容错**：处理拼写错误，量级 ~0-1，与 SUBSTRING 同级，作为"词法全未命中时的最后补救"

---

## 6. 实际量级对比

以真实查询为例，用 graphify 内部 `_score_query` 的真实数据：

### Q1: `"当前事件分域的方案是什么"`

| 排名 | 节点 | total | lex | vec | 主导通路 |
|---|---|---|---|---|---|
| #1 | Domain（分域） | 6.48 | 6.48 | 0.00 | LEX 主导 |
| #4 | EventDomainMapping | 3.32 | 0.00 | 3.32 | VEC 救援 |

**打分分解**：

- **词法**：通过 bigram 分词 `"分域"` 命中 SUBSTRING → 1.0 × IDF=6.48 = 6.48
- **向量**：通过 cosine_sim=0.6635 → 5.0 × 0.6635 = 3.32
- **结论**：向量在词法为零时是唯一通路，但 3.32 < 6.48，排名仍低于词法命中的节点

> 这个例子完美展示了设计意图：词法命中的节点（Domain）排名高于向量救援的节点（EventDomainMapping），即使后者语义相关。词法是主力，向量是兜底。

---

## 7. 关键设计意图

| # | 意图 | 实现方式 |
|---|---|---|
| 1 | **词法是主力** | EXACT(1000) >> PREFIX(100) >> SUBSTRING(1)，层次清晰，词法命中的节点天然排前 |
| 2 | **向量是兜底** | `_VECTOR_SIMILARITY_BONUS=5.0` 只在词法全零时起决定作用，否则只是微调（5.0 vs 100/1000） |
| 3 | **FUZZY 是容错** | 处理拼写错误（如 `"UserServise"` → `"UserService"`），量级 ~0-1，不干扰精确匹配 |
| 4 | **coverage 平方** | `coverage = matched_terms / total_terms`，防止单个高频词精确匹配压过多词部分命中 |
| 5 | **trigram 预筛选 + 救援** | 主循环只评分可能匹配的节点（性能优化），后循环用向量/模糊把被排除的语义相关节点捞回来 |

---

## 8. 与 hybrid-semantic-search spec 的关系

本 spec 描述**整体检索架构**（双循环 + 7 通路 + 加法公式），`docs/hybrid-semantic-search/spec.md` 描述**向量层 + fuzzy 层的具体实现**：

| 关注点 | 本 spec | hybrid-semantic-search/spec.md |
|---|---|---|
| 双循环架构（主循环 + 救援循环） | ✅ 核心内容 | ❌ 不涉及 |
| 7 通路量级设计 | ✅ 完整表格 | ✅ 部分提及（VECTOR=5.0, FUZZY=2.0） |
| 叠加公式 + coverage² | ✅ 核心内容 | ✅ 公式一致 |
| trigram 预筛选机制 | ✅ 架构层面 | ❌ 不涉及（已是既有机制） |
| embedding 生成与存储 | ❌ 不涉及 | ✅ 核心内容（build-time sidecar） |
| 节点 desc 字段提取 | ❌ 不涉及 | ✅ 核心内容（docstring/首段） |
| 接口变更（CLI/MCP） | ❌ 不涉及 | ✅ 核心内容（semantic/top_k/top_n 参数） |

**两者关系**：本 spec 是架构层，hybrid-semantic-search spec 是实现层。实施时以 hybrid-semantic-search 的 plan.md 为准（逐步文件级改动清单），本 spec 提供整体设计意图和量级依据。

---

## 9. 非目标

- 不替换既有词法 3 层（保留 EXACT/PREFIX/SUBSTRING）
- 不修改 trigram 预筛选的算法（它已是既有机制，救援循环负责弥补其召回损失）
- 不引入 LanceDB/faiss（10k-100k 节点用 numpy brute-force 足够，详见 hybrid-semantic-search spec）
- 不对 `explain`/`path` 命令加语义检索（这两个命令需要精确匹配语义，不适合 fuzzy/vector）
- 不实现 query rewriting / synonym expansion（vector tier 已覆盖同义场景）

---

## 10. 验收标准

| ID | 标准 | 验证方式 |
|---|---|---|
| AC1 | 主循环只对 trigram 预筛选放行的节点跑 5 通路词法打分 | 代码审查：`_score_query` 主循环作用于 trigram 候选集 |
| AC2 | 救援循环对 trigram 排除的节点跑 VECTOR + FUZZY rescue 打分 | 代码审查：后循环作用于 trigram 排除集 |
| AC3 | 所有通路是加法叠加，最终得分 = Σ(每路贡献) | 代码审查：公式为加法，无替换/取max逻辑 |
| AC4 | EXACT/PREFIX 乘 coverage²，SUBSTRING/SOURCE 不乘 coverage | 代码审查：coverage² 只作用于 EXACT/PREFIX |
| AC5 | 量级层级 EXACT(1000) > PREFIX(100) > VECTOR(5) > SUBSTRING(1) > SOURCE(0.5) | 代码审查：常量值符合层级 |
| AC6 | VECTOR 救援只在 `semantic != false` 且 embedding sidecar 存在时触发 | `graphify query "login" --no-semantic` 不走向量层 |
| AC7 | 词法命中的节点排名高于向量救援的节点（即使后者语义相关） | 用 Q1 示例验证：Domain(6.48) > EventDomainMapping(3.32) |
| AC8 | FUZZY 仅当词法 3 层全未命中时触发 | `graphify query "UserService"` 的 FUZZY 分为 0（EXACT 已命中） |
| AC9 | trigram 预筛选 + 救援循环配合：语义相关但字符零重叠的节点能被召回 | `graphify query "how does login work?"` 能召回 `AuthService`（若 embedding 判断语义相关） |
| AC10 | coverage² 防止单个高频词精确匹配压过多词部分命中 | 构造 query：1 个高频词精确命中 + 2 个词无命中，验证 coverage² 压低分数 |

---

## 11. 防护约束（来自 issue 评论区）

在 skill 文件中添加防护约束，避免 agent 误用 graphify 内部 API：

1. **`skill-agents.md`**：加入明确规则 `"禁止 from graphify.* import — 仅使用 CLI 或内联 NetworkX 遍历"`。agent 不应直接 import graphify 内部模块（如 `graphify.query`、`graphify.serve`），因为内部 API 不稳定且跨版本可能不兼容；应通过 `graphify query` CLI 或直接加载 `graph.json` 用 NetworkX 遍历
2. **`query.md` 参考文件**：加入关于 embedding `index.json` 是 dict 而非 list 的提示。`{model_slug}.index.json` 的结构是 `{"node_ids": [...], "model": "...", "dim": N}`，其中 `node_ids` 是列表但消费时应转为 `{node_id: row_index}` 的 dict 映射，不能直接按索引取值

---

## 12. 风险

| 风险 | 缓解 |
|---|---|
| trigram 预筛选误杀语义相关节点 | 救援循环用 VECTOR + FUZZY rescue 把排除的节点捞回来 |
| 救援循环增加全量节点遍历开销 | VECTOR 层用 numpy 矩阵运算（sub-ms for 10k 节点）；FUZZY rescue 仅对 trigram 排除集做，且 rapidfuzz 是 C 加速 |
| 量级调参困难（VECTOR bonus vs 词法 bonus） | `_VECTOR_SIMILARITY_BONUS=5.0` 介于 SUBSTRING(1) 和 PREFIX(100) 之间，保证精确查询词法主导；用 benchmark fixture 调参 |
| 混合模式延迟（query embedding 需 API 调用） | LRU 缓存 query embedding（同 query 不重复 embed）；可配置本地 embedding 后端（sentence-transformers / ollama）避免远程调用 |
| Anthropic 无 embedding API（默认 backend 不支持） | `GRAPHIFY_EMBED_BACKEND` 显式指定 OpenAI/Ollama；无配置时降级为纯词法（救援循环跳过 VECTOR，仅保留 FUZZY rescue） |

---

## 13. 参考文献

- [Issue #2 评论](https://github.com/xuanxuancmd/graphify/issues/2#issuecomment-5488722635) — 双循环架构与 7 通路打分设计的原始描述
- `docs/hybrid-semantic-search/spec.md` — 向量层 + fuzzy 层的详细设计与 embedding 存储
- `docs/hybrid-semantic-search/plan.md` — 逐步文件级实施清单（desc 提取、embeddings.py、fuzzy.py、hybrid_scorer.py、serve.py 改动）
- `serve.py:462-629` — `_score_query` 实现（既有 3 层词法 + 新增加法 tier）
- `serve.py:124` — `_trigram_index` 预筛选机制
