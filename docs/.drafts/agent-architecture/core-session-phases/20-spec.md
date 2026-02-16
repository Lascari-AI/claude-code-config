# SPEC Phase — Define Intent

The SPEC phase captures WHAT to build and WHY through an interactive interview.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SPEC PHASE: QUESTION-DRIVEN INTERVIEW                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  The SPEC phase is an INTERACTIVE INTERVIEW with the user.                  │
│  The user is the PRIMARY source of information.                             │
│                                                                             │
│  Core Principles:                                                           │
│  • Ask ONE focused question at a time                                       │
│  • ATOMIC SAVE after EVERY exchange (spec.md + state.json)                  │
│  • Capture WHY, not just WHAT                                               │
│  • Preserve user's mental model and "taste"                                 │
│  • Research is OPTIONAL, triggered when needed                              │
│  • Continue until spec is truly complete                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## High-Level Flow

```
     USER REQUEST
     "Add dark mode"
          │
          ▼
┌───────────────────┐
│   INITIALIZE      │
│   SESSION         │
│                   │
│   - Create dir    │
│   - state.json    │
│   - spec.md       │
└─────────┬─────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│              QUESTION-DRIVEN INTERVIEW LOOP                   │
│                                                               │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│    │   ASK   │────▶│  WAIT   │────▶│ PROCESS │──┐           │
│    │question │     │  for    │     │ answer  │  │           │
│    └─────────┘     │ answer  │     └─────────┘  │           │
│         ▲          └─────────┘          │       │           │
│         │                               ▼       │           │
│         │                        ┌─────────┐    │           │
│         │                        │  SAVE   │    │           │
│         │                        │ (atomic)│    │           │
│         │                        └────┬────┘    │           │
│         │                             │         │           │
│         └─────────────────────────────┘         │           │
│                                                 │           │
│    Exit when: User signals ready OR             │           │
│               All key questions answered        │           │
│                                                 │           │
└─────────────────────────────────┬───────────────┘
                                  │
                                  ▼
                       ┌───────────────────┐
                       │    FINALIZE       │
                       │    + APPROVE      │
                       └─────────┬─────────┘
                                 │
                                 ▼
                          spec.md ready
                          → PLAN phase
```

---

## The Interview Cycle

```
══════════════════════════════════════════════════════════════════════════════
 THE INTERVIEW CYCLE (Repeats until complete)
══════════════════════════════════════════════════════════════════════════════

                    ┌─────────────────────────────┐
                    │        ASK QUESTION         │
                    │                             │
                    │  • ONE question at a time   │
                    │  • Explain WHY you're       │
                    │    asking                   │
                    │  • Be non-obvious           │
                    │  • Dig deep                 │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      WAIT FOR ANSWER        │
                    │                             │
                    │  (User provides response)   │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      PROCESS ANSWER         │
                    │                             │
                    │  • Acknowledge understanding│
                    │  • Capture exact phrasing   │
                    │    for nuance               │
                    │  • Note the WHY behind      │
                    │    their answer             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
          ┌────────────────────────────────────────────────┐
          │              ATOMIC SAVE (CRITICAL)            │
          │                                                │
          │  Update BOTH files IMMEDIATELY after each      │
          │  exchange. Never batch updates.                │
          │                                                │
          │  ┌──────────────────┐  ┌──────────────────┐   │
          │  │    spec.md       │  │   state.json     │   │
          │  │                  │  │                  │   │
          │  │  Add/update      │  │  - open_questions│   │
          │  │  relevant        │  │  - key_decisions │   │
          │  │  section         │  │  - goals arrays  │   │
          │  │                  │  │  - updated_at    │   │
          │  └──────────────────┘  └──────────────────┘   │
          │                                                │
          │  Rationale: Preserves context if session       │
          │  is interrupted. User's input is valuable.     │
          └────────────────────────┬───────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │     DECIDE NEXT ACTION      │
                    └──────────────┬──────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
   ┌────────────┐          ┌────────────┐          ┌────────────┐
   │ More Qs    │          │  Research  │          │  Finalize  │
   │ needed     │          │  needed    │          │  ready     │
   └─────┬──────┘          └─────┬──────┘          └─────┬──────┘
         │                       │                       │
         │                       ▼                       │
         │          ┌────────────────────────┐           │
         │          │ Trigger /research        │          │
         │          │ (optional, on-demand)  │           │
         │          └────────────┬───────────┘           │
         │                       │                       │
         │                       ▼                       │
         │              Resume interview                 │
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                 │
                          Loop continues
```

---

## Question Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SPEC INTERVIEW QUESTION CATEGORIES                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PROBLEM SPACE                                                      │   │
│  │  • What problem are we solving?                                     │   │
│  │  • Who experiences this problem?                                    │   │
│  │  • What's the current workaround?                                   │   │
│  │  • What triggers the need for this?                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  GOALS                                                              │   │
│  │  • What does success look like?                                     │   │
│  │  • How will we know we're done?                                     │   │
│  │  • What's the minimum viable version?                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CONSTRAINTS                                                        │   │
│  │  • What can't change?                                               │   │
│  │  • What dependencies exist?                                         │   │
│  │  • What's the timeline?                                             │   │
│  │  • Are there technical constraints?                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SCOPE                                                              │   │
│  │  • What's explicitly NOT included?                                  │   │
│  │  • What could be a future phase?                                    │   │
│  │  • What's the priority order?                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CONTEXT                                                            │   │
│  │  • How does this fit with existing systems?                         │   │
│  │  • Are there similar implementations to reference?                  │   │
│  │  • Who else is involved in this decision?                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DEEPER EXPLORATION                                                 │   │
│  │  • What concerns you about this approach?                           │   │
│  │  • What tradeoffs are you willing to accept?                        │   │
│  │  • Are there UI/UX considerations that matter?                      │   │
│  │  • What edge cases keep you up at night?                            │   │
│  │  • What would make you consider this a failure even if it "works"?  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TASTE & REASONING (Capture the user's mental model)                │   │
│  │  • What's your mental model for how this should work?               │   │
│  │  • Why does this particular approach resonate with you?             │   │
│  │  • What's the experience you're trying to create?                   │   │
│  │  • When you imagine using this, what does it feel like?             │   │
│  │  • What would feel "off" even if it technically worked?             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Optional: Research During Spec

```
══════════════════════════════════════════════════════════════════════════════
 RESEARCH IS ON-DEMAND, NOT AUTOMATIC
══════════════════════════════════════════════════════════════════════════════

Research is triggered ONLY when:
• Agent needs to understand existing codebase to ask better questions
• User asks "how does X currently work?"
• Agent needs context to clarify something

                    ┌─────────────────────────────┐
                    │  During interview, need     │
                    │  arises to understand       │
                    │  existing system            │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  /research [query]          │
                    │                             │
                    │  --session={session_id}     │
                    │  --phase=spec               │
                    │  --triggered-by="reason"    │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  Research executes:         │
                    │  • Explore codebase         │
                    │  • Generate report.md       │
                    │  • Store in research/       │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  Resume interview with      │
                    │  new understanding          │
                    └─────────────────────────────┘
```

---

## Optional: Debug Sub-Phase

```
══════════════════════════════════════════════════════════════════════════════
 DEBUG SUB-PHASE (When investigating a bug during spec)
══════════════════════════════════════════════════════════════════════════════

    SPEC ──▶ (need to understand bug) ──▶ DEBUG SUB-PHASE ──▶ SPEC (informed)
                                                │
                                                ├── Make EPHEMERAL changes
                                                │   (logs, repro steps)
                                                ├── Investigate root cause
                                                ├── Capture in debug/{issue}.md
                                                └── REVERT changes (not committed)

Key: Debug changes are for UNDERSTANDING, not implementation.
     Actual fix happens in PLAN → BUILD phases.
```

---

## Finalization

```
══════════════════════════════════════════════════════════════════════════════
 FINALIZATION
══════════════════════════════════════════════════════════════════════════════

                    ┌─────────────────────────────┐
                    │  User signals ready to      │
                    │  finalize OR all key        │
                    │  questions answered         │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  Review spec.md for         │
                    │  completeness               │
                    │                             │
                    │  Required sections:         │
                    │  ✓ Overview                 │
                    │  ✓ High-level goals         │
                    │  ✓ Mid-level goals          │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  ASK: What next?            │
                    │                             │
                    │  □ Proceed to plan          │
                    │  □ Complete as-is           │
                    │    (spec-only, no impl)     │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
          ┌─────────────────┐           ┌─────────────────┐
          │ Proceed to plan │           │ Complete as-is  │
          │                 │           │                 │
          │ status:         │           │ status:         │
          │ "finalized"     │           │ "finalized_     │
          │                 │           │  complete"      │
          │ → PLAN phase    │           │                 │
          └─────────────────┘           │ Spec preserved  │
                                        │ as documentation│
                                        └─────────────────┘
```

---

## Artifacts Produced

```
agents/sessions/{session-id}/
├── state.json           # Session state (current_phase, open_questions, etc.)
├── spec.md              # The specification document
├── research/            # Research artifacts (if any research was triggered)
│   └── {research-id}/
│       ├── state.json   # Research metadata
│       └── report.md    # Research findings
├── context/             # Supporting materials
│   └── diagrams/        # Any diagrams created during spec
└── debug/               # Debug artifacts (if debug sub-phase entered)
    └── {issue-slug}.md  # Debug findings
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/session:spec [topic]` | Start new spec session |
| `/session:spec [session-id]` | Resume existing session |
| `/session:spec [session-id] finalize` | Finalize spec for planning |

---

*Draft - expand with more examples and edge cases*
