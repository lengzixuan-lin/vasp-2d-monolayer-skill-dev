# CHATGPT_REVIEW.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/1
- PR: pending
- Branch: `task_001_review-github-bridge`
- Task ID: `task_001_review-github-bridge`

## 本轮审查目标

- 审查 GitHub 作为 ChatGPT 与 Codex 中间桥梁的协作流程是否清晰、可执行、安全。
- 优先检查模板、交接文件和忽略规则，而不是深入修改 VASP skill 逻辑。

## 已阅读的文件

- 待 ChatGPT 填写。

## 发现的问题

- 待 ChatGPT 填写。

## 风险等级

- 待 ChatGPT 填写。

## 推荐修改方案

- 待 ChatGPT 填写。

## 建议 Codex 修改的具体文件

- 待 ChatGPT 填写。

## 可选补丁建议

- 待 ChatGPT 填写。

## 需要用户确认的问题

- 待 ChatGPT 填写。

## 建议 ChatGPT 审查范围

- `docs/GITHUB_COLLABORATION_WORKFLOW.md`
- `.github/ISSUE_TEMPLATE/task.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `docs/handoff/README.md`
- `docs/handoff/TEMPLATE.md`
- `.gitignore`
- `docs/VASP_REFERENCES_INDEX.md`
- `CODEX_FEEDBACK.md`

## 建议 Codex 执行步骤

- 根据 ChatGPT 在本文件或 Issue/PR review 中提出的建议执行本地文件修改。
- 更新 `CODEX_FEEDBACK.md`。
- 写入或更新 `docs/handoff/YYYY-MM-DD_task_001_review-github-bridge.md`。
- 提交前执行 `git status`，只 `git add <明确文件>`，不要使用 `git add .`。
- 提交后更新 PR，供 ChatGPT 审查 diff。

## 禁止直接执行的操作

- 不直接执行 `ssh lilin`。
- 不直接执行 `sbatch`。
- 不删除、覆盖或修改远程服务器文件。
- 不修改真实计算任务，除非用户明确确认并交给 Codex 执行。
