# Implementation Plan

> **Session**: `2026-01-01_updating-plan-mode_p4k7n2`
> **Status**: Complete
> **Spec**: [./spec.md](./spec.md)
> **Created**: 2026-01-01
> **Updated**: 2026-01-01

---

## Overview

- **Checkpoints**: 5 (0 complete)
- **Total Tasks**: 0

## ⬜ Checkpoint 1: Update Plan Templates and Data Models

**Goal**: Replace Tranche/Subtask terminology with Task Group/Action in templates and Pydantic models

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `.claude/skills/session/plan/templates/plan.json` | 📄 exists | Current template using 'tranches' and 'subtasks' |
| Before | `.claude/skills/session/plan/reference/models.py` | 📄 exists | Pydantic models with Tranche and Subtask classes |
| After | `.claude/skills/session/plan/templates/plan.json` | 📝 modified | Template using 'task_groups' and 'actions' |
| After | `.claude/skills/session/plan/reference/models.py` | 📝 modified | Pydantic models with TaskGroup and Action classes |

**Projected Structure**:
```
.claude/skills/session/plan/
├── templates/
│   └── plan.json (updated)
└── reference/
    └── models.py (updated)
```

### Testing Strategy

**Approach**: Syntax validation and structure verification

**Verification Steps**:
- [ ] `python -c "import json; json.load(open('.claude/skills/session/plan/templates/plan.json'))"`
- [ ] `python -c "import sys; sys.path.insert(0, '.claude/skills/session/plan'); from reference.models import Plan, TaskGroup, Action"`

---

## ⬜ Checkpoint 2: Update Plan Phase Documentation and Command

**Goal**: Implement tiered progressive confirmation workflow in OVERVIEW.md and plan.md command

**Prerequisites**: Checkpoints 1

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `.claude/skills/session/plan/OVERVIEW.md` | 📄 exists | Current documentation with Tranche terminology |
| Before | `.claude/commands/session/plan.md` | 📄 exists | Current plan command with two-tier workflow |
| After | `.claude/skills/session/plan/OVERVIEW.md` | 📝 modified | Updated with Task Group/Action and tiered workflow |
| After | `.claude/commands/session/plan.md` | 📝 modified | Updated command with 4-tier progressive confirmation |

**Projected Structure**:
```
.claude/
├── skills/session/plan/
│   └── OVERVIEW.md (updated)
└── commands/session/
    └── plan.md (updated)
```

### Testing Strategy

**Approach**: Manual review of documentation clarity and workflow consistency

**Verification Steps**:
- [ ] `Review OVERVIEW.md for consistent Task Group/Action terminology`
- [ ] `Verify plan.md command flow matches spec tiered diagram`

---

## ⬜ Checkpoint 3: Update Sync Script for New Structure

**Goal**: Modify sync-plan-md.py to generate markdown using Task Group/Action terminology

**Prerequisites**: Checkpoints 1

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `.claude/skills/session/plan/scripts/sync-plan-md.py` | 📄 exists | Current script generating markdown with Tranche/Subtask terminology |
| After | `.claude/skills/session/plan/scripts/sync-plan-md.py` | 📝 modified | Updated script generating markdown with Task Group/Action terminology |

**Projected Structure**:
```
.claude/skills/session/plan/scripts/
└── sync-plan-md.py (updated)
```

### Testing Strategy

**Approach**: JSON parsing and output verification

**Verification Steps**:
- [ ] `python -c "import sys; sys.path.insert(0, '.claude/skills/session/plan/scripts'); import importlib.util; spec = importlib.util.spec_from_file_location('sync', '.claude/skills/session/plan/scripts/sync-plan-md.py'); m = importlib.util.module_from_spec(spec)"`

---

## ⬜ Checkpoint 4: Update Build Phase for Checkpoint-Commit Workflow

**Goal**: Implement checkpoint=commit boundary, no auto-continuation in build commands

**Prerequisites**: Checkpoints 1

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `.claude/skills/session/build/OVERVIEW.md` | 📄 exists | Current build documentation with tranche terminology |
| Before | `.claude/commands/session/build.md` | 📄 exists | Interactive build command |
| Before | `.claude/commands/session/build-background.md` | 📄 exists | Autonomous build command with tranche references |
| After | `.claude/skills/session/build/OVERVIEW.md` | 📝 modified | Updated with task_group terminology and checkpoint=commit |
| After | `.claude/commands/session/build.md` | 📝 modified | Updated with task_group and git commit at checkpoint end |
| After | `.claude/commands/session/build-background.md` | 📝 modified | Updated with task_group and git commit at checkpoint end |

**Projected Structure**:
```
.claude/
├── skills/session/build/
│   └── OVERVIEW.md (updated)
└── commands/session/
    ├── build.md (updated)
    └── build-background.md (updated)
```

### Testing Strategy

**Approach**: Review documentation for consistency

**Verification Steps**:
- [ ] `grep -r 'tranche' .claude/skills/session/build/ .claude/commands/session/build*.md should return no matches`
- [ ] `grep -r 'git commit' .claude/skills/session/build/ .claude/commands/session/build*.md should return matches`

---

## ⬜ Checkpoint 5: Add Prior Spec Referencing to Spec Phase

**Goal**: Update spec.md command to prompt for and store prior session references

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `.claude/commands/session/spec.md` | 📄 exists | Current spec command without prior spec prompting |
| Before | `.claude/skills/session/spec/OVERVIEW.md` | 📄 exists | Current spec phase documentation |
| After | `.claude/commands/session/spec.md` | 📝 modified | Updated with prior spec referencing workflow |
| After | `.claude/skills/session/spec/OVERVIEW.md` | 📝 modified | Updated with prior spec documentation |

**Projected Structure**:
```
.claude/
├── commands/session/
│   └── spec.md (updated)
└── skills/session/spec/
    └── OVERVIEW.md (updated)
```

### Testing Strategy

**Approach**: Documentation review

**Verification Steps**:
- [ ] `grep 'prior' .claude/commands/session/spec.md should return matches`
- [ ] `grep 'prior_session' .claude/skills/session/spec/OVERVIEW.md should return matches`

---

---
*Auto-generated from plan.json on 2026-01-01 11:41*