# 模型部署成本调研

以下是 11 月 19 日从官方文件清单核得的下载体积，使用十进制 GB。各模型的运行峰值显存、端到端延迟和每题费用需在具体硬件上测量。

| 方案 | 可核实的资源成本 | 对本项目的含义 |
| --- | --- | --- |
| RetroChimera Pistachio | 官方集成模型 ZIP 为 4,213,968,927 字节。还需解压空间和图网络依赖。 | 优先用于单步 + 搜索基线。[模型发布仓库](https://github.com/microsoft/retrochimera) |
| Solvent 8B | 权重分片合计 16.38 GB。官方推理环境采用 NVIDIA CUDA、打过补丁的 SGLang，并需要准备库存及相应评测资源。 | 适合作为整条路线的对照。要单独记录生成 token、库存查询和总耗时。[模型文件](https://huggingface.co/Alden19910/Solvent/tree/main) · [部署说明](https://github.com/alden199/Solvent) |
| DianShi-RetroStepLM-Direct | 4B 单步权重 8.04 GB。 | 可与 RetroChimera 共用规划器，分别测固定 top-k 下的延迟和前体覆盖。[模型文件](https://huggingface.co/DianShiGroup/DianShi-RetroStepLM-Direct/tree/main) |
| DianShi 完整系统（官方默认配置） | 另需 Qwen3.5-397B-A17B-FP8，94 个权重分片合计 406.15 GB。默认规划器 TP=8，单步服务 TP=1。发布的库存为 1.15 GB，模板为 92.4 MB。 | 全系统比较要把两个推理服务与工具开销都计入。默认并行配置仅描述作者的部署选择。[系统配置](https://github.com/DianShiGroup/DianShi-RetroStepLM) · [规划器文件](https://huggingface.co/Qwen/Qwen3.5-397B-A17B-FP8/tree/main) · [库存与模板](https://huggingface.co/datasets/DianShiGroup/DianShi-RetroPlanSystem-Assets/tree/main) |
