# Seed STEM 分子逆合成挑战赛

本项目开发**面向真实合成任务的可靠多步逆合成规划系统**。RetroChimera 根据目标结构预测单步前体，Syntheseus 搜索能够追溯到指定库存原料的路线。比赛练习还需核查关键反应的化学证据。

## 仓库导航

| 想做什么 | 从哪里开始 |
| --- | --- |
| 查看或复跑论文图 4a 的第 1 题 | [单题复现](reproduction/fig4a/README.md)包含 CPU 环境入口、原始目标与库存来源、30 分钟 MCTS 配置和复跑命令。[运行结果](reproduction/fig4a/runs/target-000/result.json)与[搜索图复核](reproduction/fig4a/runs/target-000/audit.json)可直接查看。 |
| 查模型部署成本 | [部署调研](docs/model-deployment.md)汇总 RetroChimera、Solvent 和 DianShi 的公开权重体积及环境要求。 |
| 整理比赛方案 | 用[通用单题工作稿](practice/route-template.md)记录目标、候选路线、反应先例、选择性与风险。[结构绘制工具](tools/draw_structure.py)可把 SMILES 画回结构图，供人工核对。 |

当前正式基准跑了原始 172 道题中的第 1 题。使用 23,081,629 项库存，在本机 CPU 上搜索 30 分钟，生成 43,086 个节点，未找到完整路线。50 个首步候选中只有 2 个得到后续展开。[实验设置、分时结果与局限](reproduction/fig4a/README.md)

## 比赛准备

赛题从目标分子结构图开始，要求在火山方舟设计完整逆合成路线。2026 年 12 月 4 日中午 12:00 截止报名，12 月 7 日公布题目及提交要求，12 月 10 日提交方案。专家初筛之后，独立 CRO 会对入选方案做湿实验。[赛事通知](https://seed.bytedance.com/zh/blog/seed-stem-计划-分子逆合成挑战赛启动?view_from=homepage_tab) · [报名入口](https://bytedance.larkoffice.com/share/base/form/shrcnPuqeyluTnYwI7SnjBqL4Be)

## 出题前安排

| 时段 | 要解决的问题 | 可检查的产物 |
| --- | --- | --- |
| 11 月 19–23 日 | 强基线能否找到完整路线，运行一次要多少资源？ | 在 [SimpRetro 原始目标](reproduction/fig4a/README.md)上运行 RetroChimera + Syntheseus，记录库存、预算、搜索图和用时 |
| 11 月 24–27 日 | 关键前体是否出现、是否展开、叶节点为何未闭合、闭合路线的关键步有何依据？ | 针对具体节点回查单步候选、搜索图、库存和文献，保留替代路线及无法判定的案例 |
| 11 月 28 日–12 月 3 日 | 哪个干预能解决已观察到的问题？ | 按归因选择先例检索、路线评分或失败节点重搜。冻结目标、库存和预算，逐项消融，只保留有可重复收益的模块 |
| 12 月 4–6 日 | 三天能否完成十道高难题的搜索、证据核查和方案整理？ | 用未参与调参的十道题限时演练，逐题记录首条候选时间、人工核查用时、可交付方案及未解决风险 |

以上是内部训练安排。12 月 7 日按正式要求调整工作稿和交付格式。
