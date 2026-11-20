# Seed STEM · 多步逆合成规划

给定一个目标分子的 SMILES，RetroChimera 预测单步反应前体，Syntheseus 用蒙特卡洛树搜索（MCTS）寻找能追溯到库存原料的完整路线。本仓库使用作者公开的模型、权重和搜索器，提供本地 CPU 实验入口、库存查询实现和搜索图复核代码。[RetroChimera 论文](https://www.nature.com/articles/s41586-026-11160-9) · [模型代码](https://github.com/microsoft/retrochimera) · [搜索框架](https://github.com/microsoft/syntheseus)

## 当前实验

已在 SimpRetro 原始 172 道题中运行第 1 题。使用 23,081,629 项 eMolecules 库存，在本机 CPU 上搜索 30 分钟，共生成 43,086 个节点。50 个首步候选中有 2 个得到后续展开，限时内未找到完整路线。论文图 4a 使用 V100 评测整个题集。[实验设置与分时结果](docs/fig4a.md) · [机器可读结果](results/fig4a/target-000/result.json)

## 运行与复核

首次使用时，按[环境安装、权重下载和库存建库步骤](docs/fig4a.md#复跑)准备运行环境。以下命令从仓库根目录在 Linux 或 WSL 中执行。复核已有结果只需安装依赖、准备库存索引，然后运行第二条命令。

```bash
PYTHONHASHSEED=0 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONUNBUFFERED=1 \
  .runtime-linux/venv/bin/python scripts/run_target.py --index 0 \
  --stock .runtime-linux/fig4a-stock.sqlite --out results/fig4a/target-000-repeat

.runtime-linux/venv/bin/python scripts/audit_run.py results/fig4a/target-000 \
  --stock .runtime-linux/fig4a-stock.sqlite
```

## 仓库结构

| 目录 | 内容 |
| --- | --- |
| [scripts/](scripts/) | 建立库存索引、运行单题搜索、复核搜索图、从 SMILES 绘制结构图 |
| [configs/](configs/) | 图 4a 实验的模型、搜索策略和预算 |
| [data/](data/simpretro/) | SimpRetro 原始目标清单，保留作者的顺序与文件校验值 |
| [environment/](environment/) | CPU 环境依赖和本机安装的包版本 |
| [results/](results/fig4a/target-000/) | 已完成实验的原始输入、结果、搜索图、日志、资源统计和复核报告 |
| [docs/](docs/) | 单题复现说明、[部署成本调研](docs/model-deployment.md)、[比赛安排](docs/competition.md)和[通用单题工作稿](docs/route-template.md) |

本地权重、完整库存及其 SQLite 索引保存在 Git 忽略的 `.runtime-linux/` 目录中。
