# RetroChimera 图 4a 单题复现

本实验在本机 CPU 上运行论文图 4a 使用的 SimpRetro 基准。运行前按作者清单的顺序选取第 1 题（索引 0），完整搜索 30 分钟。原图在 172 个目标上统计求解率。[RetroChimera 论文图 4 与 Methods](https://www.nature.com/articles/s41586-026-11160-9) · [作者发布的目标清单](https://github.com/catalystforyou/SimpRetro/blob/5abbdd12d23bec3b0c524a3f5e59d160beac00f3/SMILES.txt)

## 第 1 题实测结果

**30 分钟内未找到所有叶节点均在库的路线。** 目标分子式为 C53H51Cl2FN6O9S，含 72 个重原子，本身不在库存。单步模型完成了 33 个未命中缓存的分子预测。搜索器展开 544 个节点，最终图包含 43,086 个节点，对应 11,507 种不同的分子集合。独立读取保存的图，逐边检查反应与状态变化，并对图中 1,217 个不同分子重查原料库，所得五档判定与运行器一致。[输入](runs/target-000/input.json) · [原始结果](runs/target-000/result.json) · [搜索图](runs/target-000/graph.pkl) · [独立复核结果](runs/target-000/audit.json)

| 搜索时间 | 图中节点 | 最深逆推步数 | 已出现后续反应的首步分支 | 完整路线 |
| ---: | ---: | ---: | ---: | --- |
| 1 分钟 | 51 | 1 | 0 | 未找到 |
| 2 分钟 | 101 | 2 | 1 | 未找到 |
| 5 分钟 | 1,001 | 7 | 1 | 未找到 |
| 10 分钟 | 2,751 | 11 | 1 | 未找到 |
| 30 分钟 | 43,086 | 19 | 2 | 未找到 |

根节点产生了 50 个首步候选，只有两个得到继续展开。排名第一的候选把目标的羧酸逆推为叔丁酯，保留整个大环骨架。它的搜索策略分数为 0.941，其下有 41,135 个后续节点，占整棵树的 95.5%。这给出一个具体的失败现象：在这次 CPU 预算下，搜索集中在一个末步脱保护假设上。该步是否合理、另外 48 条首步候选中是否存在可闭合路线，以及调整探索强度能否改善结果，都需要独立检验。[根节点反应与分支计数](runs/target-000/audit.json)

模型与规划器初始化 95.66 秒，搜索 1,800.69 秒。含启动、导入依赖及写出结果，整个进程耗时 33 分 00 秒。GNU time 记录的最大常驻内存为 6.60 GiB，该值按进程统计。[运行日志](runs/target-000/search.log) · [资源记录](runs/target-000/resources.txt)

## 实验设置

| 环节 | 本次设置与依据 |
| --- | --- |
| 目标与库存 | 输入作者清单中第 1 个 SMILES。eMolecules 原文件共 23,081,629 行，去掉每行两端空白后仍有 23,081,629 个不同字符串。使用 SQLite 做精确成员查询，以便 CPU 机器同时容纳模型与库存。与作者配置一致，导入库存时不再做分子规范化。[原始库存下载说明](https://github.com/catalystforyou/SimpRetro/tree/5abbdd12d23bec3b0c524a3f5e59d160beac00f3) |
| 单步预测 | RetroChimera 1.3.0，公开 Pistachio 权重，包含模板定位与 R-SMILES2。每次最多请求 50 组前体，模板应用参数 `r_app=1`。图 4a 的单步候选直接进入搜索。[模型与权重](https://github.com/microsoft/retrochimera) · [论文 Methods](https://www.nature.com/articles/s41586-026-11160-9) |
| 多步规划 | 按 SimpRetro 公开入口采用 MolSetMCTS。每个节点代表一组当前待合成或已在库的分子，每条边代表一次逆合成断开。最大展开深度 20，使用模型概率引导选枝，PUCB 探索系数 1，初始价值 0.5。作者仓库按单步模型列出过部分调参值，公开配置未列出 RetroChimera。本次使用明确记录的默认参数与种子 0。[原始启动脚本](https://github.com/catalystforyou/SimpRetro/blob/5abbdd12d23bec3b0c524a3f5e59d160beac00f3/run_search.sh) · [上游调参表](https://github.com/catalystforyou/SimpRetro/blob/5abbdd12d23bec3b0c524a3f5e59d160beac00f3/syntheseus/cli/search_config.yml) · [本地配置](search.yml) |
| 时间与判分 | 模型加载另行计时。每个时间点检查是否已到达一个所有分子均在库存的状态。首解后继续搜索。搜索器在迭代之间检查时限，故进程实际用时可超过 1,800 秒。判定 30 分钟是否求解时，只计入 1,800 秒内出现的解。 |
| 硬件与软件 | 本机使用 Intel Core Ultra 5 125H、WSL Ubuntu 22.04、CPU PyTorch 和 Syntheseus 0.9.0。图 4a 的 GPU 为 V100，SimpRetro 原仓库带有自己的 Syntheseus 代码。本机的时间档结果只用于描述这一台机器上的这一题。 |

作者还公开了 **SimpRetro 模型**在这道题上的计算路线。压缩包内 `saved_routes/0_route.pdf` 的根节点记录首解用时 235.06 秒，配套 `0_templates.txt` 包含 17 步。这个独立对照说明同题在该基准上有过闭合路线。RetroChimera 这次运行只读取目标和库存，未使用该参考路线。[SimpRetro 路线原件](https://github.com/catalystforyou/SimpRetro/blob/5abbdd12d23bec3b0c524a3f5e59d160beac00f3/results/simpretro_routes.zip) · [原作者计时与路线导出代码](https://github.com/catalystforyou/SimpRetro/blob/5abbdd12d23bec3b0c524a3f5e59d160beac00f3/syntheseus/cli/search.py)

## 复跑

从项目根目录执行。先按[环境与权重说明](../../baseline/README.md)准备 Python 和 Pistachio 权重。以下命令在 Bash 中运行，库存索引只需建立一次。目标清单已随仓库保存，运行器会核对原始文件 SHA-256。

```bash
curl -fL 'https://drive.usercontent.google.com/download?id=1x33LmAizIdA5Dgw7IJp7_k7gRdNVv5cT&export=download&confirm=t' -o .runtime-linux/emolecules.txt
.runtime-linux/venv/bin/python reproduction/fig4a/prepare_stock.py .runtime-linux/emolecules.txt .runtime-linux/fig4a-stock.sqlite
PYTHONHASHSEED=0 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONUNBUFFERED=1 \
  .runtime-linux/venv/bin/python reproduction/fig4a/run_target.py \
  --stock .runtime-linux/fig4a-stock.sqlite --index 0 --out reproduction/fig4a/runs/target-000-repeat
```

每次复跑指定一个新的输出目录。目录内的 `input.json` 保存实际目标、库存校验值、依赖版本和搜索配置。`graph.pkl` 保存原始搜索图。`result.json` 保存五个时间点的求解状态、模型调用数、搜索图节点数和根节点断键。若有解，文件还给出最早闭合路线的反应序列和库存叶节点。路线闭合仅核实库存条件，反应可行性还需另行查证。

可用保存的图独立复核。下列命令逐个分子重查库存，逐边核对反应前后的状态，按节点创建时间重建五档结果。若有解，还会从库存原料正向重放首条路线。该步骤无需加载权重。

```bash
.runtime-linux/venv/bin/python reproduction/fig4a/audit_run.py reproduction/fig4a/runs/target-000 --stock .runtime-linux/fig4a-stock.sqlite
```
