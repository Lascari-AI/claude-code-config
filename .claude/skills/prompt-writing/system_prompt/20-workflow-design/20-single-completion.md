---
covers: Thinking-window workflow pattern using <steps> structure
type: pattern
concepts: [single-completion, steps, thinking-window, internal-reasoning, classification, extraction, generation]
depends-on: [system_prompt/20-workflow-design/10-base.md]
---

# Single-Completion Workflows

Workflows where **your code controls execution**. You make the API call, process the response, decide what happens next. The model works through internal reasoning in its thinking window and returns a single, complete response.

---

## When to Use

Use single-completion workflows when:

- **Your code orchestrates**: You call the LLM API directly
- **You process results**: Your application handles the response
- **You control the loop**: Multi-step processes are managed by your code, not the LLM
- **No external feedback needed**: The model doesn't need to wait for tool results mid-reasoning

**Common patterns**:
- Classification (sentiment, category, intent routing)
- Data extraction (entities, structured fields, parsing)
- Content generation (summaries, rewrites, translations)
- Analysis (evaluation, comparison, assessment)
- Agentic loops where YOUR code coordinates multiple LLM calls

**Key insight**: Tool use is fine here. The distinction is WHO controls the execution loop—your code or an autonomous system.

---

## The `<steps>` Structure

Steps are the **internal reasoning scaffold**. They guide how the model thinks through a problem within a single completion.

```xml
<steps>
    <step name="understand_input">
        <description>
        Parse and validate the input. Identify key entities,
        relationships, and any ambiguities to resolve.
        </description>
    </step>

    <step name="analyze">
        <description>
        Apply domain expertise to evaluate the input.
        Consider multiple perspectives before concluding.
        </description>
        <constraints>
        - Cite specific evidence from the input
        - Flag low-confidence assessments
        </constraints>
    </step>

    <step name="synthesize">
        <description>
        Combine analysis into final output.
        Prioritize actionable insights.
        </description>
    </step>
</steps>
```

### How Steps Execute

1. Model reads all steps upfront
2. Works through them in thinking window (internal)
3. No external feedback between steps
4. Output is the result of processing ALL steps

Steps are a **reasoning guide**, not a tool-calling sequence. The model uses them to organize its thinking, but the execution is internal and continuous.

---

## Step Anatomy

Each step has:

| Element | Required | Purpose |
|---------|----------|---------|
| `name` attribute | Yes | Identifier for the step (snake_case) |
| `<description>` | Yes | What to do, how, and why it matters |
| `<constraints>` | No | Rules specific to THIS step only |

### Writing Good Steps

**Name**: Use action verbs that describe the reasoning phase
- `parse_input`, `evaluate_criteria`, `generate_response`
- NOT: `step_1`, `process`, `do_thing`

**Description**: Include methodology, not just action
```xml
<!-- Weak -->
<description>Classify the sentiment</description>

<!-- Strong -->
<description>
Classify sentiment as positive, negative, or neutral.
Look for explicit emotional language first, then consider
implicit sentiment through word choice and context.
Weight recent statements more heavily than opening statements.
</description>
```

**Constraints**: Localize rules to specific steps
```xml
<step name="cite_evidence">
    <description>Support conclusions with specific quotes</description>
    <constraints>
    - Minimum 2 quotes per major claim
    - Include page/section references
    - Do not paraphrase; use exact text
    </constraints>
</step>
```

---

## No External State

Single-completion workflows have no concept of external state:

| Aspect | Single-Completion | Multi-Turn |
|--------|-------------------|------------|
| State | In-context only | External files, databases |
| Feedback | None during execution | Tool results, state reads |
| Output | Single response | Incremental across turns |
| Recovery | Not applicable | Explicit error handling |

**Implication**: Everything the model needs must be provided in the prompt. There's no "read state file" or "wait for tool result" during reasoning.

---

## Global vs Step Constraints

Place constraints at the right scope:

```xml
<workflow>
    <steps>
        <step name="analyze">
            <constraints>
            <!-- Rules for THIS step only -->
            - Use only data from the provided context
            </constraints>
        </step>
    </steps>

    <global_constraints>
    <!-- Rules that apply EVERYWHERE -->
    - Maintain professional tone
    - Never include PII in output
    - Response must be under 500 words
    </global_constraints>
</workflow>
```

**Localization principle**: If a rule only matters for one step, put it there. Global constraints apply to ALL reasoning.

---

## Examples

### Classification Workflow

```xml
<steps>
    <step name="identify_signals">
        <description>
        Scan input for classification signals: keywords,
        phrases, structural patterns, and metadata.
        </description>
    </step>

    <step name="evaluate_categories">
        <description>
        Map signals to possible categories. Weight signals
        by reliability. Identify the strongest match.
        </description>
        <constraints>
        - Require 3+ signals for high-confidence classification
        - Flag ambiguous cases explicitly
        </constraints>
    </step>

    <step name="output_classification">
        <description>
        Return category with confidence score and
        supporting evidence.
        </description>
    </step>
</steps>
```

### Extraction Workflow

```xml
<steps>
    <step name="parse_structure">
        <description>
        Identify document structure: sections, tables,
        lists, headers. Build mental map of content location.
        </description>
    </step>

    <step name="locate_fields">
        <description>
        For each target field, identify location in document.
        Handle variations in labeling and formatting.
        </description>
    </step>

    <step name="extract_and_normalize">
        <description>
        Extract values and normalize to target schema.
        Apply type coercion and validation rules.
        </description>
        <constraints>
        - Dates to ISO 8601 format
        - Currency to decimal (no symbols)
        - Missing fields as null (not empty string)
        </constraints>
    </step>
</steps>
```

### Generation Workflow

```xml
<steps>
    <step name="understand_requirements">
        <description>
        Parse the generation request. Identify: target format,
        length constraints, tone, audience, key points to cover.
        </description>
    </step>

    <step name="plan_structure">
        <description>
        Outline the response structure. Determine section
        breakdown and information flow.
        </description>
    </step>

    <step name="draft_content">
        <description>
        Generate content following the plan. Maintain
        consistent voice throughout.
        </description>
    </step>

    <step name="refine">
        <description>
        Review for clarity, accuracy, and adherence to
        constraints. Adjust as needed.
        </description>
    </step>
</steps>
```

---

## Template Reference

For the complete single-completion template with all sections:

→ **[10-single-completion.md](../10-single-completion.md)** - Full template with Purpose, Knowledge, Goal, Background, Workflow structure

For base workflow principles that apply to all patterns:

→ **[10-base.md](10-base.md)** - Constraint localization, output format vs protocol, `<critical>` tags
