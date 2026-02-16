---
allowed-tools: Bash(git ls-files:*), Read, Write
description: Answer questions about the project structure and documentation with Mermaid diagrams
argument-hint: [question]
model: opus
---

# Purpose

Answer the user's question by analyzing the project structure and documentation, then enhance the response with relevant Mermaid diagrams that visualize key concepts, relationships, or flows. This prompt provides comprehensive answers with visual aids while following the `Instructions` section guidelines.

## Variables

USER_QUESTION: $1

## Instructions

- **IMPORTANT: This is primarily a question-answering task - focus on providing informative answers**
- **IMPORTANT: Enhance answers with Mermaid diagrams to visualize concepts, relationships, and flows**
- **IMPORTANT: Use appropriate diagram types based on the question context:**
  - `flowchart` - for processes, workflows, and decision trees
  - `sequenceDiagram` - for interactions between components/systems
  - `classDiagram` - for class relationships and structures
  - `erDiagram` - for database/entity relationships
  - `graph` - for general relationships and hierarchies
  - `stateDiagram-v2` - for state machines and transitions
  - `mindmap` - for concept organization and brainstorming
- **IMPORTANT: Diagrams should clarify and enhance understanding, not replace textual explanations**
- **IMPORTANT: If the question requires code changes, explain conceptually with diagrams showing proposed architecture**

## Workflow

1. Run `git ls-files` to understand the project structure
2. Read README.md for project overview and documentation
3. Analyze the project structure to identify relevant files and components
4. Read additional files as needed to answer the question thoroughly
5. Formulate a comprehensive textual answer
6. Determine which diagram type(s) best visualize the answer
7. Create Mermaid diagram(s) that enhance understanding
8. Combine textual answer with diagrams in the response

## Report

Respond with the following format:

### Answer

[Direct, comprehensive answer to the question with supporting evidence from project analysis]

### Diagram(s)

[One or more Mermaid diagrams that visualize the answer. Include a brief description of what each diagram shows.]

```mermaid
[Appropriate diagram type and content]
```

### References

- [List of relevant files and documentation referenced]
- [Key project structure elements related to the answer]

### Additional Context

[Any conceptual explanations, related considerations, or suggestions for further exploration]
