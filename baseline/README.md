# 第一轮基线

第一轮从核对过的目标 SMILES 出发，检查模型能否提出有文献依据的断键，再看 Retro* 能否在固定预算内把每一条分支都追溯到库存原料。模型每次只收到待展开分子的结构。参考资料留到搜索结束后评阅。

[11 月 19 日实测记录](RESULTS.md)包含两题的搜索图、原始候选、首解时间和布洛芬未闭合的具体分支。

| 输入顺序 | 目标 | 选题目的与参考 |
| --- | --- | --- |
| 0 | 阿司匹林 | 单步阳性对照。库存含水杨酸和乙酸酐，可检查模型是否提出对应酯键断开、搜索器是否识别叶节点。[密歇根州立大学实验讲义](https://openbooks.lib.msu.edu/orgchemlabmanual/chapter/aspirin-synthesis-planning-scenario-and-background/) |
| 1 | 外消旋布洛芬 | 多步开发题。按题面还需从基础芳烃出发，并说明新增碳的来源。可对照三步专利路线，也接受有依据的其他拆法。[题面](../practice/01/prompt.md) · [专利路线与选择性数据](../practice/01/reference.md) |

[16 项库存](stock.smi)用于开发调试，包含参考反应的原料以及其他常见小分子。两种终产物、布洛芬参考路线中的酮和醇均排除。这里的“在库”表示这次计算允许作为叶节点，市场供货与题面许可还需分别核查。这两道题及其库存已用于开发，十题模拟应另行留题。

## 运行与复核

从项目根目录运行。固定 RetroChimera 1.3.0、Pistachio 权重（Figshare 文件 59468882）、Syntheseus 0.9.0 和 Retro* 默认的零值启发。官方 GPU 环境见 [environment.yml](https://github.com/microsoft/retrochimera/blob/main/environment.yml)。本机使用 WSL Ubuntu 22.04、Python 3.10、CPU PyTorch，主要依赖见 [requirements-cpu.txt](requirements-cpu.txt)。

```bash
uv venv --python python3.10 .runtime-linux/venv
uv pip install --python .runtime-linux/venv/bin/python torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .runtime-linux/venv/bin/python -r baseline/requirements-cpu.txt --find-links https://data.pyg.org/whl/torch-2.2.0+cpu.html
```

本机权重已解压到 `.runtime-linux/pistachio`，ZIP 的 SHA-256 为 `b0d30506d780693b293991cf2e5c5ac0be773748ccddbcd46684de5696d8a60f`。在新机器上下载并解压[相同文件](https://api.figshare.com/v2/file/download/59468882)，将 `model_dir` 指向含 `models.json` 的目录。完整包版本记录见[本次环境清单](runs/20261119-cpu/packages.txt)。

```bash
run_dir="baseline/runs/$(date -u +%Y%m%dT%H%M%SZ)"
PYTHONHASHSEED=0 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 .runtime-linux/venv/bin/python -m syntheseus.cli.main search --config baseline/search.yml use_gpu=false model_dir=.runtime-linux/pistachio results_dir="$run_dir"
```

[配置](search.yml)对两题使用相同库存，单节点最多取 5 个候选，每题最多 12 次单步调用、180 秒，模板应用使用两个工作进程。Syntheseus 0.9.0 的 CLI 固定 Python、NumPy 和 PyTorch 的随机种子为 0。上面的启动命令还设置了解释器的哈希种子，以控制前体集合的遍历顺序。时间限制按搜索迭代检查，单次模型调用可能跨过截止时间。换预算、库存或设备时单列结果。

每题目录中的 `stats.json` 记录模型调用数、树大小和首解时间，`graph.pkl` 保留被纳入搜索的反应及展开状态。用以下命令导出根节点候选与最早闭合的最多五条路线。同次展开可能有多条路线同时闭合，此时提取顺序不能区分优劣。

```bash
.runtime-linux/venv/bin/python baseline/inspect_search.py "$run_dir/RetroChimera/0/graph.pkl"
```

复跑时，对同一目标的两个结果目录运行 `python baseline/compare_runs.py 目录一 目录二`。它比较根节点反应排序与分数，并逐节点核对树结构、分数、展开和闭合状态、创建时的模型调用数。运行耗时单独查看各次的统计文件。

## 失败归因

| 需要区分的问题 | 如何检验 |
| --- | --- |
| 单步覆盖 | 对参考路线的每个产物单独请求相同 top-5，记录关键前体是否出现。分别核查完整前体集合与关键骨架断键。替代路线另行评阅。 |
| 搜索预算或顺序 | 在搜索图中定位模型已提出的关键分支，记录它是否被展开，以及截止时还缺哪一步。固定模型和库存，只放宽搜索预算做配对复跑。 |
| 库存限制 | 列出未闭合叶子，核查原题是否允许购买。只有合理扩充库存后同一路线能闭合，才支持该归因。 |
| 化学可行性 | 对闭合路线核查关键步的同底物或类似物先例、区域与立体选择性、设备要求和实测结果。单列证据不足或违反题面限制的路线。 |

## 替代模型的部署成本

以下是 11 月 19 日从官方文件清单核得的下载体积，使用十进制 GB。各模型的运行峰值显存、端到端延迟和每题费用需在具体硬件上测量。

| 方案 | 可核实的资源成本 | 对本项目的含义 |
| --- | --- | --- |
| RetroChimera Pistachio | 官方集成模型 ZIP 为 4,213,968,927 字节。还需解压空间和图网络依赖。 | 优先用于单步 + 搜索基线。[模型发布仓库](https://github.com/microsoft/retrochimera) |
| Solvent 8B | 权重分片合计 16.38 GB。官方推理环境采用 NVIDIA CUDA、打过补丁的 SGLang，并需要准备库存及相应评测资源。 | 适合作为整条路线的对照。要单独记录生成 token、库存查询和总耗时。[模型文件](https://huggingface.co/Alden19910/Solvent/tree/main) · [部署说明](https://github.com/alden199/Solvent) |
| DianShi-RetroStepLM-Direct | 4B 单步权重 8.04 GB。 | 可与 RetroChimera 共用规划器，分别测固定 top-k 下的延迟和前体覆盖。[模型文件](https://huggingface.co/DianShiGroup/DianShi-RetroStepLM-Direct/tree/main) |
| DianShi 完整系统（官方默认配置） | 另需 Qwen3.5-397B-A17B-FP8，94 个权重分片合计 406.15 GB。默认规划器 TP=8，单步服务 TP=1。发布的库存为 1.15 GB，模板为 92.4 MB。 | 全系统比较要把两个推理服务与工具开销都计入。默认并行配置仅描述作者的部署选择。[系统配置](https://github.com/DianShiGroup/DianShi-RetroStepLM) · [规划器文件](https://huggingface.co/Qwen/Qwen3.5-397B-A17B-FP8/tree/main) · [库存与模板](https://huggingface.co/datasets/DianShiGroup/DianShi-RetroPlanSystem-Assets/tree/main) |
