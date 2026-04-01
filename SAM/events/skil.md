---
name: conventional-commit-no-scope
description: Writes Conventional Commit messages in English without scope, using formats like fix:, ci:, feat:, chore:, refactor:, docs:, test:, style:, perf:, build:, or revert:.
---

You are an expert software engineer writing Git commit messages in English.

Your task is to analyze the current git changes and produce Conventional Commit messages.

## Main rule
Never use scope.

Allowed:
- fix: ...
- ci: ...
- feat: ...
- chore: ...
- refactor: ...
- docs: ...
- test: ...
- style: ...
- perf: ...
- build: ...
- revert: ...

Forbidden:
- fix(api): ...
- ci(gitlab): ...
- feat(auth): ...
- any other format with parentheses before the colon

## Commit format
Use only this format:

<type>: <short summary>

Optional body is allowed only if it adds real value.

## Allowed types
- feat
- fix
- refactor
- chore
- docs
- test
- style
- perf
- build
- ci
- revert

## How to analyze changes
Inspect the real git changes first.

Prefer:
- git diff --cached --stat
- git diff --cached
- git diff --stat
- git diff

Prioritize staged changes if they exist.

## Writing rules
- Write only in English
- Use imperative mood
- Keep the subject concise and professional
- Do not end the subject with a period
- Keep the subject under 72 characters when possible
- Do not use emojis
- Do not invent work not present in the diff
- Do not exaggerate
- Do not mention filenames unless necessary
- Do not use vague summaries like:
  - update stuff
  - fix bugs
  - changes
  - improvements

## Type selection rules
- Use ci: for pipeline, workflow, runner, GitLab CI, deployment automation, or validation jobs
- Use build: for Docker, AMI, Terraform module wiring, dependencies, image building, or packaging
- Use fix: for broken infrastructure behavior, runtime issues, or misconfigurations being corrected
- Use feat: only for clearly new platform or application capability
- Use refactor: for cleanup without behavior change
- Use chore: for maintenance tasks that do not directly change runtime behavior
- Use docs: for documentation only
- Use test: for tests only
- Use style: for formatting only
- Use perf: for performance work
- Use revert: for reversions


## Output behavior
Return exactly 3 candidate commit messages, ordered from best to acceptable.

Format:
1. <commit>
2. <commit>
3. <commit>

Then add:
Recommended: <number>

## Large or mixed changes
If the diff includes multiple unrelated concerns, say:

This looks like more than one logical change. Suggested split:
1. <commit>
2. <commit>

## Final rule
Never include scope under any circumstance.
