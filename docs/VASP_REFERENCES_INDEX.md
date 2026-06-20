# VASP References Index

The repository contains a reference bundle at:

```text
vasp_references资料/
```

This bundle was originally ignored by git. It is now intentionally tracked after explicit user approval so ChatGPT can read it through GitHub and provide better review suggestions.

Important review note: ChatGPT recommended splitting the full bundle into a
separate PR or replacing it with curated summaries. Codex has not removed the
tracked bundle in this PR because that deletion/restructuring needs explicit
user confirmation.

When ChatGPT needs this material for review, prefer these safer approaches:

- Read the tracked Markdown, JSON, configuration, and source files first.
- Use PDFs and images only when they are directly relevant to the review question.
- Ask Codex to summarize or index large subsections when full review is not necessary.

Current known local bundle categories:

- JAMIP materials
- VASPKIT materials

Current upload summary:

- Total tracked bundle size before git compression: about 58 MB.
- Largest single file found before upload: about 14.7 MB.
- No file exceeded GitHub's ordinary 100 MB single-file limit during preflight inspection.

Current risk summary:

- The current PR changes 404 files relative to `main`.
- `vasp_references资料/` accounts for 399 tracked files.
- The bundle includes PDFs, images, generated JSON, third-party source files,
  configuration files, and binary/tool-like files.
- Keep the repository private unless the user separately confirms copyright and
  redistribution boundaries.

Future policy:

- Prefer curated Markdown/YAML/TXT summaries for GitHub review.
- Do not add new full reference bundles, PDFs, images, generated parser caches,
  third-party source trees, or binaries unless the user explicitly approves that
  exact exception.
