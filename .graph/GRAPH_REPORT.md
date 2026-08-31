# 图谱报告 - graphify  (2026-08-31)

## 语料检查
- 824 个文件 · 约 1,404,229 词
- 判定：语料规模足够大，图结构能带来价值。

## 概要
- 15781 个节点 · 29065 条边 · 1045 个社区（展示 855 个，省略 190 个稀疏社区）
- 提取：97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED：783 条边（平均置信度：0.85）
- Token 开销：0 输入 · 0 输出

## 图谱新鲜度
- 构建自提交：`6c8e80d1`
- 运行 `git rev-parse HEAD` 并与之对比，以检查图谱是否陈旧。
- 代码变更后运行 `graphify update .`（无 API 开销）。

## 社区枢纽（导航）
- _make_id
- load_prompts_from_dir
- test_extract.py
- _labels
- test_build.py
- _file_stem
- _read_text
- test_languages.py
- test_import_extension_resolution.py
- bash.py
- graphify/__main__.py
- export.py
- detect
- test_llm_backends.py
- serve.py
- test_detect.py
- test_export.py
- test_install.py
- test_dedup.py
- test_serve.py
- expand_oversized_files
- test_analyze.py
- test_dedup_remaps_hyperedges.py
- classify_file
- test_chunking.py
- test_dotnet.py
- test_pascal.py
- test_ignore_file_encoding.py
- extract.py
- _call_claude_cli
- test_cli_export.py
- test_extract_cli.py
- test_image_vision.py
- install
- test_ruby_resolution.py
- Communities (141 total, 52 thin omitted)
- test_incomplete_build_guard.py
- _edge_labels
- extract_python
- test_csharp_member_calls.py
- _detect_main_language
- Embedding 手动验证流程
- test_js_import_resolution.py
- extract_js
- embeddings.py
- build_from_json
- test_multigraph_diagnostics.py
- cache.py
- extract
- test_codebuddy.py
- generate_embeddings_incremental
- normalize_id
- _extract_node_desc
- _parse_llm_json
- save_semantic_cache
- introspect_postgres
- Communities
- cache_dir
- test_ddd_extractor.py
- test_skillgen.py
- test_scip_ingest.py
- test_reflect.py
- test_serve_http.py
- test_devin.py
- test_manifest_ingest.py
- test_global_graph.py
- gen.py
- extract_cpp
- extract_files_direct
- test_benchmark.py
- audit_coverage
- test_indirect_dispatch.py
- build
- test_evidence_binding.py
- reflect.py
- build_tree
- edge_data
- extract_objc
- _get_extractor
- test_mcp_ingest.py
- _score_nodes
- _query_graph_text
- test_affected_cli.py
- test_query_induced_edges.py
- Path
- test_query_names_its_graph.py
- test_install_references.py
- _pick_seeds
- claude_install
- ingest_scip_json
- test_transcribe.py
- User
- 聚合协作视图 — 用户管理
- _make_graph
- exceptions.py
- raw/analyze.py
- _estimate_file_tokens
- Response
- 3. Tier 2 扩展:提示词型解析器
- test_cache.py
- test_obsidian_vault_migration.py
- _hooks_dir
- test_user_management_e2e.py
- hooks.py
- test_querylog.py
- /graphify
- /graphify
- /graphify
- Spec: DDD 文档自定义解析器 + 解析器优先级机制
- Docker MCP Toolkit + SQLite MCP server
- HttpClient
- extract_commonlisp
- callflow_html.py
- validate_extraction
- test_labeling.py
- test_explain_cli.py
- 业务约束提取参考（DDD）
- parametrize
- test_minhash.py
- /graphify
- build_merge
- skipif
- render_all
- /graphify
- /graphify
- markdown.py
- _is_ignored
- run_language_resolvers
- Cookies
- TestSubprocessEncoding
- test_indirect_call_function_expression_shadow.py
- Plan: DDD 文档自定义解析器 + 解析器优先级机制
- write_callflow_html
- test_callflow_html.py
- extract_dart
- mcp_ingest.py
- test_go_qualified_resolution.py
- test_install_roundtrip.py
- test_path_cli.py
- Request
- build_label_index
- Spec: 混合语义检索（语义 + fuzzy 重排）
- test_csharp_interface_dispatch.py
- test_agents_platform.py
- _fixture
- test_hook_guard.py
- test_read_hook.py
- _make_symbol_doc
- test_swift_cross_file_calls.py
- to_wiki
- sample.swift
- graphify 数据建模
- test_indirect_dispatch_getattr.py
- dedup.py
- test_vue_extraction.py
- ddd.py
- ExtractionResult
- scip_ingest.py
- What You Must Do When Invoked
- DataProcessor
- What You Must Do When Invoked
- introspect_cargo
- test_prs.py
- detect.py
- file_hash
- swagger.py
- multigraph_compat.py
- What You Must Do When Invoked
- _corpus
- What You Must Do When Invoked
- test_stat_index_portability.py
- reverse-engineering-ddd
- extract_dm
- google_workspace.py
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- test_extract_code_only_cli.py
- test_incremental.py
- test_jsconfig_baseurl.py
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- test_multilang.py
- _relations
- test_python_import_resolution.py
- graphify/build.py
- test_community_labels_skill.py
- test_swagger_e2e.py
- test_js_dynamic_imports.py
- test_kotlin_grammar.py
- test_prune_sweeps_orphans.py
- What You Must Do When Invoked
- Specific Issues Found
- 方法论参考
- _parse_ci
- test_hook_out_of_project_paths.py
- _class_node
- extract_terraform
- ingest.py
- test_semantic_cleanup.py
- test_export_control_characters.py
- test_js_dynamic_import_affected.py
- test_search_hook.py
- client.py
- extract_powershell
- AuthService
- build_community_labels
- generate_section_flowchart
- CsharpNameResolver
- _extract_sql_or_skip
- test_python_decorators.py
- generate_section_cards
- resolve_cross_file_raw_calls
- extract_ocaml
- save_query_result
- _score_query
- test_csharp_partial_classes.py
- _two_community_graph
- _write_raw_doc
- rsl-siege-manager/manifest.json
- test_settings_merge.py
- index.ts
- convert_office_file
- sanitize_semantic_fragment
- test_symbol_resolution.py
- UserService
- 1. 业务实现技术
- test_cpp_objc_cross_file_calls.py
- test_go_builtin_call_targets.py
- test_install_upgrade.py
- test_java_type_resolution.py
- _run
- _load_custom_providers
- test_watch_manifest_location.py
- test_obsidian_unicode_tags.py
- 技术约束提取参考
- security.py
- SKILL.md
- test_cross_extension_reexport_self_cycle.py
- test_csharp_object_creation.py
- _claude_artifacts
- test_export_path_length.py
- sample.php
- UserControl
- Plan: 提交阶段图谱更新能力补齐
- Design: Incremental Updates + Entity Deduplication
- test_watch.py
- compute_pr_impact
- processor.py
- Graph
- sample.kt
- test_indirect_call_external_import_shadow.py
- test_semantic_cache_out_root.py
- test_ts_decorators.py
- Window
- objc.py
- test_cluster.py
- test_wiki_link_filename_parity.py
- main
- validator.py
- test_merge_graphs_cli.py
- TestRebuildCodeProcessesSwaggerYaml
- test_typescript_enum_members.py
- Graphify Evaluation - Mixed Corpus (2026-04-04)
- Window
- _stale_graph_sources
- _is_regular_file
- affected_nodes
- wiki.py
- extract_markdown
- test_indirect_call_nested_closure_shadow.py
- test_inferred_confidence_rubric.py
- test_java_member_calls.py
- extract_astro
- test_objc_category_interfaces.py
- test_objc_property_ivar_receivers.py
- Platform
- test_atomic_writes.py
- sample.json
- graphify Benchmarks
- AccountService
- _inline_links
- _check_skill_version
- TDataProcessor
- Path
- test_cross_repo_shared_types.py
- test_csharp_call_site_generic_args.py
- test_csharp_enum_members.py
- test_csharp_field_generic_args.py
- _env_command_args
- test_src_layout_import_resolution.py
- test_merge_chunks_validation.py
- test_no_dedup_flag.py
- storage.py
- string
- clear_cache
- 2. 编码规范
- sample.sv
- test_csharp_member_nodes.py
- test_extract_cache_location.py
- test_indirect_call_arrow_single_param_shadow.py
- test_indirect_call_catch_binding_shadow.py
- _vault_extract
- test_node_id_canonical.py
- test_ts_namespace.py
- test_ts_receiver_member_calls.py
- test_falkordb_integration.py
- Communities
- raw/models.py
- Benchmark: Karpathy Repos + Research Papers
- Geometry
- sample.razor
- geometry
- check_ddd_anchors.py
- sample.go
- Embedding 配置指南
- DataProcessor
- Animal
- sample.dmf
- ScopedCallsUnit
- test_extraction_spec_ids.py
- test_objc_member_calls.py
- test_ts_inheritance.py
- Graph Report - worked/mixed-corpus/raw  (2026-04-05)
- test_query_cli.py
- attach_graph_impact
- _detect_default_branch
- test_swift_computed_properties.py
- 1. 业务实现技术
- compilerOptions
- barrel_reexport.ts
- test_architecture_doc.py
- Plan: 解析器扩展机制能力补齐
- test_install_strings.py
- test_js_callback_calls.py
- test_scala_self_type.py
- test_ts_generators.py
- test_typescript_module_extensions.py
- _plant_skill_tree
- _make_scip_node_id
- HTTPStatusError
- Case Study: rsl-siege-manager (Python + TypeScript monorepo)
- Demo.ViewModels
- RFC: file-level node summaries
- test_prompt_registry.py
- extract_swagger
- BC 级产物
- 使用说明（给主 Agent）
- {BC 名称} — 限界上下文索引
- test_zig_enum_and_union_methods_are_extracted
- graphify
- llm.py
- parse_memory_doc
- test_god_node_article_community_without_node_attr
- _git
- TestCodeAssociationEdges
- TMainForm
- test_cjs_module_extension.py
- test_indirect_dispatch_assign_return.py
- test_kotlin_object_literal.py
- test_partial_extraction_warning.py
- test_pascal_call_scoping.py
- test_php_type_resolution.py
- test_wheel_packaging.py
- prompt_registry.py
- 支付
- Gap-6: DDD 代码锚点匹配增强(全限定名 + 多匹配 + 置信度标注)
- Incremental Updates + Entity Deduplication Implementation Plan
- prs.py
- prompt_fingerprint
- §7 模式识别：聚合协作（Step 6）
- _is_swagger_spec
- 聚合协作视图 — {BC 名称}
- compilerOptions
- package.json
- api.py
- sample_plpgsql_quoted.sql
- test_indirect_call_for_of_binding_shadow.py
- test_phantom_cross_package_call.py
- parser.py
- render_always_on
- test_ts_parse_warning.py
- Architecture
- Gap-3: 项目级目录 + 优先级
- Gap-4: Tier 2 prompt registry
- _shortest_path_text
- sample.csproj
- _replace_or_append_section
- graphify reference: extra exports and benchmark
- _collision_rank
- graphify reference: extra exports and benchmark
- 3. 各文件类型的建模方式
- load_all_prompts
- iter_raw_calls
- graphify reference: extra exports and benchmark
- _path_match
- 实现步骤
- graphify reference: extra exports and benchmark
- 推断草稿 — {系统名称}
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- tests/conftest.py
- dynamic_import.ts
- Widget
- TBaseGadget
- Config
- sample_calls.py
- test_cross_language_call_resolution.py
- test_gemini_hook.py
- test_god_nodes_cli.py
- test_import_self_loops.py
- _many_communities
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- AsyncHTTPTransport
- Graph Report - .  (2026-05-13)
- Review: rsl-siege-manager
- saxpy
- Gap-7: URL 锚点匹配修复(endpoint 节点产出 + 路径规范化)
- How graphify works
- semantic_cleanup.py
- first_present
- format_node_refs
- safe_file_path
- {名称}
- _coerce_hyperedge_member_refs
- Migrating a language extractor out of extract.py
- lessons_fresh
- load_memory_docs
- load_validated_semantic_fragment
- §3 模式识别：限界上下文（Step 2）
- PasswordHasher
- make_pr
- §9 隐形架构决策提取
- gen_demo_path.py
- Security Model
- TestDDDDocAnchorNodes
- TestCrossFileEdgeResolution
- sample.zig
- sample.rb
- test_antigravity_install.py
- test_case_sensitive_resolution.py
- §4 临时文件 vs 产物：清晰边界
- test_phantom_external_import.py
- 用例: {用例名称}
- test_swift_import_resolution.py
- DigestAuth
- Graph Report - /home/safi/graphify-benchmark  (2026-04-04)
- Corpus (52 files)
- Gap-5: 三阶段提取顺序(代码 → 配置文件 → 文档)
- 7. 步骤 7：修改 `graphify/serve.py`
- 上下文图 — {系统名称}
- 假设草稿 — {系统名称}
- _make_noisy_graph
- test_maybe_reload_detects_graph_change
- TestTagsField
- _default_model_for_backend
- §8 模式识别：业务不变式（Step 7）
- 提问记录 — {系统名称}
- 4. 检索机制
- _community_label_lines
- 上下文图 — User Management System
- TestCodeAnchorMatching
- test_security.py
- TestNodeShape
- Foo
- sample_php_listen.php
- test_cpp_preprocess.py
- test_crossfile_identical_labels_stay_distinct_for_guarded_types
- test_home_sandbox.py
- Research Notes
- Gap-1: 解除 Tier 1 扫描范围硬编码,支持任意文件类型
- Gap-2: 内置自动扫描目录
- Plan: 混合语义检索（语义 + fuzzy 重排）
- safe_fetch
- graphify reference: query, path, explain
- _inferred_uses
- graphify reference: query, path, explain
- .opencode/opencode.json
- user-management/.opencode/opencode.json
- 日志不变式
- graphify reference: query, path, explain
- _resolve_max_retry_depth
- graphify reference: query, path, explain
- CLI 命令（终端里运行）
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- sample.c
- ensure_graph_json
- build
- Logger
- Deploy Guide
- sample.sh
- TSampleForm
- sample_php_container.php
- sample_plpgsql.sql
- SampleSpec
- test_cli_broken_pipe.py
- test_install_version_stamp.py
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- Document Pipeline Architecture
- Reproducible Example
- E2E 测试体系（双重保障）
- 3. 步骤 3：修改 `graphify/extractors/engine.py`（desc 字段提取）
- 9. 步骤 9：测试
- SamplePackage
- §11 质量检查
- validate_url
- validate_graph_path
- verilog.py
- cli.py
- test_hooks.py
- load_platforms
- HybridScorer
- 2. 边模型
- User Management Test Project
- 限界上下文映射（Context Map）
- 订单领域模型（Domain Model）
- 技术约束（Technical Constraints）
- TOtherGadget
- sample.sql
- sample_doctest.cpp
- MyApp.Accounts.User
- sample.luau
- RateLimiter
- ColorResolver
- sample.sln
- UserControl
- MainViewModel
- httpx Corpus Benchmark
- Mixed Corpus Benchmark
- Plan: 解析器扩展机制差异修复
- 10. 步骤 10：验证
- 1. 步骤 1：创建 `graphify/desc.py`（节点 desc 字段提取）
- 2. 步骤 2：创建 `graphify/embeddings.py`
- 4. 步骤 4：修改 `graphify/extractors/markdown.py`（文档节点 desc）
- 5. 步骤 5：创建 `graphify/fuzzy.py`
- 6. 步骤 6：创建 `graphify/hybrid_scorer.py`
- generate_header
- test_swift_builtin_noise.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- _match_anchored_ignore_pattern
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- test_ingest_symbol_trailing_hash_no_display_name_has_non_empty_label
- test_relationship_target_unknown_emits_stub_node
- test_non_string_relative_path_falls_back_to_default
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- test_non_string_language_falls_back
- test_documents_field_non_list_returns_empty
- test_occurrence_negative_line_falls_back_to_zero
- test_unique_cross_document_symbol_still_resolves
- test_relationship_truthy_string_flag_is_ignored
- test_relationship_int_flag_is_ignored
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- test_relationship_boolean_true_routes_correctly
- test_ingest_multiple_symbols_in_one_document
- test_ingest_multiple_documents
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- shapes
- 用户管理
- cjs_require.js
- test_ingest_documents_empty_list
- test_ingest_edge_source_location_from_first_occurrence
- Server
- test_ingest_single_symbol_no_relationships
- 订单业务流程（Business Flow）
- 订单业务契约（Contracts）
- 订单领域事件（Domain Events）
- App
- sample.ts
- Transformer
- sample_transaction.sql
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- 8. 步骤 8：修改 `graphify/cli.py`（build-time embed 命令）
- App.csproj
- graphify/__init__.py
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- test_ingest_duplicate_symbols_in_same_file_are_deduplicated
- test_ingest_document_item_not_a_dict_is_skipped
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- test_ingest_symbol_without_symbol_id_is_skipped
- test_ingest_document_without_symbols_key
- test_ingest_symbol_without_kind_defaults_to_unknown
- test_ingest_document_relative_path_overrides_source_file_param
- test_ingest_symbol_with_short_range_uses_first_element_as_line
- test_ingest_symbol_with_documentation_becomes_description
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- test_ingest_symbol_with_empty_documentation_skips_description
- test_ingest_edge_with_zero_sourceline_has_empty_location
- _doc_community
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- 订单业务不变式（Invariants）
- Dup
- Dup
- AccountTrigger
- sample_alter_fk.sql
- sample_cte.sql
- sample.dmi
- sample_schema_qualified.sql
- Foo
- Foo
- test_ingest_non_dict_input_returns_empty
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- Troubleshooting
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\env.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0002_add_preview_columns.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0003_make_siege_date_nullable.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0004_add_post_priority_config.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0005_add_description_to_post_priority_config.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0006_power_level_and_drop_sort_value.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0007_fix_group_number_max.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0008_add_matched_condition_id_to_position.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0009_add_discord_id_to_member.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0010_add_last_seen_changelog_at_to_member.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0011_add_post_suggest_preview.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\attack_day.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\auth.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\autofill.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\board.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\buildings.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\changelog.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\comparison.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\discord_sync.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\health.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\images.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\lifecycle.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\members.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\notifications.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\post_priority_config.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\post_suggestions.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\posts.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\reference.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\siege_members.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\sieges.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\validation.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\version.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\config.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\base.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\__init__.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\seeds.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\session.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\dependencies\\auth.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\dependencies\\__init__.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\__init__.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\main.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\middleware.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\building_group.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\building.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\building_type_config.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\enums.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\__init__.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\member_post_preference.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\member.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\notification_batch.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\notification_batch_result.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\position.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post_active_condition.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post_condition.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post_priority_config.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\siege_member.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\siege.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\rate_limit.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\attack_day.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\autofill.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\board.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\building.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\changelog.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\common.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\comparison.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\__init__.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\member.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\post_condition.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\post.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\post_suggestions.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\siege_member.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\siege.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\validation.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\version.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\attack_day.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\autofill.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\board.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\bot_client.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\building_capacity.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\buildings.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\comparison.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\discord_sync.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\image_gen.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\lifecycle.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\members.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\notification_message.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\post_suggestions.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\posts.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\reference.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\siege_members.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\sieges.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\validation.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\telemetry.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\scripts\\seed_demo.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\scripts\\seed.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\conftest.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\__init__.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_attack_day.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_auth.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_auth_rate_limit.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_autofill.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_board.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_bot_client.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_buildings.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_changelog.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_comparison.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_config_endpoint.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_config.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_cors.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_discord_sync.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_enums.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_health.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_image_gen.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_lifecycle_integration.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_lifecycle.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_member_changelog_column.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_members.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_notification_message.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_notifications.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_post_suggestions_integration.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_post_suggestions.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_posts.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_reference.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_schema.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_seed_canonical.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_seed_demo.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_sieges.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_telemetry.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_validation.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_version.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\config.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\discord_client.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\http_api.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\__init__.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\telemetry.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\conftest.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\__init__.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_discord_client.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_get_guild_member.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_http_api.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_telemetry.py
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\e2e\\board.spec.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\e2e\\siege-lifecycle.spec.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\e2e\\smoke.spec.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\eslint.config.js
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\playwright.config.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\postcss.config.js
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\board.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\changelog.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\client.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\config.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\members.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\notifications.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\App.tsx
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\main.tsx
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\vite-env.d.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\tailwind.config.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\vite.config.ts
- I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\vitest.config.ts
- AGENTS.md
- always_on/agents-md.md
- always_on/antigravity-rules.md
- always_on/claude-md.md
- always_on/vscode-instructions.md
- custom/__init__.py
- agents/references/extraction-spec.md
- {业务动作}
- claude/references/extraction-spec.md
- {唯一业务名称}
- {描述性失败名称}
- {术语}
- droid/references/extraction-spec.md
- {描述性契约名称}
- {EventName}
- opencode/references/extraction-spec.md
- {描述性协作名称}
- trae/references/extraction-spec.md
- vscode/references/extraction-spec.md
- windows/references/extraction-spec.md
- ddd/README.md
- sample.md
- {源状态→目标状态}
- test_label_cli_drops_sentinel_and_bare_key_echoes
- {规则陈述}
- {规则陈述}
- {技术选型名称}
- 令牌
- 挂起
- .opencode/plugins/graphify.js
- user-management/.opencode/plugins/graphify.js
- 档案
- 用户
- 软删除
- 文件命名用 kebab-case，类命名用 PascalCase
- BF-01 创建订单
- BF-02 支付回调
- BF-03 库存扣减
- BF-04 订单完成
- RF-01 发起退款
- RF-02 退款到账
- 聚合根
- 领域事件
- DE-01 订单已创建
- DE-02 订单已支付
- DE-03 订单已发货
- DE-04 订单已取消
- DE-05 订单已完成
- DE-06 支付已发起
- graphify__always_on__agents-md.md
- graphify__always_on__antigravity-rules.md
- graphify__always_on__claude-md.md
- graphify__always_on__gemini-md.md
- graphify__always_on__vscode-instructions.md
- graphify__skills__agents__references__extraction-spec.md
- graphify__skills__amp__references__extraction-spec.md
- graphify__skills__claude__references__extraction-spec.md
- graphify__skills__claw__references__extraction-spec.md
- graphify__skills__codex__references__extraction-spec.md
- graphify__skills__copilot__references__extraction-spec.md
- graphify__skills__droid__references__extraction-spec.md
- graphify__skills__kilo__references__extraction-spec.md
- graphify__skills__kiro__references__extraction-spec.md
- graphify__skills__opencode__references__extraction-spec.md
- graphify__skills__pi__references__extraction-spec.md
- graphify__skills__trae__references__extraction-spec.md
- graphify__skills__vscode__references__extraction-spec.md
- graphify__skills__windows__references__extraction-spec.md
- always-on/agents-md.md
- always-on/antigravity-rules.md
- always-on/claude-md.md
- always-on/gemini-md.md
- always-on/vscode-instructions.md
- kilo-rules.md
- shared/extraction-spec.md
- extraction-spec-compact.md
- DE-07 支付已成功
- DE-08 支付已失败
- AG-01 订单聚合
- AG-02 订单项
- AG-03 收货地址
- AG-04 支付单
- AG-05 支付明细
- AG-06 订单-支付协作
- AG-07 订单-库存协作
- 数据库分库策略
- crate_a
- crate_b
- graphifyy
- TButton
- x
- y
- z
- Int

## God Nodes（连接数最多——核心抽象）
1. `extract()` - 538 条边
2. `build_from_json()` - 205 条边
3. `_rebuild_code()` - 154 条边
4. `dispatch_command()` - 133 条边
5. `detect()` - 126 条边
6. `_make_id()` - 124 条边
7. `_read_text()` - 123 条边
8. `_file_stem()` - 113 条边
9. `_labels()` - 94 条边
10. `main()` - 92 条边

## 意外连接（你多半没注意到这些）
- `test_dmi_no_error()` --calls--> `extract_dmi()`  [INFERRED]
  tests/test_languages.py → graphify/extractors/dm.py
- `test_dmi_state_contained_by_file()` --calls--> `extract_dmi()`  [INFERRED]
  tests/test_languages.py → graphify/extractors/dm.py
- `test_dmf_elem_under_window()` --calls--> `extract_dmf()`  [INFERRED]
  tests/test_languages.py → graphify/extractors/dm.py
- `test_dmf_no_dangling_edges()` --calls--> `extract_dmf()`  [INFERRED]
  tests/test_languages.py → graphify/extractors/dm.py
- `test_dmf_no_error()` --calls--> `extract_dmf()`  [INFERRED]
  tests/test_languages.py → graphify/extractors/dm.py

## 导入循环
- 1 个文件的循环：`tests/fixtures/sample.sv -> tests/fixtures/sample.sv`

## 社区（共 1045 个，省略 190 个稀疏社区）

### 社区 0 —— "_make_id"
凝聚度：0.04
节点（共 73 个）：_import_csharp(), _import_java(), _import_kotlin(), _import_php(), _import_scala(), Apex extractor. Moved verbatim from graphify/extract.py., _make_id(), extract_blade()（还有 65 个）

### 社区 1 —— "load_prompts_from_dir"
凝聚度：0.16
节点（共 24 个）：find_prompt(), group_by_prompt(), load_prompts_from_dir(), Return the first PromptSpec whose ``match.files`` glob matches *path*. *path*…, Group semantic files by matching PromptSpec. Returns a dict mapping each…, Scan ``*.yaml`` in *prompt_dir* and return a list of PromptSpec. A malformed…, prompt_dir(), Path（还有 16 个）

### 社区 2 —— "test_extract.py"
凝聚度：0.01
节点（共 274 个）：collect_files(), extract_bash(), Extract functions, source imports, and cross-function calls from a .sh file., extract_json(), _is_config_json(), Path, True if a .json file is a recognized config/manifest worth AST-extracting.…, Extract structure and dependency edges from a *config/manifest* .json file.…（还有 266 个）

### 社区 3 —— "_labels"
凝聚度：0.04
节点（共 70 个）：extract_groovy(), extract_swift(), Extract classes, methods, constructors, and imports from a .groovy/.gradle…, Extract classes, structs, protocols, functions, imports, and calls from a…, extract_apex(), Path, Extract classes, interfaces, enums, methods, and Salesforce constructs from…, _labels()（还有 62 个）

### 社区 4 —— "test_build.py"
凝聚度：0.02
节点（共 109 个）：edge_datas(), Return every edge attribute dict for (u, v); always a list., load_extraction(), parametrize, Already-relative source_file paths must not be modified., A graph where docs/readme.md carries BOTH tiers (#2333 COEXIST): an AST layer…, #2333/#2336 (COEXIST): a semantic-only re-extract of a file replaces only that…, #2333/#2336 inverse: an AST-only re-extract of a file replaces only that file's…（还有 101 个）

### 社区 5 —— "_file_stem"
凝聚度：0.04
节点（共 103 个）：_augment_js_reexport_edges(), _import_lua(), Extract require('module') from Lua variable_declaration nodes., Compatibility wrapper for the JS/TS symbol-resolution post-pass., _file_stem(), Path, Stem used as the node-ID prefix for a file and its symbols. The full path…, _NamespaceExportFact（还有 95 个）

### 社区 6 —— "_read_text"
凝聚度：0.02
节点（共 154 个）：Get the name from a node using config.name_field, falling back to child types., _resolve_name(), _read_text(), _c_collect_type_refs(), _cpp_collect_type_refs(), _cpp_local_var_types(), _csharp_attribute_names(), _csharp_collect_type_refs()（还有 146 个）

### 社区 7 —— "test_languages.py"
凝聚度：0.02
节点（共 125 个）：extract_c(), extract_kotlin(), Extract functions and includes from a .c/.h file., Extract classes, objects, functions, and imports from a .kt/.kts file., extract_elixir(), Path, Extract modules, functions, imports, and calls from a .ex/.exs file., _cpp_preprocess()（还有 117 个）

### 社区 8 —— "test_import_extension_resolution.py"
凝聚度：0.05
节点（共 75 个）：Resolve a JS/TS module path or specifier to a local source file. With a Path…, _resolve_js_module_path(), _import_targets(), Path, Tests for #716 — TypeScript bare-path imports, Svelte 5 rune file imports…, JS variant of the rune file pattern: a `.svelte.js` file (used in JavaScript-…, When both `.svelte.ts` and `.svelte.js` exist (hybrid project mid- migration,…, If `foo.svelte` IS a real markup file, importing `./foo.svelte` must resolve to…（还有 67 个）

### 社区 9 —— "bash.py"
凝聚度：0.25
节点（共 8 个）：_bash_assignment_base(), _bash_source_suffix(), Path, Bash extractor. Moved verbatim from graphify/extract.py., Return the literal path suffix of a variable-built `source` argument, or None…, True if *target* is *ceiling* or lives beneath it, compared lexically…, Resolve a top-level assignment's value to a directory, or None if untracked.…, _within_tree()

### 社区 10 —— "graphify/__main__.py"
凝聚度：0.05
节点（共 124 个）：_agents_install(), _agents_platform_install(), _agents_platform_uninstall(), _agents_uninstall(), _always_on(), _amp_install(), _amp_legacy_cleanup(), _amp_uninstall()（还有 116 个）

### 社区 11 —— "export.py"
凝聚度：0.04
节点（共 107 个）：_cross_community_surprises(), _cross_file_surprises(), god_nodes(), _is_concept_node(), _is_file_node(), _node_community_map(), Graph analysis: god nodes (most connected), surprising connections (cross-…, Return the top_n most-connected real entities - the core abstractions. File-…（还有 99 个）

### 社区 12 —— "detect"
凝聚度：0.02
节点（共 122 个）：detect(), skipif, __snapshots__/ and real jest/vitest snapshots/ dirs are artefacts — excluded., Obsidian metadata and plugin caches are not part of the source corpus (#2493)., #1666: a bare snapshots/ dir with no .snap files is a legit code namespace…, storybook-static/ is a build artefact — must be excluded., Files inside .github/ (workflows etc.) are now indexed (#873)., .next/ (Next.js build cache) must be excluded even after dot-dir fix (#873).（还有 114 个）

### 社区 13 —— "test_llm_backends.py"
凝聚度：0.04
节点（共 85 个）：BaseException, _call_openai_compat(), _looks_like_context_exceeded(), _looks_like_timeout(), _model_requires_default_temperature(), Detect a successful HTTP response that yielded no usable extraction. A local…, Call any OpenAI-compatible API (Kimi, OpenAI, etc.) and return parsed JSON., Heuristically classify an exception as a context-window overflow. Different…（还有 77 个）

### 社区 14 —— "serve.py"
凝聚度：0.07
节点（共 33 个）：_ApiKeyMiddleware, _filter_blank_stdin(), _has_chinese(), _is_searchable(), _query_terms(), _QueryScores, Filter blank lines from stdin before MCP reads it. Some MCP clients (Claude…, # NOTE: no decorators here — the handlers below are plain coroutines,（还有 25 个）

### 社区 15 —— "test_detect.py"
凝聚度：0.04
节点（共 108 个）：_is_sensitive(), Return True if this file likely contains secrets and should be skipped., as_posix_list(), parametrize, Path, `/*` stays at the root, so `!/src/` makes the subtree walkable (#1975)., A regular `*` matches one component; recursive matching requires `**`., A single `!` re-include must not switch off pruning of *unrelated* ignored…（还有 100 个）

### 社区 16 —— "test_export.py"
凝聚度：0.03
节点（共 140 个）：cluster(), Run Leiden community detection. Returns {community_id: [node_ids]}. Community…, _dedup_node_filenames(), existing_graph_node_count(), Path, Export graph as an Obsidian Canvas file - communities as groups, nodes as…, Export graph as GraphML - opens in Gephi, yEd, and any GraphML-compatible tool.…, Node count of an existing graph.json. Returns: - an ``int`` node count when the…（还有 132 个）

### 社区 17 —— "test_install.py"
凝聚度：0.02
节点（共 128 个）：main(), Handle a downstream reader that closed the pipe early. Redirect stdout to…, Console entry point. Wraps the CLI so that when a downstream consumer closes…, _silence_broken_pipe(), _agents_install(), _agents_uninstall(), _cli_dispatched_commands(), _install()（还有 120 个）

### 社区 18 —— "test_dedup.py"
凝聚度：0.03
节点（共 116 个）：deduplicate_entities(), _entropy(), _norm(), Lowercase + collapse non-alphanumeric runs to space (Unicode-aware)., Shannon entropy in bits/char of the normalised label., Deduplicate near-identical entities in a knowledge graph. Args: nodes: list of…, _make_edges(), _make_nodes()（还有 108 个）

### 社区 19 —— "test_serve.py"
凝聚度：0.06
节点（共 62 个）：_communities_from_graph(), _community_header(), _cut_lines_to_budget(), _find_node(), _get_trigram_index(), _infer_context_filters(), _node_search_text(), _normalize_context_filters()（还有 54 个）

### 社区 20 —— "expand_oversized_files"
凝聚度：0.06
节点（共 75 个）：_best_cut(), bisect_slice(), expand_oversized_files(), FileSlice, is_splittable_text(), _pdf_text(), Path, Intra-file slicing for oversized text documents (#1369). The extraction packer…（还有 67 个）

### 社区 21 —— "test_analyze.py"
凝聚度：0.04
节点（共 88 个）：_cross_language(), _file_category(), find_import_cycles(), graph_diff(), _is_json_key_node(), Return the first path component - used to detect cross-repo edges., Score how surprising a cross-file edge is. Returns (score, reasons)., Return True if two source files belong to different language families.（还有 80 个）

### 社区 22 —— "test_dedup_remaps_hyperedges.py"
凝聚度：0.13
节点（共 25 个）：Rewire hyperedge member ids onto dedup survivors, in place. Members come in…, _remap_hyperedge_members(), _extraction(), _members(), _node(), parametrize, Dedup must rewire hyperedge members onto survivors, not drop them. `build()`…, A dedup remap built from union-find is fully flattened (path-compressed), so a…（还有 17 个）

### 社区 23 —— "classify_file"
凝聚度：0.04
节点（共 89 个）：Enum, classify_file(), FileType, Return the interpreter name from a shebang line. Handles forms that a naive…, Peek at the first line of an extensionless file for a shebang., _shebang_file_type(), _shebang_interpreter(), str（还有 81 个）

### 社区 24 —— "test_chunking.py"
凝聚度：0.03
节点（共 93 个）：_chunk_partial_files(), extract_corpus_parallel(), _extract_with_adaptive_retry(), _is_vision_image(), _merge_into(), _merged_partial_files(), _pack_chunks_by_tokens(), Greedily pack files/slices into chunks that fit a token budget. Units are first…（还有 85 个）

### 社区 25 —— "test_dotnet.py"
凝聚度：0.05
节点（共 72 个）：extract_csproj(), extract_slnx(), extract_xaml(), _project_xml_is_safe(), Reject XML that declares DTDs or entities. Stdlib ``xml.etree.ElementTree``…, Extract projects and inter-project dependencies from a .slnx file. .slnx is the…, Extract packages, project refs, and target framework from a…, Extract WPF/XAML structure, bindings, x:Class, and event handler references.（还有 64 个）

### 社区 26 —— "test_pascal.py"
凝聚度：0.05
节点（共 73 个）：extract_lazarus_package(), Extract package metadata from Lazarus .lpk package files (XML format). .lpk is…, extract_pascal(), _extract_pascal_regex(), extract_delphi_form(), extract_lazarus_form(), Path, Extract component hierarchy from Delphi .dfm form files. .dfm files come in two…（还有 65 个）

### 社区 27 —— "test_ignore_file_encoding.py"
凝聚度：0.13
节点（共 25 个）：Read an ignore file, preferring UTF-8 but never silently dropping a rule. These…, _read_ignore_text(), _corpus(), parametrize, r"""An ignore file that is not valid UTF-8 must not silently lose its rules.…, The actual regression: every rule survives, even if a third encoding renders it…, The existing NFC/NFD guarantee must survive the new decode path., A UTF-16 (BOM) .graphifyignore — what PowerShell Set-Content and Notepad…（还有 17 个）

### 社区 28 —— "extract.py"
凝聚度：0.03
节点（共 120 个）：_augment_cpp_string_tests(), _emit_rescued_import(), _extract_js_rationale(), extract_lua(), _extract_parallel(), _extract_python_rationale(), _extract_sequential(), _extract_single_file()（还有 112 个）

### 社区 29 —— "_call_claude_cli"
凝聚度：0.04
节点（共 69 个）：_call_claude_cli(), _call_llm(), _claude_cli_envelope(), _claude_cli_error(), _claude_cli_supports_json_schema(), _no_window_kwargs(), Parse the JSON returned by `claude -p --output-format json`. Older Claude Code…, Return the CLI's own error text when the envelope flags `is_error`. `claude -p`…（还有 61 个）

### 社区 30 —— "test_cli_export.py"
凝聚度：0.06
节点（共 76 个）：_calls(), _init_git_repo(), _make_graph(), CompletedProcess, Path, Integration tests for graphify export subcommands and CLI commands. Each test…, #1423: `graphify extract` honours GRAPHIFY_OUT for where it WRITES, not only…, Write a minimal hand-rolled directed graph.json for path-direction tests.（还有 68 个）

### 社区 31 —— "test_extract_cli.py"
凝聚度：0.05
节点（共 79 个）：_clear_backend_keys(), _code_only_corpus(), _failing_sql(), _make_corpus(), _manifest_row(), _node_sources(), _ok_sql(), parametrize（还有 71 个）

### 社区 32 —— "test_image_vision.py"
凝聚度：0.06
节点（共 55 个）：_anthropic_response_text(), _bedrock_response_text(), _build_image_refs(), _partition_semantic_files(), Return the first Anthropic content block that carries text. Current Claude…, Return the first Converse content block that carries text. Converse returns…, Split a chunk into (text-like units, raster-image files). A ``FileSlice`` is…, Build `_ImageRef`s for raster images. `read_bytes=True` (base64 backends) loads…（还有 47 个）

### 社区 33 —— "install"
凝聚度：0.06
节点（共 49 个）：install(), Install graphify post-commit and post-checkout hooks in the nearest git repo., Check if graphify hooks are installed., status(), _make_git_repo(), Test 2: Without .graphifyrc, generated hooks omit GRAPHIFY_VIZ_NODE_LIMIT…, Test 3: viz_node_limit from .graphifyrc is baked into both hooks., Persisting the project default must not clobber an explicit per-run…（还有 41 个）

### 社区 34 —— "test_ruby_resolution.py"
凝聚度：0.07
节点（共 72 个）：extract_ruby(), Extract classes, methods, singleton methods, and calls from a .rb file., test_ruby_no_error(), _find_raw_call(), _has_call_edge(), _labels(), _method_edges(), _mixes_in()（还有 64 个）

### 社区 35 —— "Communities (141 total, 52 thin omitted)"
凝聚度：0.03
节点（共 71 个）：Communities (141 total, 52 thin omitted), Community 0 - "Community 0", Community 10 - "Community 10", Community 11 - "Community 11", Community 12 - "Community 12", Community 13 - "Community 13", Community 14 - "Community 14", Community 15 - "Community 15"（还有 63 个）

### 社区 36 —— "test_incomplete_build_guard.py"
凝聚度：0.18
节点（共 19 个）：_arm_extract(), _arm_no_cluster(), _make_docs_corpus(), Tests for the incomplete-build shrink-guard on `graphify extract`. A full build…, #2169: an INCREMENTAL --no-cluster run merges the existing graph forward, so…, A present-but-unparseable existing graph.json (corrupt or mid-write) could be…, #2169: an incremental --no-cluster run must hard-fail on an unparseable…, Patch export.to_json to record the ``force`` it was called with and return a…（还有 11 个）

### 社区 37 —— "_edge_labels"
凝聚度：0.04
节点（共 65 个）：extract_csharp(), extract_java(), extract_scala(), Extract classes, interfaces, methods, constructors, and imports from a .java…, Extract C# type declarations, methods, namespaces, and usings from a .cs file., Extract classes, objects, functions, and imports from a .scala file., extract_verilog(), Path（还有 57 个）

### 社区 38 —— "extract_python"
凝聚度：0.05
节点（共 66 个）：extract_python(), Extract classes, functions, and imports from a .py file via tree-sitter AST., All edge sources must reference a known node (targets may be external imports)., contains / method / inherits / imports edges must always be EXTRACTED., Call-graph pass must produce INFERRED calls edges., AST-resolved call edges are deterministic and should be EXTRACTED/1.0., run_analysis() calls compute_score() - must appear as a calls edge., Analyzer.process() calls run_analysis() - cross class→function calls edge.（还有 58 个）

### 社区 39 —— "test_csharp_member_calls.py"
凝聚度：0.06
节点（共 66 个）：_calls(), _find(), C# receiver-typed member-call resolution (#1609). `recv.Method()` where `recv`…, `Svc` exists in namespaces A and B; a caller file `using A;` must bind an…, No using directive and `Svc` in two foreign namespaces: genuinely ambiguous —…, A caller in namespace A resolves `Svc` to A.Svc even though B.Svc also exists —…, A local `Other x` shadowing a field `Server x` makes the name's type…, `var x = Compute();` (untypable) redeclaring a typed field poisons the name:…（还有 58 个）

### 社区 40 —— "_detect_main_language"
凝聚度：0.14
节点（共 10 个）：_detect_main_language(), Detect the backend main language by counting code nodes per language. Walks…, Java backend (3 nodes) + Python build script (1 node) -> java., TS frontend (3 nodes) + Java backend (1 node) -> ts. Frontend-heavy repo: Impl…, Non-code nodes (file_type != 'code') are ignored., Nodes without source_file are skipped., source_file without extension contributes nothing., When two languages have equal counts, the first encountered wins (Python dict…（还有 2 个）

### 社区 41 —— "Embedding 手动验证流程"
凝聚度：0.06
节点（共 35 个）：1.1 确认 Python 版本, 1.2 安装依赖, 1.3 确认 graphify 核心依赖, 1.4 确认运行在 CPU 模式（可选，用于验证无 GPU 也能跑）, 2.1 检查 fixture 项目, 2.2 查看项目结构（可选）, 3.1 确认配置文件, 3.2 运行 extract（强制重建，自动生成 embedding sidecar）（还有 27 个）

### 社区 42 —— "test_js_import_resolution.py"
凝聚度：0.07
节点（共 102 个）：_file_node_id(), File-level node ID matching the skill.md spec: ``{parent_dir}_{stem}`` — one…, _assert_no_root_slug(), _astro_paths(), _astro_project(), Path, Regression tests for #2195: Astro/Svelte regex-rescued imports must not mint…, Relative inputs: the real file node keeps its canonical id — the #1462…（还有 94 个）

### 社区 43 —— "extract_js"
凝聚度：0.03
节点（共 73 个）：extract_js(), Extract classes, functions, arrow functions, and imports from a…, #3035: Calls inside HOF-wrapped export callbacks (with options) are attributed…, #3035 / #1077: Arbitrary `obj.x = wrap(...)` must NOT produce a node., `Foo.prototype.bar = fn` must be captured as a method owned by Foo., `const f = function(){}` (function expression, not arrow) must be captured., A class field initialised with an arrow function (`x = () => {}`) must be…, Guard against the phantom-god-node class (#1077): an arbitrary `obj.x = fn`…（还有 65 个）

### 社区 44 —— "embeddings.py"
凝聚度：0.05
节点（共 48 个）：_build_embed_http_client(), cosine_similarity(), _embed_batch(), _embed_batch_sentence_transformers(), embed_query(), generate_embeddings_for_graph(), _git_rel_path(), load_embedding_sidecar()（还有 40 个）

### 社区 45 —— "build_from_json"
凝聚度：0.07
节点（共 52 个）：build_from_json(), _doc_twin_remap(), _fold_edge_aliases(), Fold legacy edge field aliases onto canonical keys, in place (#2194). ``type``…, Map a markdown quick-scan's bare doc node ``<slug>`` to the semantic…, Build a NetworkX graph from an extraction dict. directed=True produces a…, attach_hyperedges(), Store hyperedges in the graph's metadata dict.（还有 44 个）

### 社区 46 —— "test_multigraph_diagnostics.py"
凝聚度：0.08
节点（共 58 个）：load_graph(), _canonical_edge(), _count_extra(), diagnose_extraction(), diagnose_file(), _edge_list(), _exact_signature(), format_diagnostic_json()（还有 50 个）

### 社区 47 —— "cache.py"
凝聚度：0.06
节点（共 59 个）：_absolutize_ids_in(), _absolutize_source_files_in(), cached_files(), cached_word_count(), _cleanup_stale_ast_entries(), _ensure_stat_index(), _id_anchor(), _mtime_granularity_ns()（还有 51 个）

### 社区 48 —— "extract"
凝聚度：0.07
节点（共 73 个）：_canonicalize_csharp_namespace_nodes(), _check_tree_sitter_version(), extract(), Collapse duplicate C# namespace node entries to one canonical node per label., Raise a clear error if tree-sitter is too old for the new Language API., Extract AST nodes and edges from a list of code files. Two-pass process: 1.…, _labels_by_id(), Builtin-global receiver types must not resolve to same-named user symbols.…（还有 65 个）

### 社区 49 —— "test_codebuddy.py"
凝聚度：0.05
节点（共 63 个）：codebuddy_install(), Install the graphify skill and CODEBUDDY.md section for CodeBuddy., _codebuddy_install_user(), _codebuddy_md_path(), Tests for graphify codebuddy install / uninstall commands., The installed hook must include Read|Glob matcher for file-read interception., Re-install does not duplicate ## graphify sections., Re-install replaces an old graphify section with the current template.（还有 55 个）

### 社区 50 —— "generate_embeddings_incremental"
凝聚度：0.05
节点（共 54 个）：_check_single_project(), Check one project's embedding staleness and refresh if stale. -…, _extract_embed_text_from_git_version(), generate_embeddings_incremental(), _git_diff_changed_node_ids(), Incrementally update the embedding sidecar using git diff on graph.json. Runs…, Return the set of node_ids whose lines changed in graph.json between…, Extract embed text (desc → rationale → "") for a single node_id from the…（还有 46 个）

### 社区 51 —— "normalize_id"
凝聚度：0.08
节点（共 44 个）：given, make_id(), normalize_id(), Single source of truth for node-ID normalization. Three independent producers…, r"""Normalize a single ID string to its canonical form. Guarantees, all…, Build a canonical node ID from one or more name parts. Parts are joined with…, _make_id(), Build a stable node ID via the single shared recipe (#1378).（还有 36 个）

### 社区 52 —— "_extract_node_desc"
凝聚度：0.07
节点（共 27 个）：_clean_desc(), _extract_jsdoc(), _extract_node_desc(), _extract_preceding_comment(), _extract_python_docstring(), _language_from_ts_module(), _node_text(), Node desc field extraction for hybrid semantic search. Extracts…（还有 19 个）

### 社区 53 —— "_parse_llm_json"
凝聚度：0.05
节点（共 55 个）：_parse_llm_json(), Strip optional markdown fences and parse JSON. Returns empty fragment on…, Force ``nodes``/``edges``/``hyperedges`` to lists of dicts, in place. A model…, _sanitize_fragment(), test_sanitize_fragment_coerces_dict_members_to_strings(), _make_envelope(), patch, Tests for `_parse_llm_json` robustness and the `_call_claude_cli` subprocess…（还有 47 个）

### 社区 54 —— "save_semantic_cache"
凝聚度：0.06
节点（共 55 个）：_group_has_partial_marker(), load_cached(), True if any node/edge/hyperedge in a per-file group carries the internal…, Save semantic extraction results to cache, keyed by source_file. Groups nodes…, Return cached extraction for this file if hash matches, else None. Cache key:…, save_semantic_cache(), _mark_partial(), _partial_source_files()（还有 47 个）

### 社区 55 —— "introspect_postgres"
凝聚度：0.13
节点（共 26 个）：introspect_postgres(), _quote_ident(), Connect to PostgreSQL, reconstruct DDL, and extract via extract_sql()., Double-quote a PostgreSQL identifier, escaping embedded double-quotes., _make_mock_psycopg(), _q(), Baseline: tables, views, routines, and a single-column FK all survive., Reserved-word and special-character table names must survive DDL round-trip.…（还有 18 个）

### 社区 56 —— "Communities"
凝聚度：0.04
节点（共 54 个）：Communities, Community 0 - "nanoGPT Model Architecture", Community 10 - "micrograd README + Backprop", Community 11 - "Attention Residuals Paper", Community 12 - "Continual LoRA Paper", Community 13 - "minGPT Trainer Class", Community 14 - "NeuralWalker Paper", Community 15 - "Dataset Abstractions"（还有 46 个）

### 社区 57 —— "cache_dir"
凝聚度：0.07
节点（共 30 个）：cache_dir(), prune_semantic_cache(), Remove orphaned semantic cache entries, returning the count pruned. The…, Returns the cache directory for ``kind`` - creates it if needed. kind is "ast",…, Prune touches only cache/semantic/*.json: AST entries and atomic-write *.tmp…, #1894 follow-up to #1527: prune must sweep cache/semantic/ AND cache/semantic-…, #1916 guard-rail: unscoped callers (allowed_source_files=None) must stay byte-…, A glob that stopped at the top level would leave every fingerprinted entry…（还有 22 个）

### 社区 58 —— "test_ddd_extractor.py"
凝聚度：0.04
节点（共 61 个）：_build_global_node_index(), Build concept_id → node and name → node index from ALL collected nodes. Uses…, Resolve a reference (concept_id or name) to a node using the global index.…, _resolve_ref(), clear_registry(), DocExtractor, _NotApplicable, Exception（还有 53 个）

### 社区 59 —— "test_skillgen.py"
凝聚度：0.06
节点（共 50 个）：_platform_artifacts(), Tests for the tools/skillgen generator and the claude lean-core split. skillgen…, `agents` re-homes amp's agents-md body but with its OWN install wording. It…, The Windows bootstrap must not write the sidecar markers with a BOM (#3028).…, windows: name must be `graphify` (folder-name rule, #1635), powershell install,…, codex: spawn/wait/close_agent dispatch needing multi_agent = true., codex (was 4-value) and windows (was 5-value) now carry the superset., The extraction variant differs: codex compact, windows verbose.（还有 42 个）

### 社区 60 —— "test_scip_ingest.py"
凝聚度：0.06
节点（共 35 个）：Comprehensive tests for graphify.scip_ingest., Cross-document relationship resolves to the target document's node id., A relationship entry whose `symbol` is a non-string is silently skipped., A non-dict entry in `documents` is silently skipped., When two docs both have `F#`, a relationship from b.py's F# to F# must resolve…, When occurrences list is empty, source_location is empty string., Duplicate symbol records within the SAME document collapse to one node id in…, SCIP-supplied description must be HTML-escaped before reaching node metadata; a…（还有 27 个）

### 社区 61 —— "test_reflect.py"
凝聚度：0.09
节点（共 49 个）：aggregate_lessons(), Aggregate parsed memory docs into a deterministic lessons structure. ``now``…, Render the aggregate into the deterministic LESSONS.md markdown body., render_lessons_md(), _days_before(), _doc(), Tests for `graphify reflect` and the work-memory reflection layer. `graphify…, Corroboration (k>=2) + sign decide the bucket, not raw frequency: A is useful…（还有 41 个）

### 社区 62 —— "test_serve_http.py"
凝聚度：0.10
节点（共 47 个）：_build_http_app(), _main(), _max_server_contexts(), _MCPASGIApp, Raw-ASGI wrapper around the Streamable HTTP session manager. Passed to a…, Build the Starlette ASGI app for the Streamable HTTP transport. Split out from…, Start the MCP server over Streamable HTTP (MCP spec 2025-03-26). Serves the…, Return the project-context LRU capacity (default 8, minimum 1).…（还有 39 个）

### 社区 63 —— "test_devin.py"
凝聚度：0.05
节点（共 51 个）：_devin_rules_install(), Write .windsurf/rules/graphify.md for always-on Devin context., _devin_install_user(), Tests for graphify devin install / uninstall commands., The rules file installed by devin must use query-first policy., Installing rules twice does not change content and prints 'no change'., Project-scope install prints a git add hint covering .devin/ and .windsurf/., User-scope uninstall removes the skill file.（还有 43 个）

### 社区 64 —— "test_manifest_ingest.py"
凝聚度：0.08
节点（共 44 个）：_coerce_deps(), extract_package_manifest(), is_package_manifest_path(), _parse_apm(), _parse_apm_fallback(), _parse_cargo(), _parse_pyproject(), _pep508_name()（还有 36 个）

### 社区 65 —— "test_global_graph.py"
凝聚度：0.11
节点（共 43 个）：prefix_graph_for_global(), prune_repo_from_graph(), Return a copy of G with all node IDs prefixed with repo_tag::. Labels are…, Remove all nodes tagged with repo_tag from G in-place. Returns count removed., _file_hash(), global_add(), global_list(), global_remove()（还有 35 个）

### 社区 66 —— "gen.py"
凝聚度：0.05
节点（共 47 个）：The translator is strict: a bash line it does not recognize fails the render…, test_powershell_translator_rejects_unknown_bash(), _core_to_powershell(), _enum_lines(), _is_cache_unlink_fix_line(), _is_chunk_cleanup_line(), _is_community_label_export_fix_line(), _is_content_scope_fix_line()（还有 39 个）

### 社区 67 —— "extract_cpp"
凝聚度：0.06
节点（共 45 个）：_blank_keeping_newlines(), extract_cpp(), _normalize_cpp_cli(), Replace a match with spaces, but keep its line breaks. Byte length alone is not…, Rewrite C++/CLI spellings to standard C++ ones, or None if not C++/CLI. The…, Extract functions, classes, and includes from a .cpp/.cc/.cxx/.hpp file.…, _labels(), parametrize（还有 37 个）

### 社区 68 —— "extract_files_direct"
凝聚度：0.07
节点（共 48 个）：_backend_env_keys(), _backend_supports_vision(), detect_backend(), extract_files_direct(), _get_backend_api_key(), _ollama_host_is_link_local_or_metadata(), Return accepted API-key environment variables for a backend., Return the first configured API key for backend, or an empty string.（还有 40 个）

### 社区 69 —— "test_benchmark.py"
凝聚度：0.10
节点（共 43 个）：_estimate_tokens(), _hr(), print_benchmark(), _query_subgraph_tokens(), Token-reduction benchmark - measures how much context graphify saves vs naive…, Print a human-readable benchmark report., Return unicode_char if stdout can encode it, else ascii_fallback. Windows…, Horizontal rule that survives non-UTF-8 stdout (e.g. Windows cp1252 console).（还有 35 个）

### 社区 70 —— "audit_coverage"
凝聚度：0.08
节点（共 30 个）：The per-host audit (the guard amp is the exact case for) passes for amp. amp…, `agents` is a post-v8 platform, so its audit baseline is amp's v8 body., The query section heading is the lean-core stub; query.md re-homes the rest., The fence-aware heading scanner must skip '#' lines inside code fences., Every v8 heading single-homes for the cli-inline split hosts too., Every v8 heading lands in the lean core or exactly one reference., Every split host's render single-homes its own v8 body's headings., The audit baseline is the host's OWN v8 skill body, not claude's monolith. This…（还有 22 个）

### 社区 71 —— "test_indirect_dispatch.py"
凝聚度：0.10
节点（共 44 个）：_build(), _extract(), _extract_dir(), _extract_js_dir(), Indirect dispatch edges. A function passed BY NAME as a call argument…, No recall regression: a real module fn passed by name still emits an edge., Regression: when the scan root relativizes node ids (cache_root == project…, The cross-file resolver guard in extract.py must suppress indirect_call edges…（还有 36 个）

### 社区 72 —— "build"
凝聚度：0.05
节点（共 53 个）：build(), _coerce_non_string_ids(), _fold_node_aliases(), Merge multiple extraction results into one graph. directed=True produces a…, Fold legacy node field aliases onto canonical keys, in place (#2194). ``name``…, Coerce numeric node ids and edge/hyperedge references to str, in place (#2326).…, #1007: manifest stores absolute paths, graph nodes store relative paths.…, #1007: prune_sources with Windows-style backslash absolute paths must still…（还有 45 个）

### 社区 73 —— "test_evidence_binding.py"
凝聚度：0.17
节点（共 20 个）：_bind_node_evidence(), _label_identifiers(), Identifier tokens from a node label, stripped of a trailing call/args…, Downgrade code-typed nodes whose symbol name has no evidence in the source the…, _by_label(), Tests for semantic evidence-binding in graphify.llm. A code node the model…, Drive extract_files_direct with a faked backend returning ``nodes``., _run()（还有 12 个）

### 社区 74 —— "reflect.py"
凝聚度：0.09
节点（共 43 个）：_build_id_label_maps(), build_learning_overlay(), _code_fingerprint(), _content_hash(), _decay(), _dedupe_by_question(), _empty_bucket(), _finalize_sources()（还有 35 个）

### 社区 75 —— "build_tree"
凝聚度：0.16
节点（共 24 个）：build_tree(), _common_root(), emit_html(), _make_truncation_leaf(), Any, Path, tree_html — emit a D3 v7 collapsible-tree HTML view of a graph. A self-…, Build a ``{name, total_count, children}`` hierarchy. Each leaf is either a code…（还有 16 个）

### 社区 76 —— "edge_data"
凝聚度：0.08
节点（共 45 个）：edge_data(), Return one edge attribute dict for (u, v), tolerating MultiGraph. For…, #2194: edges carrying `type`/`confidence_score` instead of…, Pre-enum graphs stored the LLM pass's float directly in `confidence`…, A numeric `confidence` next to an explicit `confidence_score` must not…, The on-disk shape of the defect: a NetworkX-serialized graph.json (`links`…, Healing must survive a round-trip: after the first load rewrites the tag to…, #1279: a semantic/LLM edge lacking source_file must inherit it from its source…（还有 37 个）

### 社区 77 —— "extract_objc"
凝聚度：0.05
节点（共 43 个）：extract_objc(), Path, Extract interfaces, implementations, protocols, methods, and imports from…, `@protocol Derived <Base>` must emit an implements edge Derived->Base.…, `[self speak]` inside Dog.fetch must produce a calls edge. The method-body…, `+ (…)shared` is a class method and must be labeled +shared, not -shared…, A compound message `[self a:x b:y]` resolves to the compound method def (#1475)., `NSArray<Product *> *` must reference the element type Product (and the…（还有 35 个）

### 社区 78 —— "_get_extractor"
凝聚度：0.12
节点（共 20 个）：_get_extractor(), _is_cpp_header(), _is_objc_header(), _is_objc_source(), Any, Whether a `.h` file is Objective-C rather than C/C++ (#1475). `.h` is shared by…, Whether a `.m` file is Objective-C rather than MATLAB/Octave (#1702). `.m` is…, Whether a `.h` file is C++ rather than plain C (#1547). Mirrors…（还有 12 个）

### 社区 79 —— "test_mcp_ingest.py"
凝聚度：0.11
节点（共 38 个）：extract_mcp_config(), is_mcp_config_path(), Path, Return True when ``path`` is a recognised MCP config filename., Parse an MCP config file into Graphify nodes and edges. Behaviour matches other…, _label_by_kind(), Path, Tests for graphify.mcp_ingest — MCP config file extraction.（还有 30 个）

### 社区 80 —— "_score_nodes"
凝聚度：0.05
节点（共 45 个）：Combined query scorer returning the existing ranked `(score, node_id)` list.…, _score_nodes(), _make_random_scoring_graph(), parametrize, A multi-word query equal to a whole label must resolve uniquely. Regression for…, Searching for '路由' should match a node with label containing '路由'., Test-only oracle for the legacy per-term `_pick_seeds(terms=...)` loop. Re-…, Reproducible broad-match DiGraph: short constructed labels + edge noise. Labels…（还有 37 个）

### 社区 81 —— "_query_graph_text"
凝聚度：0.08
节点（共 28 个）：_query_graph_text(), _build_multi_seed_graph(), Graph with several equally-matchable seed candidates for top_n tests., AC14: default (top_n=1) returns single subgraph, no === Result., AC13: top_n=3 returns 3 subgraphs separated by === Result i/3 ===., AC14: explicit top_n=1 also returns single subgraph., top_n=0 should not crash — falls through to the top_n<=1 branch., When the query matches nothing, top_n>1 returns the no-match message.（还有 20 个）

### 社区 82 —— "test_affected_cli.py"
凝聚度：0.08
节点（共 32 个）：resolve_seed(), A trailing path separator must not change the match (parity with explain's…, Several nodes share a source_file but none is the L1 file node and none's…, A caller whose call site (L158) differs from its own def line (L90)., An edge with no stored location honestly falls back to the node's def line., `./x.py`, an absolute path and `x.py` name one file and must resolve alike. The…, An absolute-path seed resolves off the graph's location, not the cwd (#2706).…, An absolute seed that is NOT under the derived repo root must report a clean…（还有 24 个）

### 社区 83 —— "test_query_induced_edges.py"
凝聚度：0.14
节点（共 32 个）：_bfs(), _complete_induced_edges(), _dfs(), _filter_graph_by_context(), Append edges between visited nodes that the traversal never recorded (#2323).…, _add(), _induced(), _link()（还有 24 个）

### 社区 84 —— "Path"
凝聚度：0.11
节点（共 23 个）：_batch_needs_llm_flag(), _batch_triggers_rebuild(), _has_non_code(), _is_relative_to(), Path, True when a debounced watch batch needs an immediate rebuild. Code changes…, True when the batch contains a non-code file that still exists on disk. Only…, Resolve source_file values across current and legacy graph roots.（还有 15 个）

### 社区 85 —— "test_query_names_its_graph.py"
凝聚度：0.17
节点（共 19 个）：_display_graph_path(), Render a graph path for the query header. Relative to the CWD when it sits…, _graph(), _header(), A query answer must say which graph it came from. `.graph/` resolves against…, A display helper must not be the reason a query fails., The end-to-end point: the parent and the subproject must not look alike., The case the issue is about: the answer came from somewhere else.（还有 11 个）

### 社区 86 —— "test_install_references.py"
凝聚度：0.06
节点（共 40 个）：_build_wheel_names(), fake_bundle(), _first_unbuilt_progressive_host(), _install(), Tests for the progressive-disclosure references/ sidecar install path. The real…, Reinstall swaps references/ in place, dropping a stale fragment., Uninstall rmtrees references/ before the dir walk so the tree is cleared., If SKILL.md links references/ but the dir is gone, warn to repair.（还有 32 个）

### 社区 87 —— "_pick_seeds"
凝聚度：0.09
节点（共 22 个）：_pick_seeds(), Select BFS seed nodes, stopping when score drops too far below the top.…, End-to-end for #1900: a German question over a graph with German heading-noise…, FooBarService at 1000 vs error nodes at 1.0 → only 1 seed chosen., When all scores are within 20% of the top, keep up to 3 seeds., Never return more than max_k seeds even when all scores are close., G/best_seed_by_term are optional and default to None: existing callers see…, Reproduces #1445: a vague natural-language query where one term's incidental…（还有 14 个）

### 社区 88 —— "claude_install"
凝聚度：0.07
节点（共 39 个）：claude_install(), Write the graphify section to the local CLAUDE.md., Tests for graphify claude install / uninstall commands., claude_install also writes .claude/settings.json with PreToolUse hook., Running claude_install twice does not duplicate the PreToolUse hook., Creates CLAUDE.md when none exists., claude_uninstall removes the PreToolUse hook from settings.json., A hook relocated to .claude/settings.local.json is removed on uninstall.（还有 31 个）

### 社区 89 —— "ingest_scip_json"
凝聚度：0.05
节点（共 40 个）：ingest_scip_json(), Convert a SCIP-style JSON document into Graphify nodes and edges. Parameter…, Cross-symbol relationship within ONE document resolves via the symbol index., Result passes Graphify's validate_extraction and build_from_json keeps the…, A symbol entry with `symbol: <int>` is silently skipped., A symbol with `relationships: None` ingests without error and emits no edges., A symbol with `kind` as a non-string falls back to 'unknown'., `display_name` as a non-string falls back to the symbol suffix.（还有 32 个）

### 社区 90 —— "test_transcribe.py"
凝聚度：0.08
节点（共 35 个）：build_whisper_prompt(), download_audio(), _get_whisper(), _get_yt_dlp(), is_url(), _model_name(), Path, Transcribe a video/audio file or URL to a .txt transcript. If video_path is a…（还有 27 个）

### 社区 91 —— "User"
凝聚度：0.06
节点（共 28 个）：创建用户, 按邮箱查询用户, 检查邮箱唯一性, 用户不存在, 邮箱已注册, 密码变更, 用户删除, 用户恢复（还有 20 个）

### 社区 92 —— "聚合协作视图 — 用户管理"
凝聚度：0.06
节点（共 30 个）：业务流程 — 用户管理, 入口点, 入口点, 失败/补偿矩阵, 失败/补偿矩阵, 时序编排, 时序编排, 用例: 用户注册（还有 22 个）

### 社区 93 —— "_make_graph"
凝聚度：0.05
节点（共 51 个）：_load_graph(), Render subgraph as text, cutting at token_budget (approx 3 chars/token). seeds:…, _subgraph_to_text(), _make_graph(), A high-degree hub plus a low-degree answer node, to force the answer past a…, BUG2: a low-degree answer node passed as a seed is rendered first and survives…, BUG2 regression guard: the query path must pass seeds to the renderer (a branch…, #2601: nodes render before edges, so a budget overflow that only trims trailing…（还有 43 个）

### 社区 94 —— "exceptions.py"
凝聚度：0.08
节点（共 32 个）：CloseError, ConnectTimeout, DecodingError, NetworkError, PoolTimeout, ProtocolError, ProxyError, httpx-like exception hierarchy. All exceptions inherit from HTTPError at the…（还有 24 个）

### 社区 95 —— "raw/analyze.py"
凝聚度：0.09
节点（共 34 个）：_cross_community_surprises(), _cross_file_surprises(), _file_category(), god_nodes(), graph_diff(), _is_concept_node(), _is_file_node(), _node_community_map()（还有 26 个）

### 社区 96 —— "_estimate_file_tokens"
凝聚度：0.07
节点（共 45 个）：_dispatched_source_text(), _estimate_file_tokens(), _file_to_text(), _get_tokenizer(), _pdf_text_for_estimate(), Path, Extracted text of a PDF, memoised for the packing pass., Estimate the prompt-token cost of a file or slice under `_read_files` rules.…（还有 37 个）

### 社区 97 —— "Response"
凝聚度：0.11
节点（共 7 个）：AsyncClient, BaseClient, Client, Asynchronous HTTP client., Shared implementation for Client and AsyncClient. Handles auth, redirects,…, Synchronous HTTP client., Response

### 社区 98 —— "3. Tier 2 扩展:提示词型解析器"
凝聚度：0.05
节点（共 38 个）：1. 背景:graphify 的两层提取, 2.1 接口契约, 2.2 三种合并策略, 2.3 生产集成, 2.4 检索集成, 2.5 节点建模约定, 2.6 边 shape, 2.7 参考实现（还有 30 个）

### 社区 99 —— "test_cache.py"
凝聚度：0.04
节点（共 61 个）：_body_content(), check_semantic_cache(), Check semantic extraction cache for a list of absolute file paths. Returns…, Strip YAML frontmatter from Markdown content, returning only the body., Tests for graphify/cache.py., mode='deep' saves under cache/semantic-deep/ and reads back from it., Deep entries must not satisfy mode=None reads (and plain entries must not…, Omitting mode writes exactly the historical cache/semantic/ layout — forward-…（还有 53 个）

### 社区 100 —— "test_obsidian_vault_migration.py"
凝聚度：0.13
节点（共 27 个）：_adopt_pre_manifest_notes(), _is_graphify_note(), Whether a vault note carries graphify's own frontmatter signature. Every note…, Names of notes in *out* that graphify itself wrote before manifests existed.…, _export(), _graph(), _notes(), pre_manifest_vault()（还有 19 个）

### 社区 101 —— "_hooks_dir"
凝聚度：0.12
节点（共 19 个）：_hooks_dir(), Raise if a hooks path looks like a Windows absolute path (#1385). On POSIX/WSL…, Return the git hooks directory, respecting core.hooksPath if set (e.g. Husky).…, _reject_windows_path(), _append_duplicate_config_entries(), Path, A Windows-style core.hooksPath must raise (loud failure), not silently create a…, A legitimate POSIX core.hooksPath (Husky-style) must still install.（还有 11 个）

### 社区 102 —— "test_user_management_e2e.py"
凝聚度：0.05
节点（共 24 个）：doc_anchors(), edges(), graph(), nodes(), Any, E2E tests for the DDD doc-extractor on a real user-management project. These…, Verify the graph contains BOTH code nodes AND doc-anchor nodes, proving the…, Verify the three-phase pipeline (code+manifests → config JSON → doc) ran,…（还有 16 个）

### 社区 103 —— "hooks.py"
凝聚度：0.10
节点（共 35 个）：_git_root(), _has_merge_attr(), _install_hook(), _load_graphifyrc(), _merge_attr_line(), _merge_default_graphifyrc(), _merge_driver_status(), _parse_graphifyrc_file()（还有 27 个）

### 社区 104 —— "test_querylog.py"
凝聚度：0.12
节点（共 31 个）：_log_path(), log_query(), _log_responses(), nodes_from_result(), Any, Path, Query logging for graphify — append-only JSONL, fail-silent., Append one JSONL record to the query log. Never raises.（还有 23 个）

### 社区 105 —— "/graphify"
凝聚度：0.06
节点（共 32 个）：For always-on context in Devin sessions, For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For --update (incremental re-extraction)（还有 24 个）

### 社区 106 —— "/graphify"
凝聚度：0.06
节点（共 32 个）：For always-on context in Devin sessions, For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For --update (incremental re-extraction)（还有 24 个）

### 社区 107 —— "/graphify"
凝聚度：0.06
节点（共 32 个）：For always-on context in Devin sessions, For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For --update (incremental re-extraction)（还有 24 个）

### 社区 108 —— "Spec: DDD 文档自定义解析器 + 解析器优先级机制"
凝聚度：0.06
节点（共 31 个）：10. 风险, 1. 背景与问题, 2. 设计目标, 3.1 白名单文件名（按文件名匹配，不依赖路径）, 3.2 标签表 5 类白名单, 3.3 标签表三列约定, 3.4 边类型与权重, 3. DDD 文档白名单（还有 23 个）

### 社区 109 —— "Docker MCP Toolkit + SQLite MCP server"
凝聚度：0.20
节点（共 9 个）：Docker MCP Toolkit + SQLite MCP server, Install, Prerequisites, Smoke test, Storage layout, Troubleshooting, Uninstall / reset, Why SQLite (and not `sqlite-mcp-server`)（还有 1 个）

### 社区 110 —— "HttpClient"
凝聚度：0.10
节点（共 25 个）：__global__, AuthedHttpClient, token_, Connection, resource, string, T, HttpClient（还有 17 个）

### 社区 111 —— "extract_commonlisp"
凝聚度：0.09
节点（共 37 个）：extract_commonlisp(), Path, Extract packages, classes, functions, methods, macros, and calls from a Common…, _needs_commonlisp, A superclass defined in another file must still yield an inherits edge. The…, The def-prefix heuristic should catch definline / definline-maybe., Functions defined via custom definers should appear in the call graph., upi=, upi<, upi> must produce distinct ids (operator chars matter).（还有 29 个）

### 社区 112 —— "callflow_html.py"
凝聚度：0.09
节点（共 31 个）：build_community_index(), _community_text(), derive_sections_from_communities(), _describe_node(), generate_overview_cards(), html_anchor_id(), _keyword_score(), label_for_community()（还有 23 个）

### 社区 113 —— "validate_extraction"
凝聚度：0.16
节点（共 21 个）：assert_valid(), Validate an extraction JSON dict against the graphify schema. Returns a list of…, Raise ValueError with all errors if extraction is invalid., validate_extraction(), #2194: nodes carrying `name`/`path` instead of `label`/`source_file` must be…, test_legacy_node_name_path_aliases_folded(), test_assert_valid_passes_silently(), test_assert_valid_raises_on_errors()（还有 13 个）

### 社区 114 —— "test_labeling.py"
凝聚度：0.16
节点（共 25 个）：generate_community_labels(), label_communities(), _placeholder_community_labels(), Return a complete ``{cid: name}`` map using ``backend`` for naming. Communities…, CLI entry point: resolve a backend, name communities, and degrade to…, _graph(), Tests for LLM-backed community labeling (issue #1097). Backend calls are mocked…, god_nodes() returns list[dict] with an 'id' key, not bare ids.（还有 17 个）

### 社区 115 —— "test_explain_cli.py"
凝聚度：0.12
节点（共 31 个）：Regression tests for `graphify explain` arrow direction (#853)., No sidecar => no Lesson line; output identical to pre-feature., BUG1: an explain connection shows the edge's call-SITE line (in the caller's…, A node with n_callers callers, spread across `files` (default: 3 files, so…, Baseline: the cut count is still announced (pre-existing behavior)., #2009: past the top-20 cutoff, the remaining callers must still be accounted…, Regression guard: nodes at or below the 20-connection cutoff keep the pre-#2009…, Pin the exact `> 20` cutoff itself. The other #2009 tests use 30 and 5…（还有 23 个）

### 社区 116 —— "业务约束提取参考（DDD）"
凝聚度：0.07
节点（共 28 个）：§10 非 DDD 代码库策略, §1 方法论：读码是为了问对问题, §2 代码信号读取与提问素材生成, §4 模式识别：业务流程（Step 3）, §5 模式识别：契约（Step 4）, §6 模式识别：业务事件（Step 5）, Step 3 实现指导：共建关键业务用例, Step 4 实现指导：共建业务契约（还有 20 个）

### 社区 117 —— "parametrize"
凝聚度：0.07
节点（共 31 个）：_pinned_python(), Return sys.executable if its path is shell-safe, else an empty string. Applies…, _launcher_payload(), parametrize, The rebuild must survive a marker written by Windows PowerShell 5.1 (#3028).…, Git for Windows' bundled shell ships no `nohup`/`setsid`, so the old `nohup ...…, The replacement detaches via Python: start_new_session on POSIX and…, Git for Windows/MSYS hooks can expose fragile pipe handles to spawned…（还有 23 个）

### 社区 118 —— "test_minhash.py"
凝聚度：0.11
节点（共 24 个）：_lsh_integrate(), _mh_coeffs(), MinHash, MinHashLSH, _optimal_lsh_params(), ndarray, MinHash + band-LSH — datasketch-compatible drop-in (no scipy). datasketch.lsh…, MinHash sketch — same API as datasketch.MinHash for the subset used here.（还有 16 个）

### 社区 119 —— "/graphify"
凝聚度：0.06
节点（共 30 个）：For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For native CLAUDE.md integration, For --update (incremental re-extraction)（还有 22 个）

### 社区 120 —— "build_merge"
凝聚度：0.06
节点（共 61 个）：build_merge(), Load existing graph.json, merge new chunks into it, and save back. Re-extracted…, _he_ids(), Path, skipif, Incremental --update: hyperedge preservation (#1574) and root-less prune…, A symlinked scan root (macOS /var -> /private/var, symlinked home/worktree)…, #1796: a file present in BOTH new_chunks (re-extracted) and prune_sources must…（还有 53 个）

### 社区 121 —— "skipif"
凝聚度：0.10
节点（共 31 个）：_assert_harness_can_reject(), _broken_uv_machine(), _detect_run(), _extract_case_pattern(), skipif, Run the emitted _PYTHON_DETECT under a real sh in a controlled environment —…, #2852's machine: the only graphify-importable python lives in the uv tool venv;…, Create a fake uv tool env python under <home>/.local/share/uv/tools; ok=False…（还有 23 个）

### 社区 122 —— "render_all"
凝聚度：0.08
节点（共 31 个）：#1939: a skill's cache read and write must both name the extraction prompt they…, Regression for #1461: every skill body that describes Step 3 extraction must…, The committed codex/windows artifacts match a fresh render and expected/., The committed artifacts and the expected/ snapshot match a fresh render. This…, Rendering twice yields byte-identical output (no timestamps/versions)., check + audit-coverage pass for every rendered progressive host., Generated artifacts use LF newlines and end in exactly one newline., No generated artifact carries the package version string.（还有 23 个）

### 社区 123 —— "/graphify"
凝聚度：0.06
节点（共 30 个）：For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For native CLAUDE.md integration, For --update (incremental re-extraction)（还有 22 个）

### 社区 124 —— "/graphify"
凝聚度：0.06
节点（共 30 个）：For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For native CLAUDE.md integration, For --update (incremental re-extraction)（还有 22 个）

### 社区 125 —— "markdown.py"
凝聚度：0.18
节点（共 15 个）：_active_scan_root(), _build_link_index(), _first_paragraph_after(), _nfc(), Path, Markdown extractor. Moved verbatim from graphify/extract.py., The scan root of the extraction in flight, or None outside extract().…, Index every linkable document under *root* by NFC-normalized basename. Each…（还有 7 个）

### 社区 126 —— "_is_ignored"
凝聚度：0.06
节点（共 33 个）：_has_coverage_artifacts(), _has_venv_markers(), _is_ignored(), _is_noise_dir(), Return True if the path should be ignored per .graphifyignore patterns. Uses…, True only when *d* holds files a coverage tool actually generated. ``coverage``…, True only when *d* has actual virtualenv/conda structure on disk.…, Return True if this directory name looks like a venv, cache, or dep dir.（还有 25 个）

### 社区 127 —— "run_language_resolvers"
凝聚度：0.12
节点（共 27 个）：LanguageResolver, Path, Registry for cross-file, language-specific resolution passes. Some…, One cross-file, language-specific resolution pass. ``resolve`` has the…, Append a resolver to the global registry and return it (for inline use)., Return a copy of the registered resolvers, in registration order., Run every resolver whose suffix appears in ``paths``. Behaviorally identical to…, register()（还有 19 个）

### 社区 128 —— "Cookies"
凝聚度：0.07
节点（共 19 个）：Invoke-Main(), Cookies, build_url_with_params(), flatten_queryparams(), is_known_encoding(), normalize_header_key(), obfuscate_sensitive_headers(), parse_content_type()（还有 11 个）

### 社区 129 —— "TestSubprocessEncoding"
凝聚度：0.07
节点（共 18 个）：Regression tests for UnicodeEncodeError on Windows cp1252 console. On Windows…, Writing a file with → ✅ ≥ then passing its content through _call_claude_cli…, _call_llm with backend='claude-cli' must also use encoding='utf-8'., extract_corpus_parallel must surface chunk failures loudly — either via non-…, When chunks fail, extract_corpus_parallel must record failed_chunks > 0 in its…, A summary line must appear on stderr when ≥1 chunk fails., When all chunks succeed, failed_chunks must be 0 and no failure summary should…, Exercises the same code path as the rsl-siege-manager reproduction without…（还有 10 个）

### 社区 130 —— "test_indirect_call_function_expression_shadow.py"
凝聚度：0.12
节点（共 29 个）：_extract_js_dir(), _indirect(), An untracked `function (…) {…}` expression's bindings must shadow indirect_call…, Locals, not just parameters, are scoped to the expression's body., Control: the arrow path was already correct and must stay correct., The bindings are scoped to the expression: a same-named module callable…, Two function expressions in one initializer are SEPARATE scopes: the first…, Widening the shadow set must not blanket-suppress inside the body: an…（还有 21 个）

### 社区 131 —— "Plan: DDD 文档自定义解析器 + 解析器优先级机制"
凝聚度：0.07
节点（共 28 个）：0. 改动总览, 1.1 文件内容, 1.2 验证, 1. 步骤 1：创建注册表 `graphify/extractors/registry.py`, 2.1 完整文件内容（三个 parser 从 .mjs 逐行移植，节点字段全通用 + tags 编码 DDD 类型）, 2.2 实现说明, 2. 步骤 2：创建 DDD 解析器 `graphify/extractors/ddd.py`, 3.1 在 `graphify/extractors/__init__.py` 追加注册 import（还有 20 个）

### 社区 132 —— "write_callflow_html"
凝聚度：0.09
节点（共 28 个）：build_section_node_map(), CallflowOptions, classify_edges(), detect_lang(), html_comment_text(), infer_project_name(), load_labels(), load_report()（还有 20 个）

### 社区 133 —— "test_callflow_html.py"
凝聚度：0.12
节点（共 28 个）：first_list(), generate_call_table_rows(), load_graph(), _node_link_payload(), Return the first list from a set of possible schema locations., Generate call table row scaffolding for a section's nodes. The Caller/Callee…, Read current graphify graph.json via NetworkX's node-link parser., Load graph.json. Returns normalized (nodes, edges, hyperedges, metadata).（还有 20 个）

### 社区 134 —— "extract_dart"
凝聚度：0.13
节点（共 11 个）：extract_dart(), Path, Extract classes, mixins, functions, imports, generic calls, and annotations…, Test that the universal parser successfully extracts generic relationships,…, Test complex Dart 3+ syntax and precise Riverpod/Bloc mappings., Test that the parser successfully handles namespaces in extends/implements, and…, Test typedefs, mixin on, factories, constructor DI types, and universal…, Test all 5 roadmap bug fixes (Bug A, B, C, D, E).（还有 3 个）

### 社区 135 —— "mcp_ingest.py"
凝聚度：0.24
节点（共 12 个）：_add_edge(), _add_node(), _detect_package_from_args(), _emit_server(), Any, mcp_ingest.py — Extract MCP (Model Context Protocol) server configuration…, Emit nodes/edges for one entry under ``mcpServers``., Return the first arg that looks like an npm or pypi package id, else None.…（还有 4 个）

### 社区 136 —— "test_go_qualified_resolution.py"
凝聚度：0.16
节点（共 28 个）：_case_only_sibling_corpus(), _extract(), _ids(), Path, Regression coverage for package-qualified Go calls and type references., An aliased internal qualified type points to its package definition., Changed callers still resolve calls and types defined in unchanged files., Exported wrapper + unexported worker of the same name, plus a decoy.（还有 20 个）

### 社区 137 —— "test_install_roundtrip.py"
凝聚度：0.08
节点（共 28 个）：_copy_in_tmp(), fake_progressive_bundle(), _has_real_bundle(), _install_via_entrypoint(), parametrize, Full per-platform install + uninstall round-trip suite. Every platform graphify…, amp's project-scope skill lands under .agents/skills, an Amp search root., VS Code Copilot Chat round trip at ~/.copilot/skills/graphify + instructions…（还有 20 个）

### 社区 138 —— "test_path_cli.py"
凝聚度：0.10
节点（共 28 个）：_arrow_line(), _diamond_graph(), _flipped_marker_graph(), Regression tests for `graphify path` arrow direction (#849) and determinism +…, No full-token candidate -> behavior identical to the old scored[0] pick., Two equal-length routes A->P->B and A->Q->B — a tie the traversal must resolve…, #2074: the same graph must yield the same route regardless of PYTHONHASHSEED.…, #2074: the printed relation must be the edge's ACTUAL stored relation, never a…（还有 20 个）

### 社区 139 —— "Request"
凝聚度：0.10
节点（共 11 个）：ConnectError, Failed to establish a connection., Request, BaseTransport, ConnectionPool, HTTPTransport, MockTransport, A transport for testing that returns predefined responses. Pass a handler…（还有 3 个）

### 社区 140 —— "build_label_index"
凝聚度：0.13
节点（共 19 个）：build_label_index(), build_python_symbol_index(), node_is_resolvable_symbol(), _node_source_stem(), normalise_callable_label(), Any, Return the stem of a node's source file., Build ``(module_stem, normalized_symbol_name) -> node_ids``. This index is…（还有 11 个）

### 社区 141 —— "Spec: 混合语义检索（语义 + fuzzy 重排）"
凝聚度：0.07
节点（共 27 个）：1. 背景与问题, 2. 设计目标, 3. 参考方案：llm-wiki 的混合检索 pipeline, 4.1 三阶段打分公式, 4.2 为什么是加法 tier 而非替换, 4.3 触发条件, 4. 混合检索架构, 5.1 生成时机：build-time（还有 19 个）

### 社区 142 —— "test_csharp_interface_dispatch.py"
凝聚度：0.13
节点（共 26 个）：_is_csharp(), _method_label(), Member-level interface dispatch for C# (#3003). A C# call through a…, True when the node is a declaration that lives in a C# file. Every end of a…, Return a method node's bare name, for matching. Case is kept: C# is case…, Link each single-implementer interface method to its implementation. Purely…, resolve_csharp_interface_dispatch(), _extract()（还有 18 个）

### 社区 143 —— "test_agents_platform.py"
凝聚度：0.10
节点（共 26 个）：parametrize, Tests for the generic `agents` platform and its `skills` alias (#1432).…, `graphify uninstall --platform agents|skills` (global) clears ~/.agents/skills.…, `graphify uninstall --project` (no platform) removes the agents project skill…, `graphify install --project --platform agents` writes ./.agents/skills and…, `graphify agents install` is the amp-twin: skill at ~/.agents/skills PLUS a `##…, Running `graphify agents install` twice leaves a single AGENTS.md section., `graphify skills install`/`uninstall` behaves exactly like the agents form:…（还有 18 个）

### 社区 144 —— "_fixture"
凝聚度：0.21
节点（共 27 个）：cache_root(), tmp_file(), Ensure custom extractors registered in a test don't leak to others., _restore_registry(), _fixture(), _invoke(), _is_deny(), Strict-mode hook-guard: opt-in block-then-nudge + #1840 gating. The strict…（还有 19 个）

### 社区 145 —— "test_hook_guard.py"
凝聚度：0.15
节点（共 27 个）：_cli(), _env(), _invoke(), parametrize, Rigorous edge-case coverage for the `graphify hook-guard` subcommand (#522).…, test_dispatch_always_exits_zero(), test_dispatch_missing_mode_exits_zero_silent(), test_dispatch_unknown_mode_exits_zero_silent()（还有 19 个）

### 社区 146 —— "test_read_hook.py"
凝聚度：0.12
节点（共 27 个）：_env(), The Read|Glob PreToolUse guard nudges toward the graph instead of raw reads.…, Config files must stay silent: '.json' must not match the '.js' extension., A real trailing extension must win on multi-dot names (the segment split):…, Backslash-separated paths split on the real final segment, then its ext., An extension that sits on a directory component, not the final segment, must…, A nudge is additionalContext only - the guard must exit 0, never deny., Reading the graph's own report must not start a go-read-the-graph loop.（还有 19 个）

### 社区 147 —— "_make_symbol_doc"
凝聚度：0.07
节点（共 28 个）：_make_symbol_doc(), Helper to build a minimal SCIP document with one symbol., is_reference → relation 'scip_ref'., is_definition → relation 'scip_def'., is_implementation → relation 'scip_impl' (takes priority over is_definition)., is_type_definition → relation 'scip_typed'., Implementation > TypeDefinition > Definition > Reference., When none of is_* flags are set, relation defaults to 'scip_ref'.（还有 20 个）

### 社区 148 —— "test_swift_cross_file_calls.py"
凝聚度：0.22
节点（共 27 个）：_edge_labels(), _extension_fixture(), _issue_fixture(), _label(), Path, #1604: `let x = Type.shared` cached into a local var, then `x.method()` on a…, A singleton, a caller, and a cross-file `extension` of that singleton., Return {(source_label, relation, target_label)} for the given relations.（还有 19 个）

### 社区 149 —— "to_wiki"
凝聚度：0.08
节点（共 47 个）：Path, Generate a Wikipedia-style wiki from the graph. Writes: - index.md — agent…, to_wiki(), _make_graph(), Tests for graphify.wiki — Wikipedia-style article generation., Each incident edge is counted exactly ONCE (#2633). The Parsing Layer (n1, n2)…, On a MultiGraph each parallel edge is its own row in the split (#2633).…, God node with bad ID should not crash.（还有 39 个）

### 社区 150 —— "sample.swift"
凝聚度：0.09
节点（共 17 个）：Bool, Foundation, CacheManager, createProcessor(), NetworkError, connectionFailed, failed, timeout（还有 9 个）

### 社区 151 —— "graphify 数据建模"
凝聚度：0.18
节点（共 11 个）：1.1 通用字段, 1.2 `file_type` 封闭枚举（6 值）, 1.3 `node_kind` 常见值, 1.4 节点 ID 规约, 1. 节点模型, 5.1 ghost-merge（build.py）, 5.2 deduplicate_entities（dedup.py）, 5.3 _doc_twin_remap（build.py）（还有 3 个）

### 社区 152 —— "test_indirect_dispatch_getattr.py"
凝聚度：0.38
节点（共 11 个）：_extract(), _ind(), Reflective dispatch via getattr string literals — #1566 slice 3. ``getattr(obj,…, test_dynamic_getattr_names_emit_nothing(), test_getattr_feeds_affected(), test_getattr_non_callable_name_emits_nothing(), test_getattr_string_literal_emits_indirect_call(), test_getattr_string_not_shadowed_by_param()（还有 3 个）

### 社区 153 —— "dedup.py"
凝聚度：0.06
节点（共 39 个）：_content_token_swap(), _crossfile_fileanchored_blocked(), _is_code(), _is_variant_pair(), _llm_tiebreak(), _make_minhash(), _merge_missing_attributes(), _numeric_tokens_differ()（还有 31 个）

### 社区 154 —— "test_vue_extraction.py"
凝聚度：0.16
节点（共 24 个）：extract_vue(), Extract imports, symbols, and type refs from a ``.vue`` SFC. Masks the…, _parse_js_tree(), Blank everything outside ``<script>`` bodies, keeping ``\\r``/``\\n``. Replaces…, _vue_mask_non_script(), Path, Tests for ``.vue`` SFC extraction. Feeding a whole SFC to the JS grammar…, Vue allows a classic ``<script>`` plus ``<script setup>``; both are TS.（还有 16 个）

### 社区 155 —— "ddd.py"
凝聚度：0.06
节点（共 59 个）：_basename_without_ext(), _build_code_indices(), _clean_anchor(), _ddd_category_from_path(), extract_ddd(), _infer_ddd_type(), _is_class_node(), _is_file_node()（还有 51 个）

### 社区 156 —— "ExtractionResult"
凝聚度：0.12
节点（共 6 个）：ExtractionResult, 声明式返回：外部解析器产出的节点/边 + 合并策略。 merge_mode: "merge" — 外部 + 默认 extract_markdown 合并（保留…, Handler functions should match in the Impl class's source_file., TestCodeIndexMatching, TestOpenAPI3Extraction, TestSwagger2Extraction

### 社区 157 —— "scip_ingest.py"
凝聚度：0.11
节点（共 26 个）：_build_scip_metadata(), _coerce_str(), _emit_relationships(), _emit_symbol_node(), _first_occurrence_line(), _is_true(), Any, scip_ingest.py — SCIP JSON ingestion (simplified subset). Reads a simplified…（还有 18 个）

### 社区 158 —— "What You Must Do When Invoked"
凝聚度：0.07
节点（共 26 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 18 个）

### 社区 159 —— "DataProcessor"
凝聚度：0.09
节点（共 13 个）：java.util.List, Override, ErrorCode, GAME_DONE, OK, ExtendedService, HttpClient, BaseProcessor（还有 5 个）

### 社区 160 —— "What You Must Do When Invoked"
凝聚度：0.07
节点（共 26 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 18 个）

### 社区 161 —— "introspect_cargo"
凝聚度：0.15
节点（共 24 个）：introspect_cargo(), _load_toml(), _member_manifest_paths(), Any, Path, Cargo manifest introspection for workspace-internal crate dependencies., Return crate nodes and internal dependency edges from Cargo manifests., Real workspace: pin raw graph fields while excluding registry-only deps.（还有 16 个）

### 社区 162 —— "test_prs.py"
凝聚度：0.17
节点（共 9 个）：fetch_worktrees(), format_prs_text(), Plain-text PR summary for MCP output (no ANSI)., Returns {branch: worktree_path}., datetime, Tests for graphify/prs.py., A detached HEAD (no branch line) must not associate its path with the next…, TestFetchWorktrees（还有 1 个）

### 社区 163 —— "detect.py"
凝聚度：0.03
节点（共 133 个）：_auto_follow_symlinks(), count_words(), detect_incremental(), docx_to_markdown(), extract_pdf_text(), _file_within_size_cap(), _find_vcs_root(), _generic_keyword_hit()（还有 125 个）

### 社区 164 —— "file_hash"
凝聚度：0.07
节点（共 34 个）：file_hash(), SHA256 of file contents + path relative to root. Uses a stat-based fastpath…, A .md file with no frontmatter is hashed by its full content., Non-.md files are still hashed by their full content., cached_files reports deep-namespace entries too., A same-length edit must change the digest even when the filesystem reports an…, The guard must not disable the cache: once a file's mtime tick has closed, the…, Editing content above a mid-document ``----`` break must change the hash --…（还有 26 个）

### 社区 165 —— "swagger.py"
凝聚度：0.09
节点（共 25 个）：_basename_without_ext(), _compose_line_map(), _detect_version(), _extract_base_path(), _extract_examples(), _extract_responses(), _has_request_body(), _is_class_node()（还有 17 个）

### 社区 166 —— "multigraph_compat.py"
凝聚度：0.15
节点（共 20 个）：_build_probe_graph(), CapabilityCheck, _check(), MultigraphCapabilityResult, _probe_duplicate_key_overwrite_semantics(), _probe_keyed_parallel_edges(), probe_multigraph_capabilities(), _probe_node_link_round_trip()（还有 12 个）

### 社区 167 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 25 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Kilo-specific rules（还有 17 个）

### 社区 168 —— "_corpus"
凝聚度：0.10
节点（共 26 个）：_assert_no_dangling(), _corpus(), _nodes_with_label(), Run the full extract() pipeline on fixture files (absolute, resolved paths so…, Foo.h (class) + Foo.cpp (Foo::bar def) + Main.cpp must yield exactly ONE Foo…, `void bar();` in Foo.h and `void Foo::bar() {}` in Foo.cpp must collapse to ONE…, The decl/def merge keeps the header node, so `source_file` names the…, A symbol that was never merged must not grow the new attributes — they mark a…（还有 18 个）

### 社区 169 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 25 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Kilo-specific rules（还有 17 个）

### 社区 170 —— "test_stat_index_portability.py"
凝聚度：0.17
节点（共 24 个）：_flush_stat_index(), _count_read_bytes(), _fail_compute(), Path, #2199 — stat-index.json must be portable and self-pruning. The on-disk stat…, A pre-#2199 index keyed by absolute paths still resolves to the right digest on…, When an old absolute key and a new relative key resolve to the same file, the…, #2197: an item whose source_file is absolute is persisted root-relative posix,…（还有 16 个）

### 社区 171 —— "reverse-engineering-ddd"
凝聚度：0.07
节点（共 28 个）：BC 级产物清单（解释性，按需加载）, --help 模式, Phase 1：业务约束（DDD）, Phase 2：技术约束, Phase 3：闭环, reverse-engineering-ddd, 与 Diátaxis 的对应, 临时文件与闭环删除（还有 20 个）

### 社区 172 —— "extract_dm"
凝聚度：0.17
节点（共 20 个）：extract_dm(), Extract types, procs, includes, and calls from a .dm/.dme file., _needs_dm, _calls(), test_cl_emits_calls(), test_cuda_host_call_edges(), test_dm_ambiguous_member_call_left_unresolved(), test_dm_call_edges_have_call_context()（还有 12 个）

### 社区 173 —— "google_workspace.py"
凝聚度：0.14
节点（共 23 个）：convert_google_workspace_file(), _extract_file_id_from_url(), _extract_resource_key(), google_workspace_enabled(), Any, Path, Optional Google Workspace shortcut export support. Google Drive for desktop…, Export a Google Workspace shortcut to a Markdown sidecar. Returns the converted…（还有 15 个）

### 社区 174 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 175 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 176 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 177 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 178 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 179 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 180 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 181 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 182 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 183 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 184 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 185 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 186 —— "test_extract_code_only_cli.py"
凝聚度：0.14
节点（共 24 个）：_mixed_repo(), Path, `graphify extract --code-only` indexes code without an LLM key (#1734). A mixed…, #1971 persistence: once --no-gitignore is set, a later flag-less `graphify…, #2106 traceability: a file dropped by the sensitive-file filter is reported by…, #2923 regression: --code-only --force must not drop the existing semantic…, #2923 follow-up: --code-only --force preserves surviving semantic nodes but…, #2071: --code-only must be discoverable in the extract usage text, not only by…（还有 16 个）

### 社区 187 —— "test_incremental.py"
凝聚度：0.13
节点（共 24 个）：_edges(), _make_docs_corpus(), CompletedProcess, Path, Integration tests for incremental graphify extract behavior., #2169: an incremental --no-cluster extract of ONE changed file must merge into…, #2169: an incremental --code-only --no-cluster run over a mixed corpus must…, #2213 (defect 1, shared root with #2211): a Python relative import's…（还有 16 个）

### 社区 188 —— "test_jsconfig_baseurl.py"
凝聚度：0.22
节点（共 24 个）：_cid(), Path, _rails_tree(), Regression tests: jsconfig.json / baseUrl module resolution (#2153).…, Editing `paths` mid-session must retarget the alias, not keep the old map., Same contract for the separately cached `baseUrl` root (#2153)., A webpacker-shaped project: config at the root, modules under baseUrl., Canonical root-relative file-node id of a cross-file import target (#2169).（还有 16 个）

### 社区 189 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 190 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 191 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 192 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 193 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 194 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 195 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 196 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 197 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 198 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 199 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 200 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 24 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files（还有 16 个）

### 社区 201 —— "test_multilang.py"
凝聚度：0.05
节点（共 63 个）：extract_rust(), Path, Extract functions, structs, enums, traits, impl methods, and use declarations…, _call_pairs(), _confidences(), _edge_labels(), _edges_with_relation(), _labels()（还有 55 个）

### 社区 202 —— "_relations"
凝聚度：0.06
节点（共 36 个）：extract_php(), Extract classes, functions, methods, namespace uses, and calls from a .php file., extract_sln(), Path, Extract projects and inter-project dependencies from a .sln file., Solution folders are virtual groupings, not files. Their node ids must be…, test_sln_contains_edges(), test_sln_solution_folder_ids_are_relative()（还有 28 个）

### 社区 203 —— "test_python_import_resolution.py"
凝聚度：0.56
节点（共 9 个）：_has_edge(), _node_id(), Path, test_ordinary_relative_import_still_resolves(), test_overdeep_relative_import_is_unresolved_not_fatal(), test_python_package_reexport_resolves_import_and_call_to_origin_symbol(), test_python_parameter_return_and_generic_contexts(), test_relative_subpackage_import_from_targets_package_init()（还有 1 个）

### 社区 204 —— "graphify/build.py"
凝聚度：0.04
节点（共 81 个）：_abs_identity(), _build_prune_sets(), deduplicate_by_label(), _derive_prune_root(), _disambiguate_file_node_labels(), _file_label_reassignments(), graph_has_legacy_ids(), _has_global_id()（还有 73 个）

### 社区 205 —— "test_community_labels_skill.py"
凝聚度：0.20
节点（共 15 个）：_code_blocks(), parametrize, Path, Curated community labels must reach the persisted graph.json (#2490). Two…, Same lint at the source of truth: the core fragments skillgen renders from., Passing community_labels stamps community_name on that community's nodes., Omitting the kwarg is the #2490 bug shape: no node carries community_name., Fenced code blocks of a markdown body, fence lines excluded.（还有 7 个）

### 社区 206 —— "test_swagger_e2e.py"
凝聚度：0.06
节点（共 13 个）：edges(), endpoint_nodes(), graph(), nodes(), Any, E2E tests for the Swagger/OpenAPI YAML extractor on the user-management…, Load the CLI-generated graph.json once for the whole test module., swagger_doc_node()（还有 5 个）

### 社区 207 —— "test_js_dynamic_imports.py"
凝聚度：0.20
节点（共 23 个）：_edges_to(), Path, `import('…')` in plain .ts/.js must produce exactly one edge per fact (#2575).…, At module scope `caller_nid` IS the file node, so the rescue is genuinely…, The rescue pass must not disturb the AST pass it runs beside., A backtick specifier with no `${` is as static as a quoted one — the AST path…, `fooimport('./x')` is a call to `fooimport`, not a dynamic import., ordinary calls inside a nested named function attribute to that inner function…（还有 15 个）

### 社区 208 —— "test_kotlin_grammar.py"
凝聚度：0.25
节点（共 23 个）：_edges(), _extract(), _find(), Kotlin grammar-node-type mismatches (#2526, #2550, #2551). PyPI tree-sitter-…, Golden guard: ordinary multi-line Kotlin produces the same nodes/edges as…, test_kotlin_aliased_import_resolves_to_original_symbol(), test_kotlin_class_property_initializer_calls(), test_kotlin_companion_property_initializer_attributes_to_class()（还有 15 个）

### 社区 209 —— "test_prune_sweeps_orphans.py"
凝聚度：0.17
节点（共 23 个）：_corpus_graph(), _extraction(), _prune(), Pruning a source file must not leave its external-import nodes behind.…, Scoped to what this prune orphans. A source-less node that was already isolated…, Only source-less nodes are swept. A node with a real source_file is prunable…, The sweep lives inside the prune branch; a plain merge must not touch isolated…, The #479 shrink guard raises on unexplained node loss. Swept orphans are…（还有 15 个）

### 社区 210 —— "What You Must Do When Invoked"
凝聚度：0.08
节点（共 23 个）：For /graphify add and --watch, For /graphify query, For the commit hook and native @@HOOKS_TARGET@@ integration, For --update and --cluster-only, /graphify, Interpreter guard for subcommands, Part A - Structural extraction for code files, Part B - Semantic extraction (parallel subagents)（还有 15 个）

### 社区 211 —— "Specific Issues Found"
凝聚度：0.08
节点（共 23 个）：1. Node/Edge Quality - Score: 6/10, 2. Edge Accuracy - Score: 5/10, 3. Community Quality - Score: 6/10, 4. Surprising Connections - Score: 4/10, 5. God Nodes - Score: 7/10, 6. Overall Usefulness - Score: 6/10, Additional Observations, Corpus size and density（还有 15 个）

### 社区 212 —— "方法论参考"
凝聚度：0.08
节点（共 25 个）：§1 核心方法：模型探索漩涡, §2 提问规则与格式, §3 模糊性处理：STOP vs ASSUME, §5 假设累积与评审门禁, §6 闭环删除协议, §7 持久化防御与自检, §8 反自我合理化, §9 红旗 — STOP（还有 17 个）

### 社区 214 —— "test_hook_out_of_project_paths.py"
凝聚度：0.17
节点（共 22 个）：_is_cwd_relative(), r"""Whether *value* is anchored at the current working directory. The hook's…, _fake_os_name(), _invoke(), _project(), parametrize, skipif, r"""The read hook's out-of-project guard must not treat a rooted-but-driveless…（还有 14 个）

### 社区 215 —— "_class_node"
凝聚度：0.10
节点（共 25 个）：_build_code_indices(), _match_controller(), _match_handler(), Build nameIndex / fileIndex from AST-extracted code nodes. Indexes only…, Match a swagger ``tags`` entry to a controller class in the code index. Returns…, Match a swagger ``operationId`` to a handler function in the code index.…, _class_node(), _function_node()（还有 17 个）

### 社区 216 —— "extract_terraform"
凝聚度：0.19
节点（共 17 个）：extract_terraform(), Path, Extract Terraform/HCL blocks and the references between them via tree-sitter.…, Facade / registry identity guards for the per-language extractor split (#1212).…, _labels(), Path, Tests for the Terraform/HCL extractor (graphify/extract.py, issue #187)., _rel_pairs()（还有 9 个）

### 社区 217 —— "ingest.py"
凝聚度：0.18
节点（共 20 个）：_detect_url_type(), _download_binary(), _fetch_arxiv(), _fetch_html(), _fetch_tweet(), _fetch_webpage(), _html_to_markdown(), ingest()（还有 12 个）

### 社区 218 —— "test_semantic_cleanup.py"
凝聚度：0.19
节点（共 22 个）：Return validation errors for an untrusted semantic extraction fragment. Empty…, validate_semantic_fragment(), Tests for graphify.semantic_cleanup.validate_semantic_fragment (#825)., #1561: an alias-keyed hyperedge must not be rejected for a missing `nodes` list…, An unknown/synonym file_type is NOT a validation failure: build_from_json…, LLM output with file_type='rationale' must pass validation so the cleanup pass…, LLM output with file_type='concept' must pass validation for the same reason., test_validate_accepts_node_ids_keyed_hyperedge()（还有 14 个）

### 社区 219 —— "test_export_control_characters.py"
凝聚度：0.10
节点（共 29 个）：_cap_filename(), _cypher_escape(), _cypher_label(), _obsidian_safe_stem(), Escape a string for safe embedding in a Cypher single-quoted literal. Handles…, Sanitise a value used in identifier position (node label / rel type). Cypher…, Cap a filename stem to ``limit`` UTF-8 bytes so it stays under the 255-byte…, Filename stem for an Obsidian note / canvas card from a node label. Strips…（还有 21 个）

### 社区 220 —— "test_js_dynamic_import_affected.py"
凝聚度：0.19
节点（共 22 个）：_build(), _fid(), _file_edges(), DiGraph, Path, `affected` must traverse a dynamic `import('…')` written inside a function —…, `import * as ns` binds the module, not the function that defers the load., `other` is a sibling export; the edge into `load()` that used to rescue this is…（还有 14 个）

### 社区 221 —— "test_search_hook.py"
凝聚度：0.15
节点（共 22 个）：_env(), The Bash PreToolUse guard nudges toward the graph before grep/find searches.…, The guard resolves the graph via GRAPHIFY_OUT, not a hardcoded path., A Bash tool_input carries `command`; the Grep-shape detection must not fire…, Feed a Grep-tool-shaped payload (pattern/path/glob, no command) to the guard., _run(), _run_grep_tool(), _search_matcher()（还有 14 个）

### 社区 222 —— "client.py"
凝聚度：0.11
节点（共 13 个）：Auth, BasicAuth, BearerAuth, NetRCAuth, Authentication handlers. Auth objects are callables that modify a request…, Load credentials from ~/.netrc based on the request host., Base class for all authentication handlers., Modify the request. May yield to inspect the response.（还有 5 个）

### 社区 223 —— "extract_powershell"
凝聚度：0.08
节点（共 25 个）：extract_powershell(), Path, Extract functions, classes, methods, and using statements from a .ps1 file., A PowerShell enum must be a real definition, and `[Enum]` refs resolve to it.…, Import-Module Foo at top level emits an imports_from edge., Import-Module -Name Bar.psm1 resolves to module stem 'bar'., Dot-source `. ./Shared.psm1` emits an imports_from edge., Dot-source `. .\\Utils.ps1` (backslash path) emits an imports_from edge.（还有 17 个）

### 社区 224 —— "AuthService"
凝聚度：0.09
节点（共 21 个）：检查用户状态, 注册, 用户已挂起, 登录, 签发令牌, 令牌刷新端点, 注册端点, 登录端点（还有 13 个）

### 社区 225 —— "build_community_labels"
凝聚度：0.43
节点（共 3 个）：build_community_labels(), Return {community_id: [top_labels]} extracted from graph node data., TestBuildCommunityLabels

### 社区 226 —— "generate_section_flowchart"
凝聚度：0.12
节点（共 22 个）：generate_overview_graph(), generate_section_flowchart(), mermaid_class_defs(), mermaid_init(), mermaid_section_id(), node_kind(), node_label(), node_mermaid_id()（还有 14 个）

### 社区 227 —— "CsharpNameResolver"
凝聚度：0.16
节点（共 14 个）：_build_csharp_type_def_index(), CsharpNameResolver, _is_cs_file(), _metadata(), Path, C# cross-file resolution. The config-driven C# *extractor* (``extract_csharp``…, Namespace/using/alias-aware C# simple-name resolution. Factored out of…, Return deterministic ``(namespace, name) -> node_id`` C# type definitions.（还有 6 个）

### 社区 228 —— "_extract_sql_or_skip"
凝聚度：0.08
节点（共 25 个）：_extract_sql_or_skip(), #2953: DDL wrapped in BEGIN; ... COMMIT; must emit table nodes., #2577: a name bound by WITH ... AS (...) is scoped to its statement, not a…, ALTER TABLE ... FOREIGN KEY ... REFERENCES produces a references edge., Schema-qualified table names (Schema.Table) are preserved., ALTER TABLE with schema-qualified names produces correct edges., PL/pgSQL bodies make tree-sitter-sql emit ERROR nodes; the functions must still…, A cleanly-parsed LANGUAGE sql function in the same file is emitted once.（还有 17 个）

### 社区 229 —— "test_python_decorators.py"
凝聚度：0.26
节点（共 21 个）：_class_nid(), _deco_edges(), _func_nid(), _method_nid(), Path, Regression tests: Python decorator references (#2154). Applying a Python…, Decorator-reference edge targets emitted from owner_nid., _stem()（还有 13 个）

### 社区 230 —— "generate_section_cards"
凝聚度：0.12
节点（共 21 个）：derive_flow_chain(), edge_score(), generate_section_cards(), node_degree_scores(), node_importance(), preferred_edges(), Counter, Aggregate inter-section edge counts and relation names.（还有 13 个）

### 社区 231 —— "resolve_cross_file_raw_calls"
凝聚度：0.13
节点（共 15 个）：Resolve unqualified raw calls conservatively after all files are known. This…, resolve_cross_file_raw_calls(), Two genuine NON-test defs of the same name: the god-node guard must still hold…, A real cross-file call must resolve to the SRC definition even when a same-…, One src def plus many same-named test stubs: exactly one edge to src., A test file calling save() with both a src def and a test-local def present…, The python cross-file resolver returns [] (not crash) on bad raw_calls., test_resolve_cross_file_raw_calls_call_site_is_test_prefers_test_local()（还有 7 个）

### 社区 232 —— "extract_ocaml"
凝聚度：0.21
节点（共 20 个）：extract_ocaml(), Path, Extract modules, values, functions, types, variant constructors, `open`…, _labels(), Path, Tests for the OCaml extractor (graphify/extractors/ocaml.py)., A qualified call whose qualifier IS a module defined in this file still…, A qualified call `M.f` to an EXTERNAL module (not defined in this file) must…（还有 12 个）

### 社区 233 —— "save_query_result"
凝聚度：0.15
节点（共 20 个）：Save a Q&A result as markdown so it gets extracted into the graph on next…, save_query_result(), Tests for graphify.ingest.save_query_result, An outcome signal is written to both frontmatter (for `reflect`) and an ##…, Backward compatible: a result without an outcome looks exactly as before., test_answer_in_body(), test_correction_in_frontmatter_and_body(), test_file_created()（还有 12 个）

### 社区 234 —— "_score_query"
凝聚度：0.11
节点（共 30 个）：_compute_idf(), _find_node_tiers(), Return match tiers in precedence order: (source_exact, exact, prefix,…, Split text into word tokens, stripping punctuation and diacritics. `_` is a…, IDF weights for query terms, cached in G.graph['_idf_cache']. Common terms like…, Single-pass combined scorer that optionally also records the best seed for each…, _score_query(), _search_tokens()（还有 22 个）

### 社区 235 —— "test_csharp_partial_classes.py"
凝聚度：0.19
节点（共 20 个）：_extract(), _find(), _nodes_labeled(), C# partial classes split across files (#2332). `partial class Foo` declared in…, Nested partial types are excluded: their ids omit the enclosing type name, so…, Map each Widget class node -> set of member-method labels hanging off it., #2411: same fully-qualified name under TWO .csproj projects is two genuinely…, Adding a .csproj must not break the #2332 merge within one project.（还有 12 个）

### 社区 236 —— "_two_community_graph"
凝聚度：0.10
节点（共 21 个）：parametrize, Two disconnected components -> two stable communities, each hub-labelled by its…, #2853: relabeling a large graph must keep a current aggregated HTML., A skipped aggregate must not race with or falsely claim an HTML write., A failed render must not destroy the previous HTML file., An interruption after graph.json advances must remain repairable., A refused write must not erase retry state owned by an earlier run., A completed HTML replacement must remain a successful command.（还有 13 个）

### 社区 237 —— "_write_raw_doc"
凝聚度：0.13
节点（共 21 个）：_overlay_corpus(), _overlay_graph(), Path, Write a memory doc with a controlled date so ordering is deterministic to…, Write a minimal graph.json under ``out`` with the given node dicts., A corpus with: a PREFERRED node (2 useful), a TENTATIVE node (1 useful), a…, reflect with a graph writes .graphify_learning.json next to graph.json with the…, Two reflect runs on identical input + fixed `now` produce a byte-identical…（还有 13 个）

### 社区 238 —— "rsl-siege-manager/manifest.json"
凝聚度：0.10
节点（共 20 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0001_initial_schema.py, hash, mtime, I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\config.py, hash, mtime, I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\__init__.py, hash（还有 12 个）

### 社区 239 —— "test_settings_merge.py"
凝聚度：0.09
节点（共 43 个）：ALL_INSTALLERS, _claude_pretooluse_hooks(), _gemini_hook(), _install_claude_hook(), _install_codeagent_hook(), _install_codebuddy_hook(), _install_codex_hook(), _install_gemini_hook()（还有 35 个）

### 社区 240 —— "index.ts"
凝聚度：0.17
节点（共 12 个）：档案, AuthResult, JwtManager, TokenPayload, AppConfig, buildApp(), defaultConfig, AuthenticatedRequest（还有 4 个）

### 社区 241 —— "convert_office_file"
凝聚度：0.14
节点（共 19 个）：convert_office_file(), Convert a .docx or .xlsx to a markdown sidecar in out_dir. Returns the path of…, The sidecar name must be identical whether the source path arrives in NFC or…, A second conversion of an unchanged source must not rewrite the sidecar, so its…, #2059: the sidecar name must depend on the scan-root-RELATIVE path, not the…, Two same-stem Office files in different subdirs must still get distinct sidecar…, A source outside the scan root (--include, custom layouts) falls back to the…, test_convert_office_file_does_not_rewrite_existing_sidecar()（还有 11 个）

### 社区 242 —— "sanitize_semantic_fragment"
凝聚度：0.10
节点（共 20 个）：Clean up a semantic extraction fragment in-place. Operations: 1. Removes nodes…, sanitize_semantic_fragment(), A node with file_type='rationale' is removed wholesale., Sentence-like rationale node connected via `rationale_for` → attribute on…, F3: a node with file_type='document' (allowed) that is BOTH sentence-like AND…, A short named node with a period (e.g. abbreviation) is NOT sentence-like., F4: hyperedges referencing removed nodes are repaired or dropped., A hyperedge referencing only nodes not present in the fragment is dropped.（还有 12 个）

### 社区 243 —— "test_symbol_resolution.py"
凝聚度：0.06
节点（共 59 个）：existing_edge_pairs(), _file_node_id_for_path(), find_unique_python_symbol(), ImportedSymbol, _module_stem(), parse_python_import_aliases(), Path, Deterministic symbol indexing and conservative cross-file resolution helpers.（还有 51 个）

### 社区 244 —— "UserService"
凝聚度：0.08
节点（共 20 个）：{业务术语名称}, {业务术语名称}, {业务术语名称}, {业务术语名称}, 用户管理服务, Injectable, Module, GET /rest/apppublishservice/v1/app/{id}（还有 12 个）

### 社区 245 —— "1. 业务实现技术"
凝聚度：0.10
节点（共 19 个）：1.1 设计模式, 1.2 算法选择, 1.3 架构模式, 1.4 安全模型, 1. 业务实现技术, 2.1 错误处理, 2.2 日志/可观测性, 2.3 测试规范（还有 11 个）

### 社区 246 —— "test_cpp_objc_cross_file_calls.py"
凝聚度：0.28
节点（共 19 个）：_call_edges(), _label(), Path, Cross-file member-call and include resolution for C++ (#1547) and ObjC (#1556).…, {(source_label, relation, target_label, confidence)} for the given relations., The headline #1547 fix: a paired class no longer islands — Main.cpp's use of…, test_cpp_cross_file_member_call_connects_with_relative_paths(), test_cpp_godnode_guard_ambiguous_and_unknown_receiver()（还有 11 个）

### 社区 247 —— "test_go_builtin_call_targets.py"
凝聚度：0.19
节点（共 19 个）：builtin_shadow_repo(), _edges_between(), _extract_go(), _label(), _nodes_by_file(), Go predeclared functions must not bind to same-named user symbols.…, The guard is a no-op for genuine user symbols. Uses a plain package-level call:…, Same-file binding needs the guard too, not just the cross-file pass.…（还有 11 个）

### 社区 248 —— "test_install_upgrade.py"
凝聚度：0.15
节点（共 19 个）：_assert_no_report_first(), _assert_query_first(), Installer-level regression tests for upgrade-in-place behavior (issue #580).…, The Claude install must also rewrite a stale .claude/settings.json hook payload…, Same upgrade behavior for AGENTS.md (Codex / OpenCode / Aider / Trae)., Same upgrade behavior for GEMINI.md., Same upgrade behavior for .github/copilot-instructions.md (VS Code)., Same upgrade behavior for .cursor/rules/graphify.mdc. The Cursor rule file is…（还有 11 个）

### 社区 249 —— "test_java_type_resolution.py"
凝聚度：0.29
节点（共 19 个）：_label_edges(), _node_by_id(), Path, test_java_ambiguous_implements_disambiguated_by_import(), test_java_ambiguous_reference_disambiguated_by_import(), test_java_builtin_library_types_not_emitted_as_references(), test_java_cross_file_constructor_call_resolves(), test_java_cross_file_implements_resolves_to_real_def()（还有 11 个）

### 社区 250 —— "_run"
凝聚度：0.10
节点（共 20 个）：CompletedProcess, argparse `choices` rejects an unknown outcome before save_query_result runs., --answer-file lets callers pass a long/multiline answer via a file instead of a…, Neither --answer nor --answer-file -> clean argparse error, not a crash., First run with no .graph/memory/ still succeeds and writes a valid doc., With a real graph.json present, reflect auto-detects it and groups lessons…, Through reflect()/CLI with a real graph.json: a cited node that isn't in the…, `reflect --if-stale` skips the rebuild when LESSONS.md is already current, and…（还有 12 个）

### 社区 251 —— "_load_custom_providers"
凝聚度：0.13
节点（共 18 个）：_custom_providers_path(), _load_custom_providers(), A provider whose base_url uses a non-http(s) scheme is skipped on load (F1)., provider_base_url_ok rejects bad schemes and warns on plaintext-http egress…, Custom providers appear after all built-ins in detect_backend() priority., Missing pricing field defaults to zero so estimate_cost doesn't blow up., Built-in provider names are protected from being overridden., Full round-trip: add → list → show → remove via providers.json.（还有 10 个）

### 社区 252 —— "test_watch_manifest_location.py"
凝聚度：0.13
节点（共 18 个）：_corpus(), parametrize, Path, #2316: `graphify update <target>` must write manifest.json into the TARGET's…, The severe half of #2316: it is data loss, not just a misplaced file.…, #777/#1964 portability, broken here by the CWD-derived ``root=``.…, Same CWD-anchoring class as #2316, but it writes wrong data, not a wrong path.…, End of the chain: the point of the manifest is the next incremental run. A…（还有 10 个）

### 社区 253 —— "test_obsidian_unicode_tags.py"
凝聚度：0.22
节点（共 13 个）：_obsidian_tag(), r"""Sanitize a community name for use as an Obsidian tag. Obsidian tags accept…, _graph(), Regression tests for issue #2862: community tags must survive non-ASCII labels,…, One node per community, so each community label reaches exactly one note., Before the fix every non-Latin label collapsed to '_'/'__', so all notes shared…, `.obsidian/graph.json` colour groups were built from the raw label, so on a…, _tags()（还有 5 个）

### 社区 254 —— "技术约束提取参考"
凝聚度：0.09
节点（共 23 个）：§1 方法论：约束 vs 偶然, §2 业务实现技术提取, 3 个提取维度, §3 编码规范提取, §4 合规约束提取, §6 产物写法：Why 主体，How 简写, §7 质量检查, Step 8（技术约束）质量检查（还有 15 个）

### 社区 255 —— "security.py"
凝聚度：0.11
节点（共 16 个）：_build_opener(), _ip_is_blocked(), Resolve *host* once and return (family, validated_ip) for the first address…, HTTPConnection that resolves + validates DNS once, then connects to the exact…, HTTPSConnection variant of _SSRFGuardedHTTPConnection. Connects to the…, urllib handler that routes http:// through _SSRFGuardedHTTPConnection., urllib handler that routes https:// through _SSRFGuardedHTTPSConnection., Return True if *ip* falls in a private/reserved/internal range. Shared by…（还有 8 个）

### 社区 256 —— "SKILL.md"
凝聚度：0.15
节点（共 9 个）：产物真实性审查 subAgent 提示词, 提示词模板, BC 内契约（可选）, C-00X: {操作/承诺名称}, 契约 — {BC 名称}, 跨 BC 契约, 业务事件 — {BC 名称}, 不变式目录（还有 1 个）

### 社区 257 —— "test_cross_extension_reexport_self_cycle.py"
凝聚度：0.23
节点（共 18 个）：_node_id_by_label(), Path, Same-basename cross-extension re-exports must not collapse to a self-cycle…, With three same-basename siblings that all collapse to the base id ``foo``…, Building the byte-identical repo at two different absolute locations must yield…, The hint is emitted only on JS/TS-family edges, and those suffixes bypass the…, _reexport_like_edges(), test_build_drops_persisted_target_file_from_a_pre_fix_graph()（还有 10 个）

### 社区 258 —— "test_csharp_object_creation.py"
凝聚度：0.26
节点（共 18 个）：_extract(), _find(), C# `new Foo(...)` links the constructing method to Foo. The C# config only…, test_ambiguous_type_name_produces_no_edge(), test_argument_position_links_to_constructed_type(), test_cross_file_publisher_reaches_the_message_class(), test_explicitly_declared_local_links_to_constructed_type(), test_generic_construction_names_the_outer_type()（还有 10 个）

### 社区 259 —— "_claude_artifacts"
凝聚度：0.15
节点（共 13 个）：_claude_artifacts(), The default code-corpus run must be fully described inside the core., No reference fragment may duplicate the core build pipeline., Every references/<name>.md the core points at is actually rendered., claude renders exactly the eight on-demand fragments from the design., Decision A: the file_type enum is the full six-value superset., The core must not inline the execution detail of an on-demand reference. The…, test_eight_references_render_for_claude()（还有 5 个）

### 社区 260 —— "test_export_path_length.py"
凝聚度：0.18
节点（共 21 个）：Largest filename stem an exporter may write directly into ``output_dir``.…, stem_filename_budget(), _fake_windows(), _graph(), Regression tests for issue #2655: export filename caps must respect the…, A CJK label at a tight budget: the stem must stay within budget counted in…, Make stem_filename_budget take its Windows branch on any host. abspath becomes…, test_budget_accounts_for_the_caller_reserve()（还有 13 个）

### 社区 261 —— "sample.php"
凝聚度：0.14
节点（共 9 个）：App\Auth\Authenticator, App\Cache\CacheManager, HasName, Loggable, ApiClient, BaseProcessor, DataProcessor, Result（还有 1 个）

### 社区 262 —— "UserControl"
凝聚度：0.14
节点（共 14 个）：Email, RefreshCommand, ObservableObject, RelayCommand, Task, ToolkitViewModel, Email, RefreshCommand（还有 6 个）

### 社区 263 —— "Plan: 提交阶段图谱更新能力补齐"
凝聚度：0.11
节点（共 17 个）：C-Gap-2: markdown 跑过 Tier2 LLM 后被 hook 跳过, C-Gap-3: ddd / 外部解析器需 code_index,hook 不传, Plan: 提交阶段图谱更新能力补齐, 不在范围内的设计决策, 差异点汇总, 执行顺序与依赖, 改动, 改动(方案 A:文档化)（还有 9 个）

### 社区 264 —— "Design: Incremental Updates + Entity Deduplication"
凝聚度：0.11
节点（共 17 个）：Auto-detection, Design: Incremental Updates + Entity Deduplication, Feature 1: Incremental Updates, Feature 2: Entity Deduplication, Files changed, Files changed, Incremental mode changes, Integration point（还有 9 个）

### 社区 265 —— "test_watch.py"
凝聚度：0.01
节点（共 288 个）：dedupe_edges(), dedupe_nodes(), Collapse nodes sharing an ``id``, last-writer-wins on attributes. Mirrors what…, Collapse exact parallel edges by ``(source, target, relation)``, keeping the…, build_embeddings(), Build (or refresh) the embedding vector index after a graph build. This is the…, external_extractor_extensions(), Union of file extensions declared by all registered extractors. Used by…（还有 280 个）

### 社区 266 —— "compute_pr_impact"
凝聚度：0.35
节点（共 4 个）：compute_pr_impact(), Return (communities_touched, nodes_affected) for a set of changed files. Builds…, 3 nodes across 2 communities, 2 distinct source files., TestComputePrImpact

### 社区 267 —— "processor.py"
凝聚度：0.20
节点（共 13 个）：enrich_document(), extract_keywords(), find_cross_references(), normalize_text(), process_and_save(), Processor module - transforms validated documents into enriched records ready…, Lowercase, strip extra whitespace, remove control characters., Pull non-stopword tokens from text, deduplicated.（还有 5 个）

### 社区 268 —— "Graph"
凝聚度：0.21
节点（共 13 个）：HashMap, Self, build_graph(), Graph, GraphEvent, GraphPair, Logger, String（还有 5 个）

### 社区 269 —— "sample.kt"
凝聚度：0.14
节点（共 14 个）：MutableList, ChatType, GROUP, NORMAL, SYSTEM, createClient(), T, BaseProcessor（还有 6 个）

### 社区 270 —— "test_indirect_call_external_import_shadow.py"
凝聚度：0.22
节点（共 17 个）：_extract_js_dir(), An import from outside the corpus must shadow indirect_call resolution.…, A `paths` entry pointing a package at its own installed copy resolves to a real…, The counter-test that bounds the fix: an import of a file INSIDE the corpus is…, Widening the shadow set must not blanket-suppress a file that also happens to…, The precise collision the fix must survive: a name that is BOTH imported…, Reported shape: an icon imported from a UI kit must not become a fabricated…, `import { Search as Find }` binds `Find` in this file, not `Search`. The shadow…（还有 9 个）

### 社区 271 —— "test_semantic_cache_out_root.py"
凝聚度：0.16
节点（共 17 个）：_count_cache_files(), Path, Regression tests for #1990 and #1991. #1990 — `graphify extract --out` saves…, When root=corpus and cache_root=out, source_file resolution must use corpus as…, Passing root=out_root (the old broken behaviour) silently writes 0 entries; the…, When cache_root is omitted, cache files still land under root (unchanged)., Count .json files under a cache dir (recursively, excluding .tmp)., When cache_root differs from root, cache files must land under cache_root.（还有 9 个）

### 社区 272 —— "test_ts_decorators.py"
凝聚度：0.30
节点（共 17 个）：_class_nid(), _has_deco(), _method_nid(), Path, Regression tests: TypeScript/JavaScript decorator references. `@Component`,…, An external decorator (definition absent from the corpus — the common framework…, True if owner_nid references the (cross-file, bare-stub) decorator symbol., test_class_decorator_on_exported_class()（还有 9 个）

### 社区 273 —— "Window"
凝聚度：0.15
节点（共 12 个）：GraphifyDemo, RoutedEventArgs, RootPanel, SaveButton, UserNameBox, Window, UserName, MainWindow（还有 4 个）

### 社区 274 —— "objc.py"
凝聚度：0.17
节点（共 12 个）：_import_c(), _cpp_declarator_name(), Return the bare variable name from a C++ declaration declarator, unwrapping…, _objc_category_base_stem(), _objc_is_category(), _objc_local_var_types(), objc — moved verbatim from graphify/extract.py., Strip an ObjC category/extension suffix from a file stem (``Foo+Cat`` ->…（还有 4 个）

### 社区 275 —— "test_cluster.py"
凝聚度：0.08
节点（共 39 个）：cohesion_score(), community_member_sigs(), label_communities_by_hub(), _partition(), Community detection on NetworkX graphs. Uses Leiden (graspologic) if available,…, Per-community membership fingerprints: ``{cid: sha256(sorted member ids)}``.…, Context manager to suppress stdout/stderr during library calls. graspologic's…, Run community detection. Returns {node_id: community_id}. Tries Leiden…（还有 31 个）

### 社区 276 —— "test_wiki_link_filename_parity.py"
凝聚度：0.21
节点（共 16 个）：Make a label safe for use as a filename across platforms AND as a markdown link…, _safe_filename(), test_wiki_safe_filename_honours_an_explicit_limit(), _assert_every_link_resolves(), parametrize, Regression tests for issue #2597: a wiki link's target must BE the on-disk…, _targets(), test_distinct_labels_collapsing_to_one_slug_stay_distinct()（还有 8 个）

### 社区 277 —— "main"
凝聚度：0.11
节点（共 18 个）：Namespace, The file_type enum is the six-value superset in every rendered artifact., The guard's line scanner flags 4- and 5-value pipe enums, not the superset., On a shallow checkout (no origin/v8) the validators skip with exit 0. CI sets…, test_git_show_validators_skip_cleanly_without_origin_v8(), test_schema_singleton_catches_legacy_enums(), test_schema_singleton_passes_across_all_platforms(), legacy_enum_lines()（还有 10 个）

### 社区 278 —— "validator.py"
凝聚度：0.17
节点（共 16 个）：Processor, handle_enrich(), Re-enrich a document to pick up new cross-references., check_format(), check_required_fields(), normalize_fields(), Exception, Validator module - checks that parsed documents meet schema requirements before…（还有 8 个）

### 社区 279 —— "test_merge_graphs_cli.py"
凝聚度：0.24
节点（共 16 个）：Path, `graphify merge-graphs` tolerates inputs that disagree on graph type (#1606).…, For a FIXED input order, the offset assignment must be deterministic: merging…, _run(), test_distinct_repo_tags_unit(), test_merge_graphs_carries_hyperedges_from_all_inputs(), test_merge_graphs_community_offset_is_byte_reproducible(), test_merge_graphs_hyperedges_dedup_on_shared_prefixed_id()（还有 8 个）

### 社区 280 —— "TestRebuildCodeProcessesSwaggerYaml"
凝聚度：0.24
节点（共 7 个）：Path, When only the .yaml changes (no code), the extractor still fires. code_index…, A non-swagger .yaml (docker-compose) should NOT enter code_files and should NOT…, Verify _rebuild_code (the post-commit hook entry point) now includes .yaml…, Create a minimal project: src/ItemController.ts + docs/api.yaml., The key gap fix: .yaml doc files now enter code_files in _rebuild_code. We…, TestRebuildCodeProcessesSwaggerYaml

### 社区 281 —— "test_typescript_enum_members.py"
凝聚度：0.32
节点（共 16 个）：_extract(), _find(), _labels(), TypeScript enum members get a node and a `case_of` edge, like Java's (#1719).…, test_a_bare_member_becomes_a_node(), test_a_class_property_identifier_is_not_read_as_an_enum_member(), test_a_const_enum_emits_members(), test_a_quoted_member_uses_its_name_not_the_literal()（还有 8 个）

### 社区 282 —— "Graphify Evaluation - Mixed Corpus (2026-04-04)"
凝聚度：0.12
节点（共 16 个）：1. Corpus Detection, 2. AST Extraction (3 Python files), 3. Community Detection, 4. Query Tests (live BFS traversal), 5. Feedback Loop Test (answers filed back into library), 6. Arabic Image OCR (via Claude vision), 7. Issues Found, 8. Scores（还有 8 个）

### 社区 283 —— "Window"
凝聚度：0.14
节点（共 15 个）：MoneyConverter, TaxConverter, Invoice.Tax, Order.Total, User.Name, ModeText, RootPanel, SaveButton（还有 7 个）

### 社区 284 —— "_stale_graph_sources"
凝聚度：0.25
节点（共 15 个）：Source files graph.json still references but the current scan no longer…, _stale_graph_sources(), #2210: incremental extract's graph-layer prune must not evict ALIVE files.…, Fail-closed: an alive in-root file missing from the corpus without provable…, (a) NFD spelling on disk vs NFC spelling in the graph: NOT stale., (b) fail-closed: a legacy bare-basename source_file whose file is alive at…, (c) a source_file with no file on disk anywhere IS pruned., #1909 must keep working: an alive file excluded by ignore rules is provably…（还有 7 个）

### 社区 285 —— "_is_regular_file"
凝聚度：0.20
节点（共 15 个）：_is_regular_file(), True only for regular files (symlinks followed). Named pipes, sockets and…, A repository may contain files that are not regular files. ``clone <github-…, The shape that hangs the whole run., A link to a FIFO blocks exactly like the FIFO, so stat must follow it., test_broken_symlink_is_rejected_without_raising(), test_char_device_is_rejected(), test_directory_named_like_a_source_file_is_rejected()（还有 7 个）

### 社区 286 —— "affected_nodes"
凝聚度：0.15
节点（共 21 个）：affected_nodes(), AffectedHit, _as_repo_relative(), _bare_name(), format_affected(), _format_location(), _node_label(), _normalize_label()（还有 13 个）

### 社区 287 —— "wiki.py"
凝聚度：0.39
节点（共 7 个）：_community_article(), _cross_community_links(), _god_node_article(), _index_md(), _md_link(), Render a link to another wiki article as a portable relative markdown link.…, Return (community_label, edge_count) pairs for cross-community connections,…

### 社区 288 —— "extract_markdown"
凝聚度：0.04
节点（共 56 个）：extract_markdown(), _parse_frontmatter(), _parse_frontmatter_fallback(), Parse frontmatter lines into a plain dict. Values are passed through…, Flat `key: value` parser for when PyYAML is not installed. Nested blocks and…, Extract structural nodes and edges from a Markdown file. Produces nodes for: -…, _md_extract(), _md_link_fixture()（还有 48 个）

### 社区 289 —— "test_indirect_call_nested_closure_shadow.py"
凝聚度：0.22
节点（共 15 个）：_extract_js_dir(), Indirect-call argument shadowing across untracked JS/TS closures (#2241). An…, A const-assigned arrow IS separately tracked (its own caller_nid, own…, Blast-radius traversal must not include a caller that only reached the target…, The fix must hold on a warm-cache re-extraction, not just a cold run — the…, Reported shape (#2241): a one-letter test helper `r` must not become a…, The same nested-arrow shape must still capture a REAL by-name reference that is…, Shadowing must compound through two levels of untracked inline closures: an…（还有 7 个）

### 社区 290 —— "test_inferred_confidence_rubric.py"
凝聚度：0.17
节点（共 13 个）：_extract(), _inferred(), parametrize, Every INFERRED edge the AST extractor emits must carry a rubric score.…, The other half of the rubric must not drift while fixing this one., The fix is scoped to INFERRED; the other two tiers keep their values., 0.8 was the value in the tree and is not on the scale. Catch it and the…, A function passed by name as an argument — the indirect_call path.（还有 5 个）

### 社区 291 —— "test_java_member_calls.py"
凝聚度：0.40
节点（共 15 个）：_calls(), _find(), Path, Java receiver-typed member-call resolution. Java ``method_invocation`` nodes…, test_ambiguous_receiver_type_emits_no_edge(), test_explicit_type_receiver_resolves_to_owned_method(), test_field_receiver_resolves_to_declared_type(), test_inherited_field_and_chained_receiver_are_deferred()（还有 7 个）

### 社区 292 —— "extract_astro"
凝聚度：0.28
节点（共 14 个）：extract_astro(), Extract imports from .astro files: frontmatter (TS) + template regex fallback.…, _import_targets(), Path, Tests for `.astro` extraction (#850). Astro files have a TypeScript frontmatter…, Astro permits frontmatter-less files (pure-HTML pages). Must not raise., Without this, detect.py silently drops `.astro` from the AST pass (#850)., test_astro_is_in_code_extensions()（还有 6 个）

### 社区 293 —— "test_objc_category_interfaces.py"
凝聚度：0.26
节点（共 15 个）：_calls(), _label(), _nodes_labelled(), Path, ObjC category / class-extension interfaces must fold into the base class…, Two unrelated `Thing` classes in different directories must not merge. The id…, {(source_label, target_label, confidence)} over `calls` edges., The headline case: `-useIt` declared in a category still resolves. Before,…（还有 7 个）

### 社区 294 —— "test_objc_property_ivar_receivers.py"
凝聚度：0.33
节点（共 15 个）：_call_edges(), _label(), Path, ObjC property/ivar receivers must type through the class's field table (#1556).…, The no-fabrication decoy: `[Foo.shared doIt]` next to a REAL class FooShared. A…, {(source_label, relation, target_label, confidence)} for the given relations., test_objc_ambiguous_field_type_emits_no_edge(), test_objc_dotted_class_receiver_fabricates_nothing()（还有 7 个）

### 社区 295 —— "Platform"
凝聚度：0.10
节点（共 22 个）：Each monolith is diff-clean vs v8 except the file_type enum unification., test_monolith_roundtrip_passes_for_aider_and_devin(), _is_sanctioned_monolith_diff(), _is_trigger_line(), monolith_roundtrip(), _normalise(), Platform, Whether a single added/removed monolith line is an allowed change.（还有 14 个）

### 社区 296 —— "test_atomic_writes.py"
凝聚度：0.13
节点（共 22 个）：_atomic_replace(), Path, Atomically replace ``path`` with content written by ``write_fn(f)``. Writes a…, Atomically write ``text`` (UTF-8) to ``path``. See :func:`_atomic_replace`., Atomically write ``obj`` as JSON to ``path``, streaming the encode into the…, write_json_atomic(), write_text_atomic(), skipif（还有 14 个）

### 社区 297 —— "sample.json"
凝聚度：0.13
节点（共 14 个）：axios, react, dependencies, axios, react, devDependencies, typescript, typescript（还有 6 个）

### 社区 298 —— "graphify Benchmarks"
凝聚度：0.13
节点（共 14 个）：Cost and token economics, Datasets, Fairness rules, graphify Benchmarks, Harness, Judge and grading, LOCOMO (n=300), LongMemEval-S (n=50)（还有 6 个）

### 社区 299 —— "AccountService"
凝聚度：0.15
节点（共 7 个）：delete, insert, update, AccountService, AccountStatus, Account, Notifiable

### 社区 300 —— "_inline_links"
凝聚度：0.25
节点（共 8 个）：_inline_links(), Yield (display, target) for each inline markdown link, skipping external URLs.…, Labels with spaces, &, #, and parentheses must produce a link whose target IS…, A god node links its neighbours, but only communities and god nodes get article…, When two labels collide on disk and the second article gets a numeric suffix…, test_wiki_links_to_nodes_without_articles_are_plain_text(), test_wiki_links_use_collision_suffixed_slug(), test_wiki_special_characters_in_label_resolve()

### 社区 301 —— "_check_skill_version"
凝聚度：0.22
节点（共 11 个）：_check_skill_version(), Path, Warn if the installed skill is from an older graphify version., Parse a version string into a comparable integer tuple (``0.9.2`` -> ``(0, 9,…, _version_tuple(), _make_skill(), Path, Direction-aware skill-version mismatch warning (#1568). `_check_skill_version`…（还有 3 个）

### 社区 302 —— "TDataProcessor"
凝聚度：0.16
节点（共 7 个）：IProcessor, TObject, SampleUnit, TBaseProcessor, TDataProcessor, Process(), Reset()

### 社区 303 —— "Path"
凝聚度：0.14
节点（共 15 个）：_graph_ids(), _portability_corpus(), Path, allowed_source_files=None must leave the result untouched (same contract as…, A corpus covering every id/path carrier a cache entry can hold. Deliberately…, Node ids + edge endpoint pairs — the granularity #2257 is about. Deliberately…, #2257: extract corpus under root A (populating the cache), copy the tree AND…, A relative ``root`` (what save_semantic_cache forwards) must not be used as an…（还有 7 个）

### 社区 304 —— "test_cross_repo_shared_types.py"
凝聚度：0.28
节点（共 14 个）：_merge(), Path, `merge-graphs` links a type declaration two repos share (#3007). Node ids are…, The join key is namespace+name, deliberately NOT structural. Two repos whose…, _run(), test_a_type_with_no_namespace_is_not_linked(), test_non_type_nodes_are_not_linked(), test_same_name_in_different_namespaces_is_not_linked()（还有 6 个）

### 社区 305 —— "test_csharp_call_site_generic_args.py"
凝聚度：0.20
节点（共 14 个）：_all_refs(), C# generic type arguments at CALL SITES. Properties, returns, and parameters…, A plain call site (no explicit type args) must not regress., End-to-end: the exact two-file repro from #2911 produces all six edges., Extract, returning {(source_label, target_label)} for `references` edges., Extract, returning [(source_label, target_label, context)] for every…, The Microsoft.Extensions.DependencyInjection shape that the issue calls out., _refs()（还有 6 个）

### 社区 306 —— "test_csharp_enum_members.py"
凝聚度：0.32
节点（共 14 个）：_extract(), _find(), _labels(), C# enum members get a node and a `case_of` edge, like Java's (#1719).…, test_a_member_is_not_a_method(), test_a_namespaced_enum_still_emits_members(), test_a_property_and_an_enum_member_sharing_a_name_stay_separate(), test_an_empty_enum_emits_no_members()（还有 6 个）

### 社区 307 —— "test_csharp_field_generic_args.py"
凝聚度：0.21
节点（共 14 个）：C# generic type arguments in FIELD position. The field_declaration handler read…, The non-generic path must be unchanged., Extract, returning {(source_label, target_label)} for `references` edges., A field and a property of the same type must produce the same references., `T item` must not create a node for the type parameter itself., _refs(), test_bare_type_parameter_is_not_fabricated(), test_field_generic_argument_produces_edge()（还有 6 个）

### 社区 308 —— "_env_command_args"
凝聚度：0.50
节点（共 4 个）：_env_command_args(), Re-tokenize an `env -S`/`--split-string` packed command, prepending the operand…, Strip leading env(1) options and var assignments, return the trailing command…, _split_env_s()

### 社区 309 —— "test_src_layout_import_resolution.py"
凝聚度：0.15
节点（共 16 个）：_import_python(), _probe_python_module_candidate(), Resolve one module-path candidate to a .py file (dir+__init__, exact, or with a…, _resolve_python_module_path(), _import_edges(), Path, #2072: Python import resolution must not depend on the scan root. A src-layout…, A dotted-module id claimed by two different files (two src roots with the same…（还有 8 个）

### 社区 310 —— "test_merge_chunks_validation.py"
凝聚度：0.27
节点（共 14 个）：Tests that `graphify merge-chunks` validates untrusted subagent chunk JSON.…, A valid fragment may legitimately contain no entities; it still counts., _run_merge(), test_merge_chunks_accepts_synonym_file_type(), test_merge_chunks_accepts_unicode_id(), test_merge_chunks_accepts_valid_empty_chunk(), test_merge_chunks_fails_closed_on_unmatched_glob(), test_merge_chunks_fails_closed_when_every_chunk_is_invalid()（还有 6 个）

### 社区 311 —— "test_no_dedup_flag.py"
凝聚度：0.27
节点（共 14 个）：_assert_spied(), _capture_dedup(), _corpus(), `graphify extract --no-dedup` (#2881). The incremental merge path hardcoded…, Run the CLI and return its exit code (0 when main() simply returns)., Record the `dedup` kwarg both build entry points are called with. Patching…, Fail loudly if the spy never fired, so no assertion is vacuous., _run()（还有 6 个）

### 社区 312 —— "storage.py"
凝聚度：0.25
节点（共 14 个）：delete_record(), _ensure_storage(), load_index(), load_record(), Storage module - persists documents to disk and maintains the search index. All…, Load the full document index from disk., Persist the index to disk., Write a parsed document to storage. Returns the assigned record ID.（还有 6 个）

### 社区 313 —— "string"
凝聚度：0.21
节点（共 8 个）：double, Get-Data(), Process-Items(), string, Circle, DataProcessor, Shape, void

### 社区 314 —— "clear_cache"
凝聚度：0.22
节点（共 13 个）：clear_cache(), Delete all cache entries (ast/, semantic/, semantic-deep/, and legacy flat…, _count_by_ext(), _format_languages(), main(), Path, Run extraction, return (elapsed_seconds, node_count, edge_count)., Count files by extension.（还有 5 个）

### 社区 315 —— "2. 编码规范"
凝聚度：0.12
节点（共 15 个）：2.1 错误处理, 2.2 日志/可观测性, 2.3 测试规范, 2.4 命名规范, 2. 编码规范, 3.1 依赖与禁止项, 3.2 兼容性约束, 3. 合规约束（还有 7 个）

### 社区 316 —— "sample.sv"
凝聚度：0.18
节点（共 12 个）：leaf, math_pkg, leaf, Payload, BaseProcessor, Config, DataProcessor, build（还有 4 个）

### 社区 317 —— "test_csharp_member_nodes.py"
凝聚度：0.35
节点（共 13 个）：_extract(), _find(), _labels(), C# properties get a node, like C++ data members (#3006). `_CSHARP_CONFIG`…, test_a_backing_field_does_not_take_the_property_node(), test_a_field_alone_makes_no_member_node_but_keeps_its_type_reference(), test_a_generic_parameter_typed_property_still_gets_a_node(), test_a_primitive_property_still_gets_a_node()（还有 5 个）

### 社区 318 —— "test_extract_cache_location.py"
凝聚度：0.24
节点（共 13 个）：_make_corpus(), Path, #1774 — extract() must never write its AST cache into the analyzed source tree.…, The location/anchor split must keep content-hash keys anchored on the corpus…, The stat-index location is chosen once per process via a module global (#1747).…, Fresh-process regression for the stat-index leak specifically: even for a…, A second extract() of the same corpus must hit the CWD cache the first wrote —…, _reset_stat_index()（还有 5 个）

### 社区 319 —— "test_indirect_call_arrow_single_param_shadow.py"
凝聚度：0.25
节点（共 13 个）：_extract_js_dir(), _indirect(), A single unparenthesised arrow parameter must shadow indirect_call args.…, The reported shape: a minified bundle's private `k` must not become a…, Control: the `parameters` path was already correct and must stay correct., `async x => …` is the same node with the same singular field., The parameter is scoped to its arrow: a same-named module callable referenced…, Widening the shadow set must not blanket-suppress inside arrows: an unshadowed…（还有 5 个）

### 社区 320 —— "test_indirect_call_catch_binding_shadow.py"
凝聚度：0.25
节点（共 13 个）：_extract_js_dir(), `catch (e)` bindings must shadow indirect_call args — inside the clause only.…, ES2019 `catch { }` is a real catch_clause with no `parameter` field — the…, Reported shape: a minified bundle's private `k` must not become a fabricated…, `catch ({ cause })` binds through the same field via a pattern — the…, The binding is scoped to the clause: a same-named module callable referenced…, Widening the shadow set must not blanket-suppress indirect_call inside a catch…, _rels()（还有 5 个）

### 社区 321 —— "_vault_extract"
凝聚度：0.14
节点（共 14 个）：Serial extract() anchored at *vault*, returning (node_ids, ref_edges, page-id…, A subfolder note's [[wikilink]] to a root-level doc resolves vault-wide when…, [[folder/name]] from a subfolder matches on the full segment suffix., On a bare-name collision the shallowest match wins — Obsidian resolves a bare…, An existing sibling target keeps lexical resolution — the fallback only fires…, Inline [text](missing.md) links get no vault fallback: a missing relative…, A wikilink typed in NFD finds a file named in NFC (and spaces survive):…, test_markdown_inline_link_keeps_relative_semantics()（还有 6 个）

### 社区 322 —— "test_node_id_canonical.py"
凝聚度：0.27
节点（共 13 个）：_assert_no_slug(), Path, Node-id / edge-endpoint canonicalization: no absolute-path (machine/temp slug)…, #2262: a .tsx component with a JSX-returning nested arrow component defined…, General invariant: extracting a mixed corpus (python module-level dispatch +…, #2231: a module-TOP-LEVEL dispatch table (`HANDLERS = {'a': handle_a}`) records…, #2243 (bash): `source ./b.sh` mints the target from the resolved absolute path.…, _real()（还有 5 个）

### 社区 323 —— "test_ts_namespace.py"
凝聚度：0.30
节点（共 13 个）：_has_node(), _node_label(), Path, Regression tests: TypeScript namespace/module container nodes. `namespace Foo…, The container node must not cost us the members the default recurse reached., The handler is TS-only; plain JS has no namespace syntax to confuse it., test_ambient_string_module_quotes_stripped(), test_module_keyword_is_node()（还有 5 个）

### 社区 324 —— "test_ts_receiver_member_calls.py"
凝聚度：0.25
节点（共 13 个）：_calls(), _cross_file_edges(), TS/JS receiver-typed member calls beyond `this.field` (#1630). The #1316…, Edges (any relation) whose source node lives in src_file and target in tgt_file., test_array_typed_receiver_emits_no_edge(), test_closure_over_typed_param_receiver(), test_genuinely_imported_type_still_resolves_inferred(), test_local_new_binding_receiver()（还有 5 个）

### 社区 325 —— "test_falkordb_integration.py"
凝聚度：0.29
节点（共 7 个）：_connect(), db(), Integration test for push_to_falkordb against a real FalkorDB instance. Runs…, Return a connected FalkorDB client, or skip if none is reachable., MERGE-based push is safe to re-run - counts must not grow., test_push_to_falkordb_creates_expected_graph(), test_push_to_falkordb_is_idempotent()

### 社区 326 —— "Communities"
凝聚度：0.14
节点（共 13 个）：Communities, Community 0 - "Community 0", Community 1 - "Community 1", Community 2 - "Community 2", Community 3 - "Community 3", Community 4 - "Community 4", Community 5 - "Community 5", Corpus Check（还有 5 个）

### 社区 327 —— "raw/models.py"
凝聚度：0.14
节点（共 3 个）：Headers, Core data models: URL, Headers, Cookies, Request, Response. These are the…, URL

### 社区 328 —— "Benchmark: Karpathy Repos + Research Papers"
凝聚度：0.14
节点（共 13 个）：Benchmark: Karpathy Repos + Research Papers, Code-only (AST, no Claude), Communities detected (major), Full corpus (code + papers + images), God nodes (highest degree), Graph quality evaluation, Graph summary, Per-question breakdown (full corpus)（还有 5 个）

### 社区 329 —— "Geometry"
凝聚度：0.21
节点（共 11 个）：Base, Base.Threads, Float64, LinearAlgebra, ParentModule, area(), describe(), Circle（还有 3 个）

### 社区 330 —— "sample.razor"
凝聚度：0.15
节点（共 12 个）：ComponentBase, CounterRecord, DataGrid, ICounterService, Microsoft.AspNetCore.Components, MyApp.Services, NavigationManager, route:/counter（还有 4 个）

### 社区 331 —— "geometry"
凝聚度：0.22
节点（共 11 个）：constants, geometry, double_val(), circle_area(), geometry, main, point, origin()（还有 3 个）

### 社区 332 —— "check_ddd_anchors.py"
凝聚度：0.22
节点（共 14 个）：check_file(), find_tables(), is_separator_line(), main(), parse_table_header(), parse_table_rows(), 判断是否为表格分隔行（如 |---|---|）, 解析表格数据行，返回 [[cell1, cell2, ...], ...]（还有 6 个）

### 社区 333 —— "sample.go"
凝聚度：0.26
节点（共 9 个）：BaseProcessor, DataProcessor, Logger, Reader, ReaderLogger, Result, Server, main()（还有 1 个）

### 社区 334 —— "Embedding 配置指南"
凝聚度：0.12
节点（共 15 个）：build-time 生成 sidecar, CLI flag（可选覆盖）, Embedding 配置指南, `openai-compatible` backend（推荐用于自托管端点）, query-time 自动加载, sentence-transformers（仅测试/CI）, 三种部署模式, 初始化行为（还有 7 个）

### 社区 335 —— "DataProcessor"
凝聚度：0.27
节点（共 8 个）：List, HttpClient, DataProcessor, Owner, Workers, IProcessor, Processor, Result

### 社区 336 —— "Animal"
凝聚度：0.21
节点（共 12 个）：NSObject, NSString, SampleDelegate, Animal, -initWithName, -speak, <Base>, -baseMethod（还有 4 个）

### 社区 337 —— "sample.dmf"
凝聚度：0.15
节点（共 12 个）：elem "info" [CHILD], elem "infowindow" [MAIN], elem "map" [MAP], elem "mapwindow" [MAIN], elem "output" [OUTPUT], elem "outputwindow" [MAIN], elem "stat" [INFO], elem "statwindow" [MAIN]（还有 4 个）

### 社区 338 —— "ScopedCallsUnit"
凝聚度：0.23
节点（共 12 个）：TObject, ScopedCallsUnit, TBaseWidget, Prepare(), TDerivedWidget, Run(), TFirstWidget, Configure()（还有 4 个）

### 社区 339 —— "test_extraction_spec_ids.py"
凝聚度：0.24
节点（共 12 个）：_ast_symbol_id(), _examples(), parametrize, Path, Drift guard for the node-ID spec shown to LLM semantic subagents.…, Reproduce the symbol ID the AST extractor emits for a file + symbol, using the…, Guard the guard: if the spec moves or the example format changes so nothing…, The canonical spec warns against the filename-only and full-path ID forms. Lock…（还有 4 个）

### 社区 340 —— "test_objc_member_calls.py"
凝聚度：0.28
节点（共 12 个）：_edges(), _label(), Path, ObjC receiver typing must not treat a ``@protocol`` as a message receiver…, {(source_label, target_label, confidence)} for edges of one relation., No class named Reload exists, so `[Reload reload]` is untypable -> ZERO edges.…, A protocol and a class may share a name; the class must still resolve.…, The exclusion is scoped to receiver typing: adoption edges are unaffected.（还有 4 个）

### 社区 341 —— "test_ts_inheritance.py"
凝聚度：0.35
节点（共 12 个）：_has_inherits(), Path, Regression tests for issue #1095: TypeScript inheritance capture. Two gaps on…, Regression guard: the originally-working imported-class case must stay., test_class_extends_same_file(), test_class_implements_same_file_interface(), test_imported_class_extends_still_works(), test_interface_extends_generic_base_same_file()（还有 4 个）

### 社区 342 —— "Graph Report - worked/mixed-corpus/raw  (2026-04-05)"
凝聚度：0.15
节点（共 12 个）：Communities, Community 0 - "Community 0", Community 1 - "Community 1", Community 2 - "Community 2", Community 3 - "Community 3", Community 4 - "Community 4", Corpus Check, God Nodes (most connected - your core abstractions)（还有 4 个）

### 社区 343 —— "test_query_cli.py"
凝聚度：0.22
节点（共 12 个）：Tests for graphify query CLI context filtering., #F4: query CLI must refuse to parse a graph.json that exceeds the cap., A single directed `calls` edge on an (on-disk) undirected graph.json, the…, `graphify query` must render `calls` edges caller->callee regardless of which…, Same edge, seeded from the caller side — must stay correct too., test_query_cli_explicit_context_filter(), test_query_cli_heuristic_context_filter(), test_query_cli_preserves_calls_direction_when_seeded_on_callee()（还有 4 个）

### 社区 344 —— "attach_graph_impact"
凝聚度：0.18
节点（共 8 个）：attach_graph_impact(), fetch_pr_files(), _load_graph_json(), Path, Fetch PR file lists concurrently, compute graph impact, return community labels., prs.py reads gh/git/claude output via subprocess.run(text=True). Without an…, Guard: the fixture's UTF-8 bytes must be undecodable as cp1252, else these…, TestSubprocessOutputEncoding

### 社区 345 —— "_detect_default_branch"
凝聚度：0.24
节点（共 6 个）：_detect_default_branch(), fetch_prs(), _gh(), Auto-detect the repo's default branch via gh, then git, then fall back to…, gh returns data but with no defaultBranchRef — should still fall back., TestDetectDefaultBranch

### 社区 346 —— "test_swift_computed_properties.py"
凝聚度：0.47
节点（共 4 个）：_labels(), Regression tests for #2181. Swift computed properties (`var body: some View { ……, _rel(), TestSwiftComputedProperties

### 社区 347 —— "1. 业务实现技术"
凝聚度：0.13
节点（共 15 个）：1.1 设计模式, 1.2 算法选择, 1.3 架构模式, 1.4 并发模型, 1.5 安全模型, 1.6 高可靠设计, 1.7 trade-off 优先级（可选）, 1. 业务实现技术（还有 7 个）

### 社区 348 —— "compilerOptions"
凝聚度：0.17
节点（共 11 个）：compilerOptions, declaration, esModuleInterop, module, moduleResolution, outDir, skipLibCheck, strict（还有 3 个）

### 社区 349 —— "barrel_reexport.ts"
凝聚度：0.23
节点（共 5 个）：LOCAL_CONST, readCookie(), writeCookie(), basePathRewrite(), getFullUrl()

### 社区 350 —— "test_architecture_doc.py"
凝聚度：0.18
节点（共 11 个）：_documented_symbols(), parametrize, ARCHITECTURE.md's module table must name symbols that actually exist (#2640).…, (module, function) for every function named in the module table., Guard the parser itself: a regex that silently matches nothing would make every…, `extract(path)` was documented for a function whose first parameter is a list;…, The omitted `root=` is the parameter whose absence yields non-canonical ids and…, test_architecture_documents_extract_as_taking_a_list()（还有 3 个）

### 社区 351 —— "Plan: 解析器扩展机制能力补齐"
凝聚度：0.12
节点（共 15 个）：4.1 新建 `graphify/prompt_registry.py`(~120 LOC), 4.2 改 `graphify/llm.py` `extract_files_direct()`(~15 LOC), 4.3 改 `graphify/cli.py` semantic extraction 分组(~40 LOC), 4.4 扩展 `graphify/validate.py`(~30 LOC), 4.5 测试, Gap-1: 解除 Tier 1 扫描范围硬编码, Gap-2: 内置目录自动扫描, Gap-3: 项目级目录 + 优先级（还有 7 个）

### 社区 352 —— "test_install_strings.py"
凝聚度：0.17
节点（共 8 个）：Regression tests for install-time instruction strings. These strings live in…, The fix demotes GRAPH_REPORT.md, it doesn't delete the reference. Most install…, All ten install surfaces must point the assistant at `graphify query` as the…, The pre-fix instructions told assistants to read GRAPH_REPORT.md as their first…, test_every_install_surface_recommends_graphify_query(), test_no_install_surface_demands_reading_the_full_report_first(), test_report_is_still_referenced_as_fallback(), test_skill_registration_uses_host_generic_instruction()

### 社区 353 —— "test_js_callback_calls.py"
凝聚度：0.35
节点（共 11 个）：_extract(), _indirect(), Calls inside a callback passed to a module-level call must not be dropped…, test_callback_body_call_is_not_double_counted(), test_callback_body_calls_are_captured(), test_callback_member_call_is_origin_gated(), test_multi_closure_direct_calls_still_captured(), test_own_closure_local_still_suppresses_indirect_call()（还有 3 个）

### 社区 354 —— "test_scala_self_type.py"
凝聚度：0.38
节点（共 11 个）：_build(), Scala self-type annotations (`self: Logging with Database =>`, `this: T =>`). A…, _rels(), test_affected_includes_self_type_dependents(), test_class_without_self_type_emits_no_requires_edge(), test_requires_edges_carry_no_context(), test_self_type_binder_only_emits_no_requires_edge(), test_self_type_coexists_with_unrelated_extends()（还有 3 个）

### 社区 355 —— "test_ts_generators.py"
凝聚度：0.36
节点（共 11 个）：_contains(), _has_node(), Path, Regression tests: TypeScript/JavaScript generator functions as nodes. Before…, A call inside a generator's body should be attributed to the generator, proving…, test_async_generator_declaration_is_node(), test_generator_body_calls_are_attributed(), test_generator_declaration_is_node_js()（还有 3 个）

### 社区 356 —— "test_typescript_module_extensions.py"
凝聚度：0.26
节点（共 7 个）：_extract(), _labels(), Path, TypeScript module extensions (`.mts` / `.cts`) are treated as code. `.mts`…, test_cts_uses_the_typescript_grammar(), test_mts_uses_the_typescript_grammar(), test_uppercase_typescript_extensions_use_typescript_grammar()

### 社区 357 —— "_plant_skill_tree"
凝聚度：0.21
节点（共 12 个）：_plant_skill_tree(), parametrize, Path, Create <root>/<dot_dir>/skills/graphify/{SKILL.md, references/x.md,…, fn(project_dir) removes only the project skill tree (#2215 trap closed)., fn() with no args keeps the historical CLI behavior: global skill removed., fn(pd, remove_user_skill=True) removes the global skill, leaves the project…, fn(pd, project=True) removes only the project skill tree.（还有 4 个）

### 社区 358 —— "_make_scip_node_id"
凝聚度：0.12
节点（共 16 个）：_make_scip_node_id(), Derive a stable Graphify node ID from a SCIP symbol identifier. Uses SHA-1…, Symbol with # uses suffix after last #., Symbol without # uses the full symbol (sanitised) as suffix., Non-alphanumeric characters are replaced with underscores., Same inputs always produce the same id., Different source_file produces different hash., Different symbol produces different hash.（还有 8 个）

### 社区 359 —— "HTTPStatusError"
凝聚度：0.18
节点（共 9 个）：CookieConflict, HTTPError, HTTPStatusError, InvalidURL, Exception, A 4xx or 5xx response was received., Base class for all httpx exceptions., URL is improperly formed or cannot be parsed.（还有 1 个）

### 社区 360 —— "Case Study: rsl-siege-manager (Python + TypeScript monorepo)"
凝聚度：0.17
节点（共 9 个）：1. Clone the corpus, 2. Install the CLI, 3. Run extraction, 4. Inspect, Case Study: rsl-siege-manager (Python + TypeScript monorepo), How to reproduce, Reference, What's in this directory（还有 1 个）

### 社区 361 —— "Demo.ViewModels"
凝聚度：0.18
节点（共 6 个）：Demo.ViewModels, PrismOrderViewModel, SettingsViewModel, UserControl, SettingsView, UserControl

### 社区 362 —— "RFC: file-level node summaries"
凝聚度：0.18
节点（共 11 个）：Follow-up ideas, Goals, Non-goals, Option A: `summary` attribute in `graph.json`, Option B: sidecar `node-summaries.json`, Problem, Proposed summary contents, Questions for maintainers and users（还有 3 个）

### 社区 363 —— "test_prompt_registry.py"
凝聚度：0.27
节点（共 10 个）：Validate extraction JSON against a prompt spec's ``output_schema``. Runs AFTER…, validate_prompt_schema(), Tests for the Tier 2 prompt registry (Gap-4). Covers: - load_prompts_from_dir:…, validate_prompt_schema should catch issues validate_extraction doesn't., test_validate_prompt_schema_invalid_confidence(), test_validate_prompt_schema_invalid_file_type(), test_validate_prompt_schema_invalid_relation(), test_validate_prompt_schema_none_returns_empty()（还有 2 个）

### 社区 364 —— "extract_swagger"
凝聚度：0.12
节点（共 17 个）：extract_swagger(), _make_doc_node(), Path, Build the per-file swagger document node., Extract REST endpoint nodes + references edges from a swagger/openapi yaml.…, _code_index(), Path, Issue #1 fixture + a mock code_index with APPPublishService class and…（还有 9 个）

### 社区 365 —— "BC 级产物"
凝聚度：0.17
节点（共 11 个）：BC 级产物, business-flow.md — 业务流程, context-map.md — 业务边界图, contracts.md — 业务契约, domain-events.md — 业务事件, domain-model.md — 领域模型, index.md — BC 入口速查, invariants.md — 业务不变式（还有 3 个）

### 社区 366 —— "使用说明（给主 Agent）"
凝聚度：0.17
节点（共 12 个）：Claude Code, OpenCode, 何时派发, 使用说明（给主 Agent）, 其他平台, 如何派发, 审查对象清单, 审查报告 — {产物文件名}（还有 4 个）

### 社区 367 —— "{BC 名称} — 限界上下文索引"
凝聚度：0.17
节点（共 11 个）：API 测试规格（可选）, {BC 名称} — 限界上下文索引, operation → 业务契约映射（可选）, 业务约束, 关键概念, 契约文件清单, 工件链接, 技术契约索引（还有 3 个）

### 社区 368 —— "test_zig_enum_and_union_methods_are_extracted"
凝聚度：0.67
节点（共 3 个）：_needs_zig, Methods declared inside a Zig enum or tagged union must be captured. Only…, test_zig_enum_and_union_methods_are_extracted()

### 社区 369 —— "graphify"
凝聚度：0.20
节点（共 7 个）：graphify, Worked examples, 你会得到什么, 安装, 工作原理, 平台支持, 让助手始终优先使用图谱（推荐）

### 社区 370 —— "llm.py"
凝聚度：0.04
节点（共 58 个）：_anthropic_content(), _azure_client(), _backend_pkg_hint(), _balanced_object(), _bedrock_content(), _bedrock_inference_config(), _call_azure(), _call_bedrock()（还有 50 个）

### 社区 371 —— "parse_memory_doc"
凝聚度：0.18
节点（共 11 个）：parse_memory_doc(), Parse the frontmatter of a memory doc into a dict, or None if it has none.…, Reverse the double-quoted escaping that ingest._yaml_str applies., _yaml_unescape(), parse_memory_doc reads back exactly what save_query_result wrote, including an…, A plain markdown file with no frontmatter is skipped, not crashed on., save -> parse preserves tricky characters in the question, the correction, and…, test_parse_handles_crlf()（还有 3 个）

### 社区 373 —— "_git"
凝聚度：0.13
节点（共 15 个）：_git(), Gitignore rules do not apply to tracked files, matching Git itself (#2759)., A graph-specific exclusion remains authoritative for tracked paths., Tracked paths are repo-relative even when the requested scan root is nested., Watch reconciliation must agree with detect() for tracked paths (#2759)., CLI/persisted excludes are graph-level intent, not Git ignore rules., A missing/broken Git command must not fail open or abort discovery., Optimization (#2759): a git repo with no .gitignore in play must not pay the…（还有 7 个）

### 社区 374 —— "TestCodeAssociationEdges"
凝聚度：0.18
节点（共 4 个）：The POST /users endpoint with operationId=createUser should link to a code node…, The GET /auth/login endpoint with tag=AuthController should link to the…, The POST /auth/register endpoint should link to handleRegister function. The TS…, TestCodeAssociationEdges

### 社区 375 —— "TMainForm"
凝聚度：0.18
节点（共 5 个）：TButton, TPanel, TMainForm, TMemo, TStatusBar

### 社区 376 —— "test_cjs_module_extension.py"
凝聚度：0.22
节点（共 5 个）：_extract(), _labels(), Path, CommonJS module extension (`.cjs`) is treated as code. `.cjs` is the explicit-…, test_cjs_extracts_like_js()

### 社区 377 —— "test_indirect_dispatch_assign_return.py"
凝聚度：0.42
节点（共 10 个）：_extract(), _ind(), Indirect dispatch via assignment + return references — #1566 slice 2. A…, test_assignment_and_return_emit_indirect_call(), test_assignment_feeds_affected(), test_local_shadow_emits_nothing(), test_module_level_assignment_emits_indirect_call(), test_multiple_assignment_emits_for_each()（还有 2 个）

### 社区 378 —— "test_kotlin_object_literal.py"
凝聚度：0.45
节点（共 10 个）：_edges(), _extract(), _find(), Kotlin anonymous-object members (#2347). `object : Foo { ... }` (node type…, Keep-the-bar: named `object` declarations and plain classes extract exactly as…, test_named_object_and_plain_class_unchanged(), test_object_literal_implements_supertype(), test_object_literal_member_calls_sibling_member()（还有 2 个）

### 社区 379 —— "test_partial_extraction_warning.py"
凝聚度：0.31
节点（共 9 个）：_partial_parse_fixture(), The partial-extraction warning must be actionable and must not misdirect. It…, A file the parser ACCEPTS only through ERROR recovery — an unclosed table…, The line number was the one actionable thing the old message had; it must…, _run(), test_a_clean_file_is_silent(), test_warning_carries_no_hardcoded_issue_number(), test_warning_names_the_file_and_how_much_survived()（还有 1 个）

### 社区 380 —— "test_pascal_call_scoping.py"
凝聚度：0.47
节点（共 10 个）：_class_node_id(), _extractors(), _has_call(), _method_node_id(), parametrize, Regression tests for scoped call resolution in the Pascal/Delphi extractor.…, test_calls_do_not_cross_unrelated_classes(), test_calls_resolve_via_ancestor_chain()（还有 2 个）

### 社区 381 —— "test_php_type_resolution.py"
凝聚度：0.53
节点（共 10 个）：_class_defs(), _node_by_id(), Path, test_php_ambiguous_base_disambiguated_by_use(), test_php_external_namespaced_base_does_not_collapse_onto_internal_class(), test_php_fully_qualified_base_resolves(), test_php_import_resolves_when_target_name_prefixes_sibling_classes(), test_php_plain_no_namespace_inheritance_preserved()（还有 2 个）

### 社区 382 —— "test_wheel_packaging.py"
凝聚度：0.25
节点（共 10 个）：_expected_artifacts(), _has_build(), parametrize, Path, Packaging guard (#1121 follow-up): the 5 skillgen guards check the *repo tree*,…, Every distinct skill body a platform installs (the SKILL.md is copied from one…, Every committed skill body + references/*.md (per host) + always_on/*.md block., _skill_bodies()（还有 2 个）

### 社区 383 —— "prompt_registry.py"
凝聚度：0.29
节点（共 6 个）：_glob_match(), _match_globstar(), PromptSpec, Match a relative posix path against a glob pattern. Supports ``**`` (cross-…, Recursive ``**`` matcher: ``**`` matches zero or more path segments., A YAML-declared custom Tier 2 extraction prompt.

### 社区 384 —— "支付"
凝聚度：0.15
节点（共 14 个）：订单, 支付, 库存, 订单, CT-01 订单创建事件, CT-02 订单状态查询, CT-03 订单取消通知, CT-04 支付完成事件（还有 6 个）

### 社区 385 —— "Gap-6: DDD 代码锚点匹配增强(全限定名 + 多匹配 + 置信度标注)"
凝聚度：0.20
节点（共 10 个）：6.1 修改 `_match_code_anchor` 返回所有候选 + 置信度, 6.2 各分支匹配逻辑, 6.3 调用方改造, 6.4 `_resolve_pending_edges` 透传置信度, Gap-6: DDD 代码锚点匹配增强(全限定名 + 多匹配 + 置信度标注), 改动, 测试, 现状（还有 2 个）

### 社区 386 —— "Incremental Updates + Entity Deduplication Implementation Plan"
凝聚度：0.20
节点（共 9 个）：File Map, Incremental Updates + Entity Deduplication Implementation Plan, Self-Review, Task 1: Add `datasketch` and `rapidfuzz` to dependencies, Task 2: Create `graphify/dedup.py` — entropy gate + MinHash/LSH + Jaro-Winkler, Task 3: Wire dedup into `build.py`, Task 4: Incremental updates — semantic cache + manifest in `__main__.py`, Task 5: Add `--dedup-llm` tiebreaker to `dedup.py`（还有 1 个）

### 社区 387 —— "prs.py"
凝聚度：0.24
节点（共 23 个）：default_graph_json(), Default ``graph.json`` path under the configured output dir. The package-wide…, bold(), _c(), _ci_icon(), cmd_prs(), cyan(), dim()（还有 15 个）

### 社区 388 —— "prompt_fingerprint"
凝聚度：0.17
节点（共 12 个）：prompt_fingerprint(), Return a short stable fingerprint of an extraction prompt. ``prompt`` is either…, The fingerprint is stable for identical prompts and differs when the prompt…, A CRLF checkout of the same spec must not look like a prompt change — otherwise…, Fingerprinted entries live under cache/semantic/p{fp}/, never flat., #2927 healing: a legacy on-disk cache entry containing edges but no nodes or…, #1920 / #2927: an existing on-disk cache entry with hyperedges but no nodes…, test_existing_hyperedge_only_cache_entry_remains_hit()（还有 4 个）

### 社区 389 —— "§7 模式识别：聚合协作（Step 6）"
凝聚度：0.22
节点（共 9 个）：§7 模式识别：聚合协作（Step 6）, Step 6 实现指导：共建聚合协作视图, 状态机 — 问业务触发, 聚合协作视图 — 本 skill 的核心产出, 聚合根信号, 聚合边界 — 通过聚合根表和协作视图隐式表达, 行为归属识别（贫血/充血模型）, 识别模式（还有 1 个）

### 社区 390 —— "_is_swagger_spec"
凝聚度：0.31
节点（共 4 个）：_is_swagger_spec(), Any, Heuristic: is this parsed yaml a swagger/openapi spec? Accepts: - ``swagger:…, TestIsSwaggerSpec

### 社区 391 —— "聚合协作视图 — {BC 名称}"
凝聚度：0.22
节点（共 9 个）：1. 聚合根, 2. 领域实体, 3. 值对象, 4. 聚合协作视图, 5. 状态机（可选）, 6. 行为归属与领域服务（可选）, SM-01: {实体/聚合名} 状态机, 聚合协作视图 — {BC 名称}（还有 1 个）

### 社区 392 —— "compilerOptions"
凝聚度：0.20
节点（共 9 个）：@tsconfig/strictest/tsconfig.json, compilerOptions, module, outDir, strict, target, extends, include（还有 1 个）

### 社区 393 —— "package.json"
凝聚度：0.20
节点（共 9 个）：description, devDependencies, typescript, typescript, name, scripts, build, type（还有 1 个）

### 社区 394 —— "api.py"
凝聚度：0.14
节点（共 15 个）：handle_delete(), handle_get(), handle_list(), handle_search(), handle_upload(), API module - exposes the document pipeline over HTTP. Thin layer over parser,…, Accept a list of file paths, run the full pipeline on each, and return a…, Fetch a document by ID and return it.（还有 7 个）

### 社区 396 —— "test_indirect_call_for_of_binding_shadow.py"
凝聚度：0.33
节点（共 9 个）：_extract_js_dir(), _indirect(), A `for...of` / `for...in` loop binding must shadow indirect_call references.…, The reported shape: a `for...of` binding `entry` used in an object-shorthand…, A destructured loop binding (`for (const { entry } of xs)`) must shadow the…, Widening the shadow set must not blanket-suppress: a same-named callable…, test_for_of_binding_does_not_fabricate_indirect_call(), test_for_of_destructuring_binding_shadows()（还有 1 个）

### 社区 397 —— "test_phantom_cross_package_call.py"
凝聚度：0.56
节点（共 9 个）：_calls(), Path, #1659 — a JS/TS call with no local definition and no import must not bind to a…, test_imported_cross_file_call_still_resolves(), test_many_files_do_not_collapse_onto_one_export(), test_non_js_single_candidate_cross_file_still_resolves(), test_same_file_call_unaffected(), test_unimported_cross_package_call_emits_no_edge()（还有 1 个）

### 社区 398 —— "parser.py"
凝聚度：0.23
节点（共 11 个）：parse_and_save(), parse_file(), parse_json(), parse_markdown(), parse_plaintext(), Parser module - reads raw input documents and converts them into a structured…, Read a file from disk and return a structured document., Extract title, sections, and links from markdown.（还有 3 个）

### 社区 399 —— "render_always_on"
凝聚度：0.24
节点（共 10 个）：render_always_on yields exactly the six always-on instruction files., Each always_on/*.md reproduces its former __main__.py constant byte for byte.…, test_always_on_renders_six_blocks(), test_always_on_roundtrip_is_byte_faithful(), _always_on_constants(), always_on_roundtrip(), Parse the always-on string constants out of a __main__.py blob. Reads the…, Assert each always_on/*.md reproduces its former constant byte for byte. The…（还有 2 个）

### 社区 400 —— "test_ts_parse_warning.py"
凝聚度：0.47
节点（共 9 个）：_assert_silent(), _extract(), _labels(), #2610/#2599: the #2551 partial-parse warning must not fire on VALID TS/TSX.…, test_ts_generics_as_and_jsx_logical_and_are_silent(), test_ts_genuinely_broken_file_still_warns(), test_ts_interface_member_named_in_prefix_is_silent(), test_ts_midfile_breakage_warns_and_keeps_intact_functions()（还有 1 个）

### 社区 401 —— "Architecture"
凝聚度：0.22
节点（共 9 个）：Adding a new language extractor, Architecture, Calling `extract()` from your own code, Confidence labels, Extraction output schema, Module responsibilities, Pipeline, Security（还有 1 个）

### 社区 402 —— "Gap-3: 项目级目录 + 优先级"
凝聚度：0.22
节点（共 9 个）：3.1 `registry.py` 加 priority 参数, 3.2 `__init__.py` 加项目级目录扫描, 3.3 目录结构, Gap-3: 项目级目录 + 优先级, 改动, 测试, 现状, 目标（还有 1 个）

### 社区 403 —— "Gap-4: Tier 2 prompt registry"
凝聚度：0.22
节点（共 9 个）：4.1 新建 `graphify/prompt_registry.py`, 4.2 `cli.py` 集成 prompt registry, 4.3 声明文件目录, Gap-4: Tier 2 prompt registry, 改动, 测试, 现状, 目标（还有 1 个）

### 社区 404 —— "_shortest_path_text"
凝聚度：0.24
节点（共 10 个）：_pick_scored_endpoint(), Body of the `shortest_path` MCP tool (module-level so tests can call it without…, Pick a path endpoint from a _score_nodes result, preferring full-token matches.…, _shortest_path_text(), _directed_chain(), DiGraph, alpha --calls--> beta --calls--> gamma, as _load_graph would load it (directed…, test_shortest_path_tool_directed_backwards_is_no_path()（还有 2 个）

### 社区 405 —— "sample.csproj"
凝聚度：0.22
节点（共 6 个）：net8.0, FluentValidation (11.9.0), MediatR (12.2.0), Microsoft.AspNetCore.Authentication.JwtBearer (8.0.0), Swashbuckle.AspNetCore (6.5.0), Microsoft.NET.Sdk.Web

### 社区 406 —— "_replace_or_append_section"
凝聚度：0.33
节点（共 8 个）：Idempotently update or append a graphify-owned section in shared files. If no…, _replace_or_append_section(), #1688 - graphify's shared-file section update must not destroy user content.…, test_append_when_no_real_heading(), test_inline_reference_to_marker_is_not_treated_as_the_section(), test_prefers_last_heading_when_duplicated(), test_real_section_is_replaced_in_place(), test_reinstall_is_idempotent()

### 社区 407 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 408 —— "_collision_rank"
凝聚度：0.10
节点（共 21 个）：_collision_rank(), _defines_id(), _id_prefixes(), _lifecycle_penalty(), Path, _rank_path(), The ID prefixes a node extracted from ``source_file`` may legitimately mint. An…, True when the node's own source_file is the file its ID encodes. A doc that…（还有 13 个）

### 社区 409 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 410 —— "3. 各文件类型的建模方式"
凝聚度：0.25
节点（共 8 个）：3.1 code 文件（.py / .ts / .go / .rs / .java / ...）, 3.2 配置 JSON（package.json / tsconfig.json / composer.json / ...）, 3.3 包清单（pyproject.toml / Cargo.toml / go.mod / pom.xml / apm.yml）, 3.4 markdown 文档（.md / .mdx / .qmd / .rst / .txt）, 3.5 YAML 文件（.yaml / .yml）, 3.6 DDD 文档（context-map / technical-constraints / business-flow / invariants / contracts / domain-events / domain-model）, 3.7 PDF / 图片, 3. 各文件类型的建模方式

### 社区 411 —— "load_all_prompts"
凝聚度：0.20
节点（共 11 个）：load_all_prompts(), load_builtin_prompts(), Path, Scan the built-in ``graphify/prompts/*.yaml`` directory. These ship with the…, Load built-in + project-level prompts, project-level first (priority). Mirrors…, load_all_prompts returns project-level specs before built-in., Built-in prompts dir (graphify/prompts/) is currently empty., Project-level specs are prepended so first-match-wins favours them.（还有 3 个）

### 社区 412 —— "iter_raw_calls"
凝聚度：0.25
节点（共 8 个）：iter_raw_calls(), Return raw calls from all per-file extraction fragments. Parameter is…, A non-dict per_file entry (e.g. junk fragment) must be silently skipped., `raw_calls` that isn't a list must yield empty., Items inside `raw_calls` list that aren't dicts must be dropped., test_iter_raw_calls_drops_non_dict_items_in_list(), test_iter_raw_calls_skips_non_dict_per_file_entries(), test_iter_raw_calls_skips_non_list_raw_calls()

### 社区 413 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 414 —— "_path_match"
凝聚度：0.43
节点（共 3 个）：_path_match(), True if graph_src and pr_file refer to the same file (path-boundary safe)., TestPathMatch

### 社区 415 —— "实现步骤"
凝聚度：0.29
节点（共 7 个）：AGENTS.md 追加协议, Step 0：全局意图对齐, Step 1：建立代码图谱 + 检测项目结构, Step 2-7：业务约束（DDD）, Step 8：技术约束, Step 9：闭环, 实现步骤

### 社区 416 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 417 —— "推断草稿 — {系统名称}"
凝聚度：0.29
节点（共 6 个）：INF-001: {候选语义陈述}, Step {N}: {扫描目标}, 代码信号区, 推断区, 推断草稿 — {系统名称}, 汇总

### 社区 418 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 419 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 420 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 421 —— "tests/conftest.py"
凝聚度：0.22
节点（共 8 个）：_can_symlink(), Any, pytest_collection_modifyitems(), Whether this machine can create symlinks at all (#2642). Probed rather than…, Skip a test that must create symlinks when the platform won't allow it. Take…, Every test gets a throwaway HOME so installers/uninstallers can never touch the…, requires_symlinks(), _sandbox_home()

### 社区 422 —— "dynamic_import.ts"
凝聚度：0.31
节点（共 6 个）：loadStatic(), pollMessages(), processInbound(), ./mayaEngine.js, ./queue.js, ./staticHelper

### 社区 423 —— "Widget"
凝聚度：0.28
节点（共 4 个）：Widget, -refresh, -render, String

### 社区 424 —— "TBaseGadget"
凝聚度：0.28
节点（共 7 个）：BaseGadget, TObject, TBaseGadget, Prepare(), DerivedGadget, TDerivedGadget, Run()

### 社区 425 —— "Config"
凝聚度：0.36
节点（共 7 个）：BaseClient, HttpClientFactory, Int, Loggable, String, Config, HttpClient

### 社区 426 —— "sample_calls.py"
凝聚度：0.39
节点（共 5 个）：Analyzer, compute_score(), normalize(), Fixture: functions and methods that call each other - for call-graph extraction…, run_analysis()

### 社区 427 —— "test_cross_language_call_resolution.py"
凝聚度：0.58
节点（共 8 个）：_call_edges(), Path, Cross-language call resolution — a call in one language must never bind by name…, test_jvm_interop_kotlin_call_to_java_still_resolves(), test_python_call_does_not_bind_to_kotlin_function(), test_same_language_callback_still_resolves(), test_tsx_callback_does_not_bind_to_kotlin_method(), _write()

### 社区 428 —— "test_gemini_hook.py"
凝聚度：0.33
节点（共 7 个）：_env(), The Gemini CLI BeforeTool guard nudges toward the graph, shell-agnostically.…, _run(), test_allows_and_nudges_with_graph(), test_allows_without_nudge_when_no_graph(), test_matcher_and_command_shape(), test_never_blocks()

### 社区 429 —— "test_god_nodes_cli.py"
凝聚度：0.47
节点（共 8 个）：`graphify god-nodes` CLI subcommand (#2004 part 2). god_nodes has long been an…, _run(), test_god_nodes_cli_json(), test_god_nodes_cli_missing_graph_errors(), test_god_nodes_cli_text_output(), test_god_nodes_cli_top_limits(), test_god_nodes_cli_underscore_alias(), _write_graph()

### 社区 430 —— "test_import_self_loops.py"
凝聚度：0.47
节点（共 8 个）：_built_import_self_loops(), _import_self_loops(), parametrize, Path, test_python_external_import_matching_current_basename_has_no_self_loop(), test_recursive_call_self_loop_is_preserved(), test_rust_import_matching_current_basename_has_no_self_loop(), _write()

### 社区 431 —— "_many_communities"
凝聚度：0.25
节点（共 9 个）：_many_communities(), _peak_tracker(), Concurrency must not change the result: same cid->name map either way., ollama/claude-cli must stay serial regardless of --max-concurrency., test_label_communities_accumulates_token_usage(), test_label_communities_batch_size_controls_batch_count(), test_label_communities_forces_serial_for_ollama(), test_label_communities_parallel_matches_sequential()（还有 1 个）

### 社区 432 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 433 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 434 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 435 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 436 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 437 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 438 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 439 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 440 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 441 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 442 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 443 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 444 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 445 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 446 —— "graphify reference: extra exports and benchmark"
凝聚度：0.22
节点（共 8 个）：graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### 社区 447 —— "AsyncHTTPTransport"
凝聚度：0.22
节点（共 4 个）：AsyncBaseTransport, AsyncHTTPTransport, Async transport interface., The async variant of HTTPTransport.

### 社区 448 —— "Graph Report - .  (2026-05-13)"
凝聚度：0.22
节点（共 9 个）：Community Hubs (Navigation), Corpus Check, God Nodes (most connected - your core abstractions), Graph Freshness, Graph Report - .  (2026-05-13), Knowledge Gaps, Suggested Questions, Summary（还有 1 个）

### 社区 449 —— "Review: rsl-siege-manager"
凝聚度：0.22
节点（共 9 个）：Finding 1 — Test fixtures dominate "core abstractions" when tests are included, Finding 2 — Without tests, god nodes mix domain types with entry points and utilities, Finding 3 — Surprising connections cross language boundaries, Finding 4 — Community cohesion is uniformly low on this corpus, Finding 5 — Alembic migration docstrings surface as isolated nodes, Finding 6 — Suggested questions skew toward graph-property prompts, Review: rsl-siege-manager, Suggested follow-ups（还有 1 个）

### 社区 450 —— "saxpy"
凝聚度：0.29
节点（共 7 个）：constant, kernel, dot3(), device, saxpy(), Vec3, uint

### 社区 451 —— "Gap-7: URL 锚点匹配修复(endpoint 节点产出 + 路径规范化)"
凝聚度：0.25
节点（共 8 个）：Gap-7: URL 锚点匹配修复(endpoint 节点产出 + 路径规范化), 改动, 方案 A: 路由解析器产出 endpoint 节点(推荐), 方案 B: 路径规范化 + 前缀匹配(兜底), 测试, 现状, 目标, 验证

### 社区 452 —— "How graphify works"
凝聚度：0.20
节点（共 8 个）：Confidence tagging, How community detection works, How graphify works, Parallel extraction, SHA256 cache, The graph format, The three passes, Token benchmark

### 社区 453 —— "semantic_cleanup.py"
凝聚度：0.25
节点（共 7 个）：_normalize_hyperedge_members(), Canonicalize a hyperedge's member list onto the `nodes` key, in place. If…, _append_rationale_attr(), _is_sentence_like_rationale_label(), Return True if *label* looks like prose / rationale text rather than an entity…, Append one or more rationale strings to *node*'s ``rationale`` attribute. If…, _validate_semantic_id()

### 社区 454 —— "first_present"
凝聚度：0.29
节点（共 8 个）：endpoint_id(), first_present(), normalize_edge(), normalize_node(), Return the first non-empty value for any candidate key., Normalize edge endpoints that may be strings or node-like objects., Normalize a graphify node across common graph.json schema variants., Normalize graphify edges while preserving original fields.

### 社区 455 —— "format_node_refs"
凝聚度：0.25
节点（共 8 个）：format_node_refs(), humanize_label(), node_display_name(), Readable node label for tables and summaries., Render node references as readable labels instead of internal IDs., Truncate without splitting Mermaid syntax., Convert graph labels into short labels people can scan in a diagram., truncate_text()

### 社区 456 —— "safe_file_path"
凝聚度：0.25
节点（共 8 个）：generate_section_intro(), group_nodes_by_file(), is_zh(), Group selected nodes by source file for Mermaid subgraphs., Generate the section introductory paragraph., Return a short, safe display path., Return true when localized strings should be Chinese., safe_file_path()

### 社区 457 —— "{名称}"
凝聚度：0.17
节点（共 12 个）：{名称}, {名称}, {名称}, 持久化失败, 持久化用户, 用户持久化承诺, 用户查询承诺, 邮箱全局唯一（还有 4 个）

### 社区 458 —— "_coerce_hyperedge_member_refs"
凝聚度：0.33
节点（共 6 个）：_coerce_hyperedge_member_refs(), _coerce_id(), _hashable(), Coerce a hyperedge member list to hashable scalar ids, deduped in order.…, Return a str for a numeric id, else the value unchanged. ``bool`` is excluded…, True when value can be a dict key / set member (same probe as the inline ``try:…

### 社区 459 —— "Migrating a language extractor out of extract.py"
凝聚度：0.25
节点（共 7 个）：Helper classification, Invariants (non-negotiable), Migrating a language extractor out of extract.py, Pre-flight, Status, Steps, What NOT to do

### 社区 460 —— "lessons_fresh"
凝聚度：0.25
节点（共 8 个）：lessons_fresh(), True if ``out_path`` exists and is at least as new as every input that feeds it…, parametrize, test_lessons_fresh_false_when_graph_newer(), test_lessons_fresh_false_when_graph_sidecar_newer(), test_lessons_fresh_false_when_memory_newer(), test_lessons_fresh_missing_output_is_not_fresh(), test_lessons_fresh_true_when_output_newer_than_inputs()

### 社区 461 —— "load_memory_docs"
凝聚度：0.25
节点（共 8 个）：load_memory_docs(), Parse every memory doc under ``memory_dir``, sorted by date then filename. Each…, Determinism hinges on this sort: docs come back oldest-first, filename as…, dead_ends/corrections are appended in doc order, so their determinism rides on…, test_dead_ends_and_corrections_follow_doc_order(), test_load_memory_docs_missing_dir_is_empty(), test_load_memory_docs_orders_by_date_then_filename(), test_load_memory_docs_skips_foreign_and_sorts()

### 社区 462 —— "load_validated_semantic_fragment"
凝聚度：0.25
节点（共 8 个）：load_validated_semantic_fragment(), Path, Load and validate a semantic chunk, rejecting oversize files before parsing.…, Invalid JSON returns an error instead of raising., Oversize files are rejected by stat() — payload is never parsed., test_load_validated_semantic_fragment_accepts_valid(), test_load_validated_semantic_fragment_rejects_invalid_json(), test_load_validated_semantic_fragment_rejects_oversize_before_parse()

### 社区 463 —— "§3 模式识别：限界上下文（Step 2）"
凝聚度：0.33
节点（共 6 个）：§3 模式识别：限界上下文（Step 2）, Step 2 实现指导：共建业务边界图, 关系类型 — 问业务性质, 战略分类 — 必须问用户, 目录结构信号, 统一语言 — 从命名提取候选术语

### 社区 464 —— "PasswordHasher"
凝聚度：0.24
节点（共 6 个）：哈希密码, 密码错误, 验证密码, 密码最短8字符, 密码哈希算法, PasswordHasher

### 社区 465 —— "make_pr"
凝聚度：0.38
节点（共 4 个）：_classify(), make_pr(), Build a minimal PRInfo with sensible defaults., TestClassify

### 社区 466 —— "§9 隐形架构决策提取"
凝聚度：0.33
节点（共 6 个）：§9 隐形架构决策提取, 产物写法：规则而非过程, 决策信号的代码定位点, 提问策略, 设计决策不再单独产出, 隐形架构的维度

### 社区 467 —— "gen_demo_path.py"
凝聚度：0.29
节点（共 6 个）：kt(), op0(), pairs of (keyTime, value) -> (values_str, keyTimes_str)., initial opacity for a revealable element (1 when baking a static frame)., opacity reveal at time t (s), hold, fade out before loop., reveal()

### 社区 468 —— "Security Model"
凝聚度：0.25
节点（共 7 个）：Optional network calls, Reporting a Vulnerability, Security Model, Security Policy, Supported Versions, Threat Surface, What graphify does NOT do

### 社区 469 —— "TestDDDDocAnchorNodes"
凝聚度：0.25
节点（共 3 个）：Verify doc-anchor nodes cover all 7 DDD document types., Most expected DDD types appear in tags[1]. Note: _infer_ddd_type maps from the…, TestDDDDocAnchorNodes

### 社区 470 —— "TestCrossFileEdgeResolution"
凝聚度：0.25
节点（共 5 个）：Verify edges between DDD documents resolve via global concept_id index., context-map.md's BC-02 → BC-01 business relationship → conceptually_related_to., TC-001 (适用范围=BC-01) → BC-01; TC-003 (适用范围=BC-02) → BC-02., contracts.md 对端 BC=BC-02 → cites edges to BC-02., TestCrossFileEdgeResolution

### 社区 471 —— "sample.zig"
凝聚度：0.32
节点（共 6 个）：add(), Color, multiply(), main(), Point, Shape

### 社区 473 —— "test_antigravity_install.py"
凝聚度：0.25
节点（共 5 个）：Antigravity install lays down its full always-on layer, not just the skill.…, The workflow must not hardcode a SKILL.md location. One constant serves both…, Global install shares the constant, so it must stay path-free too., test_antigravity_global_install_workflow_names_no_skill_path(), test_antigravity_workflow_names_no_skill_path()

### 社区 474 —— "test_case_sensitive_resolution.py"
凝聚度：0.54
节点（共 7 个）：_extract(), _labels(), Cross-file name resolution respects case in case-sensitive languages (#1581).…, test_case_sensitive_cross_file_ref_respects_case(), test_exact_case_cross_file_still_resolves(), test_php_case_insensitive_resolution_preserved(), test_python_Path_does_not_resolve_to_shell_PATH()

### 社区 475 —— "§4 临时文件 vs 产物：清晰边界"
凝聚度：0.33
节点（共 6 个）：§4 临时文件 vs 产物：清晰边界, 临时文件（`docs/draft/`）—— 中间态，闭环即删, 产物文件 —— 干净态，长期保留, 代码锚点引用决策树, 何时写入产物, 表格标签体系

### 社区 476 —— "test_phantom_external_import.py"
凝聚度：0.39
节点（共 7 个）：Path, #1638 — an unresolved bare npm import must not alias onto an unrelated same-…, test_multiple_tsx_files_do_not_all_alias_onto_one_python_file(), test_no_phantom_edge_from_tsx_to_unrelated_python_file(), test_scoped_package_import_is_ref_namespaced(), test_unresolved_bare_import_is_ref_namespaced(), _write()

### 社区 477 —— "用例: {用例名称}"
凝聚度：0.33
节点（共 6 个）：业务流程 — {BC 名称}, 入口点, 失败/补偿矩阵, 时序图（可选）, 时序编排, 用例: {用例名称}

### 社区 478 —— "test_swift_import_resolution.py"
凝聚度：0.61
节点（共 7 个）：_import_edges(), _module_nodes(), Path, test_swift_import_edges_survive_build(), test_swift_import_resolves_to_module_node(), test_swift_same_module_imported_twice_collapses_to_one_node(), _write()

### 社区 479 —— "DigestAuth"
凝聚度：0.32
节点（共 4 个）：DigestAuth, HTTP Digest Authentication. Requires a full request/response cycle: sends the…, Extract digest parameters from the WWW-Authenticate header., Compute the Authorization header value for a digest challenge.

### 社区 480 —— "Graph Report - /home/safi/graphify-benchmark  (2026-04-04)"
凝聚度：0.25
节点（共 7 个）：Corpus Check, God Nodes (most connected - your core abstractions), Graph Report - /home/safi/graphify-benchmark  (2026-04-04), Knowledge Gaps, Suggested Questions, Summary, Surprising Connections (you probably didn't know these)

### 社区 481 —— "Corpus (52 files)"
凝聚度：0.25
节点（共 7 个）：Code — clone these 3 repos, Corpus (52 files), How to run, Images — save these 4, Karpathy Repos Benchmark, Papers — download these 5 PDFs, What to expect

### 社区 482 —— "Gap-5: 三阶段提取顺序(代码 → 配置文件 → 文档)"
凝聚度：0.29
节点（共 7 个）：Gap-5: 三阶段提取顺序(代码 → 配置文件 → 文档), 为什么这样分, 改动, 测试, 现状, 目标, 验证

### 社区 483 —— "7. 步骤 7：修改 `graphify/serve.py`"
凝聚度：0.29
节点（共 7 个）：7.1 加载 embedding sidecar（在 `_GraphContextCache._load_entry`）, 7.2 修改 `_score_query`（加参数 + 加法 tier）, 7.3 修改 `_query_graph_text`（加参数 + 准备 hybrid scorer + top_n 多结果）, 7.4 修改 MCP `query_graph` schema（加字段）, 7.5 修改 `_tool_query_graph`（透传参数）, 7.6 修改 CLI query 命令（加 `--no-semantic` / `--top-n` flag）, 7. 步骤 7：修改 `graphify/serve.py`

### 社区 484 —— "上下文图 — {系统名称}"
凝聚度：0.33
节点（共 6 个）：1. 限界上下文, 2.1 对外契约文件清单, 2. 业务关系, 3. 统一语言, 4. 领域愿景声明, 上下文图 — {系统名称}

### 社区 485 —— "假设草稿 — {系统名称}"
凝聚度：0.33
节点（共 5 个）：A-001: {模糊点描述}, {BC 名称} — Step {N}, 假设草稿 — {系统名称}, 汇总, 评审记录（Step 9 闭环时填写）

### 社区 486 —— "_make_noisy_graph"
凝聚度：0.33
节点（共 6 个）：_make_noisy_graph(), FooBarService error handling' should expand from FooBarService, not from error-…, 20 error-handler nodes + 1 rare identifier: FooBarService., error' matches 20 nodes, 'foobarservice' matches 1 — IDF should make…, test_idf_downweights_common_terms(), test_query_seeds_from_identifier_not_noise()

### 社区 487 —— "test_maybe_reload_detects_graph_change"
凝聚度：0.33
节点（共 6 个）：Write a minimal graph.json with the given node IDs., serve() picks up a new graph.json written after startup (#874)., mtime_ns + size uniquely identifies a graph version (#874)., test_load_graph_cache_key_changes_with_content(), test_maybe_reload_detects_graph_change(), _write_graph()

### 社区 488 —— "TestTagsField"
凝聚度：0.40
节点（共 3 个）：Verify doc-anchor nodes carry tags usable by serve.py _node_search_text., Code nodes should NOT have tags (only DDD doc-anchor nodes do)., TestTagsField

### 社区 489 —— "_default_model_for_backend"
凝聚度：0.50
节点（共 4 个）：_default_model_for_backend(), Return configured model override or backend default model., Return (backend, model) using GRAPHIFY_TRIAGE_BACKEND or first available key., _resolve_triage_backend()

### 社区 490 —— "§8 模式识别：业务不变式（Step 7）"
凝聚度：0.40
节点（共 5 个）：§8 模式识别：业务不变式（Step 7）, 三类规则的区分, 不变式信号, 不变式分类, 不变式的定位：聚合根对调用者的状态承诺

### 社区 491 —— "提问记录 — {系统名称}"
凝聚度：0.40
节点（共 4 个）：Q-001, 已问记录, 提问记录 — {系统名称}, 提问队列

### 社区 492 —— "4. 检索机制"
凝聚度：0.50
节点（共 4 个）：4.1 检索文本拼接（`_node_search_text`）, 4.2 字符串检索打分层级（`_score_query` / `_find_node`）, 4.3 fuzzy 检索（hybrid_scorer.py + fuzzy.py）, 4. 检索机制

### 社区 493 —— "_community_label_lines"
凝聚度：0.50
节点（共 4 个）：_community_label_lines(), One prompt line per community (largest first), sampling up to ``top_k``…, The prompt line used to read "Community {cid}: ..." — the exact string of the…, test_label_prompt_lines_use_bare_cid_keys()

### 社区 494 —— "上下文图 — User Management System"
凝聚度：0.29
节点（共 6 个）：1. 限界上下文, 2.1 对外契约文件清单, 2. 业务关系, 3. 统一语言, 4. 领域愿景声明, 上下文图 — User Management System

### 社区 495 —— "TestCodeAnchorMatching"
凝聚度：0.29
节点（共 4 个）：Verify DDD code anchors produced references edges to code nodes., TC-001's `User` anchor links to the User class code node., business-flow.md references AuthService.register → should link to AuthService., TestCodeAnchorMatching

### 社区 496 —— "test_security.py"
凝聚度：0.07
节点（共 48 个）：_max_graph_file_bytes(), Any, Return the graph.json size cap in bytes. Honors the…, Strip control characters and cap length. Safe for embedding in JSON data…, Return a control-character-free, HTML-escaped, bounded string., Sanitize a metadata value while preserving simple JSON-compatible types., Sanitize metadata keys and values before graph export. Metadata is less…, sanitize_label()（还有 40 个）

### 社区 497 —— "TestNodeShape"
凝聚度：0.29
节点（共 3 个）：Verify DDD doc-anchor nodes use all-generic fields (no ddd_* prefix)., concept_id is the raw DDD identifier (BC-01, TC-001, etc.)., TestNodeShape

### 社区 498 —— "Foo"
凝聚度：0.33
节点（共 3 个）：Foo, bar, value

### 社区 499 —— "sample_php_listen.php"
凝聚度：0.43
节点（共 6 个）：EventServiceProvider, NotifyAdmins, OrderPlaced, SendWelcomeEmail, ShipOrder, UserRegistered

### 社区 500 —— "test_cpp_preprocess.py"
凝聚度：0.38
节点（共 6 个）：_capture_cpp_argv(), parametrize, The Fortran C-preprocessor path is hardened against argument injection (F5). A…, The guard only does work when the incoming path is RELATIVE. The test above…, test_cpp_preprocess_absolutises_a_relative_attacker_named_file(), test_cpp_preprocess_passes_absolute_path()

### 社区 501 —— "test_crossfile_identical_labels_stay_distinct_for_guarded_types"
凝聚度：0.29
节点（共 7 个）：parametrize, The node whose source_file is the file its ID encodes survives, whichever chunk…, Exact-ID dedup combines AST precision with semantic enrichment (#2091)., The #2182 fix is gated to high-entropy `concept` nodes with provenance on BOTH…, test_crossfile_identical_labels_stay_distinct_for_guarded_types(), test_defining_file_wins_over_referencing_file(), test_same_id_same_entity_retains_complementary_attributes()

### 社区 502 —— "test_home_sandbox.py"
凝聚度：0.29
节点（共 3 个）：Regression tests for the repo-wide HOME sandbox (issue #2168). The autouse…, Global skill deletes land inside the sandbox home, never the real one. Since…, test_global_uninstall_is_captured_by_sandbox()

### 社区 503 —— "Research Notes"
凝聚度：0.29
节点（共 6 个）：On cross-reference detection, On keyword extraction, On storage, On the API layer, Open questions, Research Notes

### 社区 504 —— "Gap-1: 解除 Tier 1 扫描范围硬编码,支持任意文件类型"
凝聚度：0.33
节点（共 6 个）：Gap-1: 解除 Tier 1 扫描范围硬编码,支持任意文件类型, 改动, 测试, 现状, 目标, 验证

### 社区 505 —— "Gap-2: 内置自动扫描目录"
凝聚度：0.33
节点（共 6 个）：Gap-2: 内置自动扫描目录, 改动, 测试, 现状, 目标, 验证

### 社区 506 —— "Plan: 混合语义检索（语义 + fuzzy 重排）"
凝聚度：0.33
节点（共 5 个）：0. 改动总览, 11. 回 upstream 策略, 12. 实施顺序（推荐）, 13. 关键设计决策记录, Plan: 混合语义检索（语义 + fuzzy 重排）

### 社区 507 —— "safe_fetch"
凝聚度：0.21
节点（共 12 个）：Fetch *url* and return raw bytes. Protections applied: - URL scheme validated…, Fetch *url* and return decoded text (UTF-8, replacing bad bytes). Wraps…, safe_fetch(), safe_fetch_text(), _make_mock_response(), test_safe_fetch_raises_on_non_2xx(), test_safe_fetch_raises_on_size_exceeded(), test_safe_fetch_rejects_file_url()（还有 4 个）

### 社区 508 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 509 —— "_inferred_uses"
凝聚度：0.17
节点（共 12 个）：_inferred_uses(), (source, target) pairs of every INFERRED cross-file `uses` edge., A cross-file INFERRED `uses` edge binds to the symbol that actually references…, Positive control: a class that genuinely uses the imported symbol still gets…, `from helpers import Helper as H` attributes via the local alias `H`, so a body…, Each symbol that references the import gets its own edge, and only those…, A reference at true module top level has no enclosing symbol to anchor on, so…, test_inferred_uses_edge_attributes_to_the_referencing_symbol()（还有 4 个）

### 社区 510 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 511 —— ".opencode/opencode.json"
凝聚度：0.50
节点（共 3 个）：.opencode/plugins/graphify.js, plugin, $schema

### 社区 512 —— "user-management/.opencode/opencode.json"
凝聚度：0.50
节点（共 3 个）：.opencode/plugins/graphify.js, plugin, $schema

### 社区 513 —— "日志不变式"
凝聚度：0.18
节点（共 6 个）：日志不变式, Logger, Logger, log, Logger, log

### 社区 514 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 515 —— "_resolve_max_retry_depth"
凝聚度：0.50
节点（共 4 个）：How deep adaptive retry may bisect a truncated chunk. A chunk of N files can…, _resolve_max_retry_depth(), #2880: max_retry_depth was a Python-API kwarg only, so a `graphify extract`…, test_max_retry_depth_reads_the_env_var()

### 社区 517 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 518 —— "CLI 命令（终端里运行）"
凝聚度：0.15
节点（共 13 个）：CLI 命令（终端里运行）, Embedding 配置, Git hooks, Skill 命令（在 AI 编码助手里输入）, 全局图谱, 反馈与学习, 图谱构建与更新, 安装与卸载（还有 5 个）

### 社区 519 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 520 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 521 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 522 —— "sample.c"
凝聚度：0.47
节点（共 5 个）：Rectangle, main(), make_rect(), process(), validate()

### 社区 523 —— "ensure_graph_json"
凝聚度：0.40
节点（共 5 个）：ensure_graph_json(), conftest.py for tests/e2e/ — ensures graph.json is built before tests run. This…, Run graphify extract on the fixture project., Build graph.json once per test session if it doesn't exist. Tests in…, _run_extraction()

### 社区 524 —— "build"
凝聚度：0.67
节点（共 3 个）：build(), build_from_json(), Merge multiple extraction results into one graph.

### 社区 527 —— "Deploy Guide"
凝聚度：0.33
节点（共 5 个）：Database Migration, Deploy Guide, Full Deploy, Prerequisites, Rollback

### 社区 528 —— "sample.sh"
凝聚度：0.53
节点（共 5 个）：APP_ENV, build(), deploy(), sample.sh script, test_suite()

### 社区 529 —— "TSampleForm"
凝聚度：0.33
节点（共 4 个）：TPanel, TLabel, TSampleForm, TTimer

### 社区 530 —— "sample_php_container.php"
凝聚度：0.67
节点（共 4 个）：AppServiceProvider, CashierGateway, PaymentGateway, StripeGateway

### 社区 532 —— "SampleSpec"
凝聚度：0.33
节点（共 4 个）：SampleSpec, "should handle #input and return #expected", "should not change value when it's already correct", "should process valid input"

### 社区 533 —— "test_cli_broken_pipe.py"
凝聚度：0.33
节点（共 5 个）：CLI must not crash when a downstream reader closes the pipe early (#1807).…, `graphify --help | head -n1` must leave graphify exiting 0, not 255., A short, fully-buffered output (piped stdout is block-buffered) only flushes at…, test_help_survives_reader_closing_pipe_early(), test_small_buffered_output_survives_reader_that_reads_nothing()

### 社区 534 —— "test_install_version_stamp.py"
凝聚度：0.33
节点（共 5 个）：Regression test for #2694 (version-stamp half). `graphify install --platform X`…, Installing one platform must leave a different, already-installed platform's…, End-to-end (#2694): after installing one platform, a different stale platform…, test_install_does_not_bump_other_platforms_stamp(), test_stale_untouched_platform_still_emits_warning()

### 社区 535 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 536 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 537 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 538 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 539 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 540 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 541 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 542 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 543 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 544 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 545 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 546 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 547 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 548 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 549 —— "graphify reference: query, path, explain"
凝聚度：0.33
节点（共 5 个）：For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### 社区 550 —— "Document Pipeline Architecture"
凝聚度：0.33
节点（共 5 个）：Design decisions, Document Pipeline Architecture, Extending the pipeline, How data flows, Module responsibilities

### 社区 551 —— "Reproducible Example"
凝聚度：0.33
节点（共 5 个）：After it runs, How to run, Input files, Reproducible Example, What to expect

### 社区 552 —— "E2E 测试体系（双重保障）"
凝聚度：0.40
节点（共 5 个）：conftest.py force-rebuild 支持, E2E 新增/修改测试类, E2E 测试体系（双重保障）, E2E 验证命令, Fixture 数据补充

### 社区 553 —— "3. 步骤 3：修改 `graphify/extractors/engine.py`（desc 字段提取）"
凝聚度：0.40
节点（共 5 个）：3.1 职责, 3.2 改动点, 3.3 影响面控制, 3.4 LOC 估算：~40 LOC（改动）+ 依赖步骤 1 的 desc.py, 3. 步骤 3：修改 `graphify/extractors/engine.py`（desc 字段提取）

### 社区 554 —— "9. 步骤 9：测试"
凝聚度：0.40
节点（共 5 个）：9.1 新建 `tests/test_hybrid_search.py`, 9.2 新建 `tests/test_desc_extraction.py`, 9.3 Benchmark fixture, 9.4 top_n 多结果测试, 9. 步骤 9：测试

### 社区 555 —— "SamplePackage"
凝聚度：0.40
节点（共 5 个）：FCL, LCL, sampleutils, sample, SamplePackage

### 社区 556 —— "§11 质量检查"
凝聚度：0.20
节点（共 10 个）：§11 质量检查, Step 0-1（全局意图 + 结构）质量检查, Step 2（边界）质量检查, Step 3（流程）质量检查, Step 4（契约）质量检查, Step 5（事件）质量检查, Step 6（聚合协作）质量检查, Step 7（不变式）质量检查（还有 2 个）

### 社区 557 —— "validate_url"
凝聚度：0.18
节点（共 10 个）：_NoFileRedirectHandler, Raise ValueError if *url* is not http or https, or targets a private/internal…, Redirect handler that re-validates every redirect target. Prevents open-…, validate_url(), test_validate_url_accepts_http(), test_validate_url_accepts_https(), test_validate_url_rejects_data(), test_validate_url_rejects_empty_scheme()（还有 2 个）

### 社区 558 —— "validate_graph_path"
凝聚度：0.18
节点（共 11 个）：Path, Resolve *path* and verify it stays inside *base*. *base* defaults to the…, validate_graph_path(), With base omitted, the output dir is discovered by walking the path's parents…, The base=None discovery must honour GRAPHIFY_OUT, not the hardcoded '.graph'…, test_validate_graph_path_allows_inside_base(), test_validate_graph_path_blocks_traversal(), test_validate_graph_path_default_base_discovers_output_dir()（还有 3 个）

### 社区 560 —— "verilog.py"
凝聚度：0.12
节点（共 18 个）：_import_js(), _dynamic_import_js(), _find_require_call(), _js_import_binds_external(), True when a JS/TS import specifier names a module outside the scanned corpus.…, Detect dynamic import() calls in JS/TS and emit imports_from edges. Handles…, Return the call_expression node if `value_node` is a `require(...)` call or…, Detect CommonJS require imports inside lexical_declaration /…（还有 10 个）

### 社区 562 —— "cli.py"
凝聚度：0.02
节点（共 117 个）：disambiguate_file_labels_in_nodes(), distinct_repo_tags(), Return a unique, human-meaningful repo tag per input graph for merge-graphs.…, Relabel colliding-basename file nodes on a raw node-dict list, in place…, _clone_repo(), _default_graph_path(), dispatch_command(), _do_embedding_refresh()（还有 109 个）

### 社区 564 —— "test_hooks.py"
凝聚度：0.07
节点（共 30 个）：_detached_launch(), Return a POSIX-sh line that runs ``rebuild_body`` as a detached background…, Tests for hooks.py - git hook install/uninstall., Test 1: .graphifyrc parsing for valid and invalid values., Hook script must skip shebang extraction for .exe binaries (Windows)., The detection fallback must emit a message to stderr rather than bare exit 0. A…, graphify hook-check must not emit additionalContext — Codex Desktop rejects it., The shared rebuild bodies are embedded verbatim into the launcher, so they too…（还有 22 个）

### 社区 565 —— "load_platforms"
凝聚度：0.13
节点（共 22 个）：_powershell_platform_keys(), The agents skill body is amp's body verbatim (it re-homes amp's bundle). The…, Every platform now carries one unified frontmatter description, byte for byte.…, Every platform that renders for a strict-PowerShell host (windows today, plus…, #2528: the Windows variant had a PowerShell Step 1 but bash for Steps 2+…, aider and devin render one inline body, no split and no references dir., Every line that differs from pristine v8 is a sanctioned change-class. The…, The four #1392 data-loss/correctness fixes are present in both monoliths. The…（还有 14 个）

### 社区 566 —— "HybridScorer"
凝聚度：0.06
节点（共 26 个）：HybridScorer, Holds loaded embedding matrix + query embedding cache. One instance per loaded…, True iff the embedding sidecar loaded AND a backend is configured., Return the fuzzy bonus for a (query_token, node_label) pair. Returns 0.0 when…, Vector tier bonus for a cosine similarity value. Public so tests can assert the…, _GraphContextCache, Thread-safe graph contexts: one pinned default plus an LRU of projects., Build one entry for an already-resolved path and known file key.…（还有 18 个）

### 社区 570 —— "2. 边模型"
凝聚度：0.50
节点（共 4 个）：2.1 通用字段, 2.2 `relation` 封闭集合值, 2.3 `confidence` 三值枚举, 2. 边模型

### 社区 571 —— "User Management Test Project"
凝聚度：0.40
节点（共 4 个）：Bounded Contexts, Purpose, Structure, User Management Test Project

### 社区 572 —— "限界上下文映射（Context Map）"
凝聚度：0.40
节点（共 4 个）：业务关系, 统一语言, 限界上下文, 限界上下文映射（Context Map）

### 社区 573 —— "订单领域模型（Domain Model）"
凝聚度：0.40
节点（共 4 个）：支付聚合, 聚合协作关系, 订单聚合, 订单领域模型（Domain Model）

### 社区 574 —— "技术约束（Technical Constraints）"
凝聚度：0.40
节点（共 4 个）：TC-001: 消息中间件选型, TC-002: 数据库分库策略, TC-003: API 网关选型, 技术约束（Technical Constraints）

### 社区 575 —— "TOtherGadget"
凝聚度：0.40
节点（共 3 个）：OtherGadget, TObject, TOtherGadget

### 社区 576 —— "sample.sql"
凝聚度：0.60
节点（共 3 个）：active_users, organizations, users

### 社区 577 —— "sample_doctest.cpp"
凝聚度：0.40
节点（共 3 个）："addition works", "handles \"quoted\" names", "subtraction works"

### 社区 578 —— "MyApp.Accounts.User"
凝聚度：0.50
节点（共 3 个）：MyApp.Accounts.User, create(), validate()

### 社区 582 —— "sample.sln"
凝聚度：0.70
节点（共 3 个）：Domain, WebApi, Tests

### 社区 583 —— "UserControl"
凝聚度：0.40
节点（共 3 个）：DesignViewModel, DesignView, UserControl

### 社区 584 —— "MainViewModel"
凝聚度：0.40
节点（共 3 个）：MainViewModel, MainWindow, Window

### 社区 585 —— "httpx Corpus Benchmark"
凝聚度：0.40
节点（共 4 个）：Corpus (6 files), How to run, httpx Corpus Benchmark, What to expect

### 社区 586 —— "Mixed Corpus Benchmark"
凝聚度：0.40
节点（共 4 个）：Corpus (5 files), How to run, Mixed Corpus Benchmark, What to expect

### 社区 587 —— "Plan: 解析器扩展机制差异修复"
凝聚度：0.50
节点（共 3 个）：Plan: 解析器扩展机制差异修复, 回归测试, 执行顺序与依赖

### 社区 588 —— "10. 步骤 10：验证"
凝聚度：0.50
节点（共 4 个）：10.1 单元测试, 10.2 集成测试, 10.3 回 upstream 兼容性, 10. 步骤 10：验证

### 社区 589 —— "1. 步骤 1：创建 `graphify/desc.py`（节点 desc 字段提取）"
凝聚度：0.50
节点（共 4 个）：1.1 职责, 1.2 文件内容, 1.3 LOC 估算：~100 LOC, 1. 步骤 1：创建 `graphify/desc.py`（节点 desc 字段提取）

### 社区 590 —— "2. 步骤 2：创建 `graphify/embeddings.py`"
凝聚度：0.50
节点（共 4 个）：2.1 职责, 2.2 文件结构, 2.3 LOC 估算：~250 LOC, 2. 步骤 2：创建 `graphify/embeddings.py`

### 社区 591 —— "4. 步骤 4：修改 `graphify/extractors/markdown.py`（文档节点 desc）"
凝聚度：0.50
节点（共 4 个）：4.1 职责, 4.2 改动点, 4.3 LOC 估算：~40 LOC（改动）, 4. 步骤 4：修改 `graphify/extractors/markdown.py`（文档节点 desc）

### 社区 592 —— "5. 步骤 5：创建 `graphify/fuzzy.py`"
凝聚度：0.50
节点（共 4 个）：5.1 职责, 5.2 文件内容, 5.3 LOC 估算：~50 LOC, 5. 步骤 5：创建 `graphify/fuzzy.py`

### 社区 593 —— "6. 步骤 6：创建 `graphify/hybrid_scorer.py`"
凝聚度：0.50
节点（共 4 个）：6.1 职责, 6.2 文件内容, 6.3 LOC 估算：~80 LOC, 6. 步骤 6：创建 `graphify/hybrid_scorer.py`

### 社区 594 —— "generate_header"
凝聚度：0.50
节点（共 4 个）：generate_header(), generate_nav(), Generate the sticky navigation bar., Generate the HTML header, title, subtitle, and nav.

### 社区 595 —— "test_swift_builtin_noise.py"
凝聚度：0.32
节点（共 7 个）：_labels_by_id(), parametrize, Swift/Foundation/SwiftUI builtins must not become god nodes or bind to user…, Swift framework symbols must be filtered from god_nodes output. Constructs a…, test_god_nodes_excludes_swift_builtin_labels(), test_swift_builtin_receiver_does_not_bind_to_user_symbol(), test_swift_user_receiver_type_still_resolves()

### 社区 596 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 597 —— "graphify reference: commit hook and native AGENTS.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### 社区 598 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 600 —— "_match_anchored_ignore_pattern"
凝聚度：0.33
节点（共 6 个）：_match_anchored_ignore_pattern(), _match_globstar_parts(), Recursive ``**``-aware segment match, memoized via an explicit dict. Lifted out…, Match an anchored gitignore pattern without letting ``*`` cross ``/``., `_match_anchored_ignore_pattern` must not leak a reference cycle per call, as…, test_globstar_matcher_leaves_no_reference_cycle()

### 社区 602 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 603 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 604 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 614 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 615 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 616 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 623 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 624 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 625 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 629 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 630 —— "graphify reference: commit hook and native AGENTS.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native AGENTS.md integration (Trae), graphify reference: commit hook and native AGENTS.md integration

### 社区 631 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 632 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 633 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 634 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 635 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 636 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 637 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 639 —— "用户管理"
凝聚度：0.67
节点（共 3 个）：用户管理, 认证, 认证

### 社区 645 —— "订单业务流程（Business Flow）"
凝聚度：0.50
节点（共 3 个）：下单流程, 订单业务流程（Business Flow）, 退款流程

### 社区 646 —— "订单业务契约（Contracts）"
凝聚度：0.50
节点（共 3 个）：支付上下文对外契约, 订单上下文对外契约, 订单业务契约（Contracts）

### 社区 647 —— "订单领域事件（Domain Events）"
凝聚度：0.50
节点（共 3 个）：支付上下文事件, 订单上下文事件, 订单领域事件（Domain Events）

### 社区 648 —— "App"
凝聚度：0.83
节点（共 3 个）：App(), fmtCount(), fmtDate()

### 社区 651 —— "sample_transaction.sql"
凝聚度：0.67
节点（共 3 个）：alfa, delta, gamma

### 社区 652 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 653 —— "graphify reference: commit hook and native AGENTS.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### 社区 654 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 655 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 656 —— "graphify reference: commit hook and native AGENTS.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### 社区 657 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 658 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 659 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 660 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 661 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 662 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 663 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 664 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 665 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 666 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 667 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 668 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 669 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 670 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 671 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 672 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 673 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 674 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 675 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 676 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 677 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 678 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 679 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 680 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 681 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 682 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 683 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 684 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 685 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 686 —— "graphify reference: commit hook and native AGENTS.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native AGENTS.md integration (Trae), graphify reference: commit hook and native AGENTS.md integration

### 社区 687 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 688 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 689 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 690 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 691 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 692 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 693 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 694 —— "graphify reference: commit hook and native AGENTS.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native AGENTS.md integration@@AGENTS_HEADING_SUFFIX@@, graphify reference: commit hook and native AGENTS.md integration

### 社区 695 —— "graphify reference: add a URL and watch a folder"
凝聚度：0.50
节点（共 3 个）：For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### 社区 696 —— "graphify reference: commit hook and native CLAUDE.md integration"
凝聚度：0.50
节点（共 3 个）：For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### 社区 697 —— "graphify reference: incremental update and cluster-only"
凝聚度：0.50
节点（共 3 个）：For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### 社区 698 —— "8. 步骤 8：修改 `graphify/cli.py`（build-time embed 命令）"
凝聚度：0.67
节点（共 3 个）：8.1 新增 `--embed-backend` flag, 8.2 extract 完成后触发 embedding 生成, 8. 步骤 8：修改 `graphify/cli.py`（build-time embed 命令）

### 社区 729 —— "订单业务不变式（Invariants）"
凝聚度：0.50
节点（共 3 个）：支付聚合不变式, 订单业务不变式（Invariants）, 订单聚合不变式

### 社区 740 —— "test_ingest_non_dict_input_returns_empty"
凝聚度：0.67
节点（共 3 个）：parametrize, Non-dict inputs are guarded and return empty nodes/edges., test_ingest_non_dict_input_returns_empty()

### 社区 772 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\env.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\env.py, hash, mtime

### 社区 773 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0002_add_preview_columns.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0002_add_preview_columns.py, hash, mtime

### 社区 774 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0003_make_siege_date_nullable.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0003_make_siege_date_nullable.py, hash, mtime

### 社区 775 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0004_add_post_priority_config.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0004_add_post_priority_config.py, hash, mtime

### 社区 776 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0005_add_description_to_post_priority_config.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0005_add_description_to_post_priority_config.py, hash, mtime

### 社区 777 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0006_power_level_and_drop_sort_value.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0006_power_level_and_drop_sort_value.py, hash, mtime

### 社区 778 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0007_fix_group_number_max.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0007_fix_group_number_max.py, hash, mtime

### 社区 779 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0008_add_matched_condition_id_to_position.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0008_add_matched_condition_id_to_position.py, hash, mtime

### 社区 780 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0009_add_discord_id_to_member.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0009_add_discord_id_to_member.py, hash, mtime

### 社区 781 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0010_add_last_seen_changelog_at_to_member.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0010_add_last_seen_changelog_at_to_member.py, hash, mtime

### 社区 782 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0011_add_post_suggest_preview.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\alembic\\versions\\0011_add_post_suggest_preview.py, hash, mtime

### 社区 783 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\attack_day.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\attack_day.py, hash, mtime

### 社区 784 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\auth.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\auth.py, hash, mtime

### 社区 785 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\autofill.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\autofill.py, hash, mtime

### 社区 786 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\board.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\board.py, hash, mtime

### 社区 787 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\buildings.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\buildings.py, hash, mtime

### 社区 788 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\changelog.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\changelog.py, hash, mtime

### 社区 789 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\comparison.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\comparison.py, hash, mtime

### 社区 790 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\discord_sync.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\discord_sync.py, hash, mtime

### 社区 791 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\health.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\health.py, hash, mtime

### 社区 792 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\images.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\images.py, hash, mtime

### 社区 793 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\lifecycle.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\lifecycle.py, hash, mtime

### 社区 794 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\members.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\members.py, hash, mtime

### 社区 795 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\notifications.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\notifications.py, hash, mtime

### 社区 796 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\post_priority_config.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\post_priority_config.py, hash, mtime

### 社区 797 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\post_suggestions.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\post_suggestions.py, hash, mtime

### 社区 798 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\posts.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\posts.py, hash, mtime

### 社区 799 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\reference.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\reference.py, hash, mtime

### 社区 800 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\siege_members.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\siege_members.py, hash, mtime

### 社区 801 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\sieges.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\sieges.py, hash, mtime

### 社区 802 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\validation.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\validation.py, hash, mtime

### 社区 803 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\version.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\api\\version.py, hash, mtime

### 社区 804 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\config.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\config.py, hash, mtime

### 社区 805 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\base.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\base.py, hash, mtime

### 社区 806 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\__init__.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\__init__.py, hash, mtime

### 社区 807 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\seeds.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\seeds.py, hash, mtime

### 社区 808 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\session.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\db\\session.py, hash, mtime

### 社区 809 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\dependencies\\auth.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\dependencies\\auth.py, hash, mtime

### 社区 810 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\dependencies\\__init__.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\dependencies\\__init__.py, hash, mtime

### 社区 811 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\__init__.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\__init__.py, hash, mtime

### 社区 812 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\main.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\main.py, hash, mtime

### 社区 813 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\middleware.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\middleware.py, hash, mtime

### 社区 814 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\building_group.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\building_group.py, hash, mtime

### 社区 815 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\building.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\building.py, hash, mtime

### 社区 816 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\building_type_config.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\building_type_config.py, hash, mtime

### 社区 817 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\enums.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\enums.py, hash, mtime

### 社区 818 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\__init__.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\__init__.py, hash, mtime

### 社区 819 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\member_post_preference.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\member_post_preference.py, hash, mtime

### 社区 820 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\member.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\member.py, hash, mtime

### 社区 821 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\notification_batch.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\notification_batch.py, hash, mtime

### 社区 822 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\notification_batch_result.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\notification_batch_result.py, hash, mtime

### 社区 823 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\position.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\position.py, hash, mtime

### 社区 824 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post_active_condition.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post_active_condition.py, hash, mtime

### 社区 825 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post_condition.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post_condition.py, hash, mtime

### 社区 826 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post_priority_config.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post_priority_config.py, hash, mtime

### 社区 827 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\post.py, hash, mtime

### 社区 828 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\siege_member.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\siege_member.py, hash, mtime

### 社区 829 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\siege.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\models\\siege.py, hash, mtime

### 社区 830 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\rate_limit.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\rate_limit.py, hash, mtime

### 社区 831 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\attack_day.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\attack_day.py, hash, mtime

### 社区 832 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\autofill.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\autofill.py, hash, mtime

### 社区 833 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\board.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\board.py, hash, mtime

### 社区 834 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\building.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\building.py, hash, mtime

### 社区 835 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\changelog.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\changelog.py, hash, mtime

### 社区 836 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\common.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\common.py, hash, mtime

### 社区 837 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\comparison.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\comparison.py, hash, mtime

### 社区 838 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\__init__.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\__init__.py, hash, mtime

### 社区 839 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\member.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\member.py, hash, mtime

### 社区 840 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\post_condition.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\post_condition.py, hash, mtime

### 社区 841 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\post.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\post.py, hash, mtime

### 社区 842 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\post_suggestions.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\post_suggestions.py, hash, mtime

### 社区 843 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\siege_member.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\siege_member.py, hash, mtime

### 社区 844 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\siege.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\siege.py, hash, mtime

### 社区 845 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\validation.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\validation.py, hash, mtime

### 社区 846 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\version.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\schemas\\version.py, hash, mtime

### 社区 847 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\attack_day.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\attack_day.py, hash, mtime

### 社区 848 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\autofill.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\autofill.py, hash, mtime

### 社区 849 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\board.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\board.py, hash, mtime

### 社区 850 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\bot_client.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\bot_client.py, hash, mtime

### 社区 851 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\building_capacity.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\building_capacity.py, hash, mtime

### 社区 852 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\buildings.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\buildings.py, hash, mtime

### 社区 853 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\comparison.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\comparison.py, hash, mtime

### 社区 854 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\discord_sync.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\discord_sync.py, hash, mtime

### 社区 855 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\image_gen.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\image_gen.py, hash, mtime

### 社区 856 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\lifecycle.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\lifecycle.py, hash, mtime

### 社区 857 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\members.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\members.py, hash, mtime

### 社区 858 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\notification_message.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\notification_message.py, hash, mtime

### 社区 859 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\post_suggestions.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\post_suggestions.py, hash, mtime

### 社区 860 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\posts.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\posts.py, hash, mtime

### 社区 861 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\reference.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\reference.py, hash, mtime

### 社区 862 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\siege_members.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\siege_members.py, hash, mtime

### 社区 863 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\sieges.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\sieges.py, hash, mtime

### 社区 864 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\validation.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\services\\validation.py, hash, mtime

### 社区 865 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\telemetry.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\app\\telemetry.py, hash, mtime

### 社区 866 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\scripts\\seed_demo.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\scripts\\seed_demo.py, hash, mtime

### 社区 867 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\scripts\\seed.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\scripts\\seed.py, hash, mtime

### 社区 868 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\conftest.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\conftest.py, hash, mtime

### 社区 869 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\__init__.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\__init__.py, hash, mtime

### 社区 870 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_attack_day.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_attack_day.py, hash, mtime

### 社区 871 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_auth.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_auth.py, hash, mtime

### 社区 872 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_auth_rate_limit.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_auth_rate_limit.py, hash, mtime

### 社区 873 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_autofill.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_autofill.py, hash, mtime

### 社区 874 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_board.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_board.py, hash, mtime

### 社区 875 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_bot_client.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_bot_client.py, hash, mtime

### 社区 876 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_buildings.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_buildings.py, hash, mtime

### 社区 877 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_changelog.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_changelog.py, hash, mtime

### 社区 878 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_comparison.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_comparison.py, hash, mtime

### 社区 879 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_config_endpoint.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_config_endpoint.py, hash, mtime

### 社区 880 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_config.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_config.py, hash, mtime

### 社区 881 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_cors.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_cors.py, hash, mtime

### 社区 882 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_discord_sync.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_discord_sync.py, hash, mtime

### 社区 883 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_enums.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_enums.py, hash, mtime

### 社区 884 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_health.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_health.py, hash, mtime

### 社区 885 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_image_gen.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_image_gen.py, hash, mtime

### 社区 886 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_lifecycle_integration.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_lifecycle_integration.py, hash, mtime

### 社区 887 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_lifecycle.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_lifecycle.py, hash, mtime

### 社区 888 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_member_changelog_column.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_member_changelog_column.py, hash, mtime

### 社区 889 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_members.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_members.py, hash, mtime

### 社区 890 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_notification_message.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_notification_message.py, hash, mtime

### 社区 891 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_notifications.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_notifications.py, hash, mtime

### 社区 892 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_post_suggestions_integration.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_post_suggestions_integration.py, hash, mtime

### 社区 893 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_post_suggestions.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_post_suggestions.py, hash, mtime

### 社区 894 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_posts.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_posts.py, hash, mtime

### 社区 895 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_reference.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_reference.py, hash, mtime

### 社区 896 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_schema.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_schema.py, hash, mtime

### 社区 897 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_seed_canonical.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_seed_canonical.py, hash, mtime

### 社区 898 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_seed_demo.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_seed_demo.py, hash, mtime

### 社区 899 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_sieges.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_sieges.py, hash, mtime

### 社区 900 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_telemetry.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_telemetry.py, hash, mtime

### 社区 901 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_validation.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_validation.py, hash, mtime

### 社区 902 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_version.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\backend\\tests\\test_version.py, hash, mtime

### 社区 903 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\config.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\config.py, hash, mtime

### 社区 904 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\discord_client.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\discord_client.py, hash, mtime

### 社区 905 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\http_api.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\http_api.py, hash, mtime

### 社区 906 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\__init__.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\__init__.py, hash, mtime

### 社区 907 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\telemetry.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\app\\telemetry.py, hash, mtime

### 社区 908 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\conftest.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\conftest.py, hash, mtime

### 社区 909 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\__init__.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\__init__.py, hash, mtime

### 社区 910 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_discord_client.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_discord_client.py, hash, mtime

### 社区 911 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_get_guild_member.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_get_guild_member.py, hash, mtime

### 社区 912 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_http_api.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_http_api.py, hash, mtime

### 社区 913 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_telemetry.py"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\bot\\tests\\test_telemetry.py, hash, mtime

### 社区 914 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\e2e\\board.spec.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\e2e\\board.spec.ts, hash, mtime

### 社区 915 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\e2e\\siege-lifecycle.spec.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\e2e\\siege-lifecycle.spec.ts, hash, mtime

### 社区 916 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\e2e\\smoke.spec.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\e2e\\smoke.spec.ts, hash, mtime

### 社区 917 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\eslint.config.js"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\eslint.config.js, hash, mtime

### 社区 918 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\playwright.config.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\playwright.config.ts, hash, mtime

### 社区 919 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\postcss.config.js"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\postcss.config.js, hash, mtime

### 社区 920 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\board.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\board.ts, hash, mtime

### 社区 921 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\changelog.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\changelog.ts, hash, mtime

### 社区 922 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\client.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\client.ts, hash, mtime

### 社区 923 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\config.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\config.ts, hash, mtime

### 社区 924 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\members.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\members.ts, hash, mtime

### 社区 925 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\notifications.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\api\\notifications.ts, hash, mtime

### 社区 926 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\App.tsx"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\App.tsx, hash, mtime

### 社区 927 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\main.tsx"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\main.tsx, hash, mtime

### 社区 928 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\vite-env.d.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\src\\vite-env.d.ts, hash, mtime

### 社区 929 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\tailwind.config.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\tailwind.config.ts, hash, mtime

### 社区 930 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\vite.config.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\vite.config.ts, hash, mtime

### 社区 931 —— "I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\vitest.config.ts"
凝聚度：0.67
节点（共 3 个）：I:\\games\\raid\\siege-web\\.worktrees\\experiment-graphify-dry-run-doc\\frontend\\vitest.config.ts, hash, mtime

## 歧义边——需复核
- `.handleRegister()` → `业务异常用 Error 抛出`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/technical-constraints.md · 关系：references
- `.generateToken()` → `签发令牌`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/business-flow.md · 关系：references
- `.generateToken()` → `JWT 令牌认证`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/technical-constraints.md · 关系：references
- `Logger` → `日志不变式`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/invariants.md · 关系：references
- `User` → `聚合根不变式`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/invariants.md · 关系：references
- `.findByEmail()` → `按邮箱查询用户`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/business-flow.md · 关系：references
- `.findByEmail()` → `检查邮箱唯一性`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/business-flow.md · 关系：references
- `.findByEmail()` → `用户不存在`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/business-flow.md · 关系：references
- `.findByEmail()` → `邮箱已注册`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/business-flow.md · 关系：references
- `.findByEmail()` → `用户查询承诺`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/contracts.md · 关系：references
- `UserService` → `用户管理服务`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/domain-model.md · 关系：references
- `UserService` → `DELETE /rest/userservice/v1/users/{id}`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `GET /rest/userservice/v1/users`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `GET /rest/userservice/v1/users/{id}`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `POST /rest/userservice/v1/users`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `POST /rest/userservice/v1/users/{id}/reactivate`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `POST /rest/userservice/v1/users/{id}/suspend`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `PUT /rest/userservice/v1/users/{id}`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `Logger` → `日志不变式`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/invariants.md · 关系：references
- `Logger` → `日志不变式`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/invariants.md · 关系：references
- `Logger` → `日志不变式`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/invariants.md · 关系：references
- `.create()` → `POST /rest/apppublishservice/v1/app`  [AMBIGUOUS]
  tests/fixtures/swagger/apppublish.yaml · 关系：references
- `UserService` → `用户管理服务`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/features/user-management/domain-model.md · 关系：references
- `UserService` → `DELETE /rest/userservice/v1/users/{id}`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `GET /rest/userservice/v1/users`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `GET /rest/userservice/v1/users/{id}`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `POST /rest/userservice/v1/users`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `POST /rest/userservice/v1/users/{id}/reactivate`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `POST /rest/userservice/v1/users/{id}/suspend`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `UserService` → `PUT /rest/userservice/v1/users/{id}`  [AMBIGUOUS]
  tests/e2e/resources/user-management/docs/user-api.yaml · 关系：references
- `.create()` → `POST /rest/apppublishservice/v1/app`  [AMBIGUOUS]
  tests/fixtures/swagger/apppublish.yaml · 关系：references

## 知识空白
- **2707 个孤立节点：** `$schema`, `.opencode/plugins/graphify.js`, `$schema`, `.opencode/plugins/graphify.js`, `name`（还有 2702 个）
  这些节点的连接数 ≤1——可能漏掉了边，或组件未文档化。
- **190 个稀疏社区（<3 个节点）已从报告中省略** —— 运行 `graphify query` 探索孤立节点。

## 建议提问
_这张图谱特别适合回答以下问题：_

- **`.handleRegister()` 和 `业务异常用 Error 抛出` 之间到底是什么关系？**
  _这条边被标记为 AMBIGUOUS（关系：references）——置信度低。_
- **`.generateToken()` 和 `签发令牌` 之间到底是什么关系？**
  _这条边被标记为 AMBIGUOUS（关系：references）——置信度低。_
- **`.generateToken()` 和 `JWT 令牌认证` 之间到底是什么关系？**
  _这条边被标记为 AMBIGUOUS（关系：references）——置信度低。_
- **`Logger` 和 `日志不变式` 之间到底是什么关系？**
  _这条边被标记为 AMBIGUOUS（关系：references）——置信度低。_
- **`User` 和 `聚合根不变式` 之间到底是什么关系？**
  _这条边被标记为 AMBIGUOUS（关系：references）——置信度低。_
- **`.findByEmail()` 和 `按邮箱查询用户` 之间到底是什么关系？**
  _这条边被标记为 AMBIGUOUS（关系：references）——置信度低。_
- **`.findByEmail()` 和 `检查邮箱唯一性` 之间到底是什么关系？**
  _这条边被标记为 AMBIGUOUS（关系：references）——置信度低。_