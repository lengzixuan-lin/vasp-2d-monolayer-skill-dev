# VASP References Index

The local workspace contains a reference bundle at:

```text
vasp_references资料/
```

This bundle is local-only by default and should not enter this bridge PR.

ChatGPT's second review recorded the user's confirmation that the full bundle
should not remain in PR #2 and that third-party PDFs, images, source trees,
config files, and binaries should not enter long-term git history through this
bridge task.

When ChatGPT needs this material for review, prefer these safer approaches:

- Read the tracked Markdown, JSON, configuration, and source files first.
- Use PDFs and images only when they are directly relevant to the review question.
- Ask Codex to summarize or index large subsections when full review is not necessary.

Current known local bundle categories:

- JAMIP materials
- VASPKIT materials

Previous preflight summary:

- Total tracked bundle size before git compression: about 58 MB.
- Largest single file found before upload: about 14.7 MB.
- No file exceeded GitHub's ordinary 100 MB single-file limit during preflight inspection.

Current PR policy:

- The full `vasp_references资料/` bundle has been removed from Git tracking for
  this PR with `git rm --cached`, preserving local files.
- The bridge PR should only carry workflow, template, handoff, feedback, and
  safety-boundary documents.
- Future reference material should be curated into small Markdown/YAML/TXT
  summaries unless the user explicitly approves a separate reference-bundle PR.

Future policy:

- Prefer curated Markdown/YAML/TXT summaries for GitHub review.
- Do not add new full reference bundles, PDFs, images, generated parser caches,
  third-party source trees, or binaries unless the user explicitly approves that
  exact exception.
