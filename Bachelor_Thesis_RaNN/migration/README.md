# 迁移证据文件说明

- source_before.csv：修改前7067条文件/符号链接，包含500科研文件和6567运行文件。SHA均来自真实读取；kind=symlink时SHA针对链接目标路径的UTF-8文本，不读取项目外的目标解释器。
- research_files_before.csv：上述500科研文件专表。
- runtime_exclusions.csv：不进入Windows包的6567个Linux环境/缓存文件；不是缺失数据。
- original_metadata/：README/.gitignore原字节副本，供迁移前后追溯。
- experiment_catalog.json / experiment_index.csv：实际8个run目录、原日志命令证据与全部配置/结果路径。exp01固定目录另见docs/实验复现指南.md。
- command_evidence.json：历史科研日志相关行，不是完整shell history。
- csv_catalog.csv：63份原CSV的行数、列及状态字段；无status列时不虚构运行结论。
- npz_array_catalog.csv：7个NPZ中1365个数组的shape/dtype，只读取头部，无求解。
- cloud_environment.json：迁移时环境快照；原run的历史环境仍在各config，不改写。
- git_status.json：没有有效Git工作树的实际结果，不等同一组未跟踪状态。
- historical_archives_before.json：6份原ZIP的字节数和SHA，全备份保留它们。
- original_preservation.json：500科研原路径对比；498原样、2元数据补充且原字节副本一致。
- security_preflight.json / security_final_project.json：凭据模式检查的范围与结论。无匹配值入日志，不承诺机器能识别任意秘密格式。
- tool_validation.json：迁移工具语法和临时文本夹具完整性验证；不是科研测试或Windows测试。
- export_policy.json：导出/排除范围。
- manifest_sha256.csv：最终导出文件的完整逐文件路径、大小及SHA，清单自身除外。它本身的SHA写在外部发行JSON，避免循环自引用。

项目中文路径按UTF-8写清单，ZIP保存相对路径。标准库校验器不导入科研依赖，也不修改原始数据；新增本地run不在封存清单内。
