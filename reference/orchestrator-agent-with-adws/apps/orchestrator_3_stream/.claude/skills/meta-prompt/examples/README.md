# Slash Command Examples

This directory contains real-world examples of custom slash commands from the orchestrator_3_stream project. Use these as references when creating new commands.

## Available Examples

### 1. orch_one_shot_agent.md
**Type**: Simple agent lifecycle workflow
**Arguments**: `[task]`
**Key Features**:
- Single dynamic variable
- Static configuration (SLEEP_INTERVAL)
- Clear create → command → check → delete workflow
- Simple progress reporting

**Use as reference for**:
- Basic agent management commands
- Sleep/check polling patterns
- Agent status monitoring

---

### 2. orch_scout_and_build.md
**Type**: Multi-phase workflow
**Arguments**: `[problem-description]`
**Key Features**:
- Two sequential agent phases (Scout → Build)
- Context passing between phases
- Detailed progress reporting at each phase
- Agent preservation (no deletion)

**Use as reference for**:
- Complex multi-phase workflows
- Agent coordination patterns
- Contextual information passing
- Status reporting throughout execution

---

### 3. plan.md
**Type**: Planning and documentation
**Arguments**: `[user prompt]`
**Key Features**:
- Detailed output format specification
- Conditional sections based on task complexity
- Structured markdown template
- File generation with dynamic naming

**Use as reference for**:
- Commands that generate structured documents
- Complex output formatting
- Conditional workflow steps
- Template-based file creation

---

### 4. question.md
**Type**: Read-only analysis
**Arguments**: `$ARGUMENTS` (flexible question)
**Key Features**:
- Tool restrictions (`allowed-tools: Bash(git ls-files:*), Read`)
- Read-only operations (no file modifications)
- Simple workflow with bash execution
- Flexible argument handling

**Use as reference for**:
- Tool-restricted commands
- Read-only analysis tasks
- Git integration commands
- Flexible argument patterns

---

## Pattern Summary

| Pattern | Example | Key Characteristics |
|---------|---------|---------------------|
| **Agent Lifecycle** | orch_one_shot_agent.md | Create → Command → Monitor → Cleanup |
| **Multi-Phase** | orch_scout_and_build.md | Sequential phases with context passing |
| **Document Generation** | plan.md | Structured output with templates |
| **Read-Only Analysis** | question.md | Tool restrictions, no modifications |

---

## How to Use These Examples

1. **Find a similar pattern** to what you want to create
2. **Read the complete example** to understand the structure
3. **Adapt the sections** to your specific use case:
   - Frontmatter (model, description, arguments, tools)
   - Variables (dynamic and static)
   - Instructions (rules and constraints)
   - Workflow (numbered steps)
   - Report (output format)
4. **Test your command** with real inputs
5. **Iterate** based on results

---

## Quick Comparison

**Choose orch_one_shot_agent.md when**:
- You need simple agent task execution
- Single-phase workflow is sufficient
- Agent cleanup is required

**Choose orch_scout_and_build.md when**:
- You need analysis before implementation
- Multiple phases are required
- Context must pass between phases

**Choose plan.md when**:
- You're generating structured documentation
- Output has complex formatting requirements
- Conditional sections are needed

**Choose question.md when**:
- You need read-only analysis
- Tool restrictions are important
- No file modifications should occur
