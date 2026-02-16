# Meta Agent Examples

This file contains comprehensive examples of creating subagents for various use cases, both engineering and non-engineering.

## Engineering Examples

### Example 1: Create a code reviewer subagent (inherit all tools)

User request:
```
Create a subagent that reviews code for quality and security issues
```

You would:

1. Fetch latest documentation from docs.claude.com
2. Analyze requirements:
   - Purpose: Code review
   - Tasks: Check quality, identify security issues, suggest improvements
   - Domain: Software engineering
   - Tools: User didn't specify, so inherit all tools from parent
3. Generate name: `code-reviewer`
4. Select color: `cyan` (technical/code task)
5. Write description: "Expert code reviewer. Use proactively after code changes to check quality, security, and maintainability."
6. Determine tools: OMIT tools field (user didn't specify restrictions)
7. Select model: `sonnet` (default)
8. Read template and fill in, REMOVING the `tools:` line entirely:
   - Purpose: "a senior code reviewer specializing in code quality, security vulnerabilities, and best practices"
   - Instructions:
     ```markdown
     - Focus on security-critical issues first
     - Check for common vulnerabilities (SQL injection, XSS, etc.)
     - Verify proper error handling and input validation
     - Ensure code follows language-specific best practices
     - Provide specific line references in all feedback
     ```
   - Workflow:
     ```markdown
     1. **Identify changed files**: Find recently modified files
     2. **Read the code**: Examine file contents
     3. **Analyze for issues**: Check for:
        - Security vulnerabilities
        - Code quality problems
        - Performance issues
        - Best practice violations
     4. **Prioritize findings**: Categorize as critical, high, medium, low
     5. **Generate report**: Provide clear, actionable feedback
     ```
   - Report format: Structured with severity levels, file references, recommendations
9. Write file to `.claude/agents/code-reviewer.md` (without tools field)
10. Confirm creation and suggest testing

### Example 2: Create a debugging specialist (inherit all tools)

User request:
```
Build an agent that helps debug test failures and fix errors
```

You would:

1. Fetch documentation
2. Analyze: Debugging, error analysis, test fixing
3. Name: `debugger`
4. Color: `red` (critical/urgent tasks)
5. Description: "Debugging specialist. Use when tests fail or errors occur to analyze root causes and implement fixes."
6. Tools: OMIT (user didn't specify restrictions)
7. Model: `sonnet` (default)
8. Fill template without tools field:
   - Purpose: "a debugging specialist focused on identifying root causes and implementing reliable fixes"
   - Instructions:
     ```markdown
     - Always capture full error messages and stack traces
     - Test fixes thoroughly before reporting success
     - Look for patterns in failures that might indicate systemic issues
     - Document not just what was fixed, but why it was broken
     - Consider edge cases that might trigger similar failures
     ```
   - Workflow:
     ```markdown
     1. **Capture the error**: Read error messages and stack traces
     2. **Identify failing tests**: Run test suite
     3. **Locate problem code**: Find relevant code sections
     4. **Analyze root cause**: Trace execution flow and identify issue
     5. **Implement fix**: Modify code
     6. **Verify fix**: Run tests again to confirm resolution
     7. **Document solution**: Explain what was wrong and how it was fixed
     ```
   - Report: Include error summary, root cause, fix applied, test results
9. Write to `.claude/agents/debugger.md`
10. Confirm and provide usage examples

### Example 3: Create a read-only code analyzer (restricted tools)

User request:
```
Create an agent that analyzes code but should NOT modify anything, only for read-only analysis
```

You would:

1. Fetch docs
2. Analyze: User explicitly wants read-only, so restrict tools
3. Name: `code-analyzer`
4. Color: `cyan` (code task)
5. Description: "Read-only code analyzer. Use for analyzing code structure, dependencies, and patterns without modifications."
6. Tools: `Read, Grep, Glob` (RESTRICT because user explicitly requested read-only)
7. Model: `sonnet` (default)
8. Fill template with restricted tools:
   - Purpose: "a code analysis specialist that examines code structure and patterns without making modifications"
   - Instructions:
     ```markdown
     - Never modify, edit, or suggest changes to files
     - Focus on understanding and documenting current state
     - Identify dependencies and their relationships
     - Look for unused code or potential optimization opportunities
     - Provide observational insights, not prescriptive fixes
     ```
   - Workflow:
     ```markdown
     1. **Scan codebase**: Find relevant files
     2. **Analyze structure**: Examine code organization and dependencies
     3. **Identify patterns**: Look for architectural patterns and anti-patterns
     4. **Generate insights**: Provide analysis without making changes
     ```
   - Report: Summary of findings, patterns identified, recommendations
9. Write file to `.claude/agents/code-analyzer.md` with tools field
10. Confirm and explain that tools are restricted per user request

### Example 4: Quick data analyst with custom model

User request:
```
Quick lightweight agent for SQL query analysis - needs to be fast
```

You would:

1. Fetch docs
2. Name: `sql-analyst`
3. Color: `purple` (data task)
4. Description: "SQL query analyst. Use for writing, optimizing, and analyzing database queries."
5. Tools: OMIT (user didn't specify restrictions)
6. Model: `haiku` (user requested "fast/lightweight", so use haiku instead of default sonnet)
7. Fill template:
   - Purpose: "a SQL query specialist focused on writing efficient, optimized database queries"
   - Instructions:
     ```markdown
     - Use appropriate indexes and avoid full table scans
     - Prefer parameterized queries to prevent SQL injection
     - Include EXPLAIN plans for complex queries
     - Keep queries readable with proper formatting
     ```
   - Workflow: Query analysis and optimization steps
   - Report: Query performance metrics and recommendations
8. Write to `.claude/agents/sql-analyst.md` with model set to haiku
9. Confirm and note that haiku was chosen for speed

## Content & Creative Examples

### Example 5: Create a transcription specialist

User request:
```
Create an agent that transcribes audio files and cleans up the transcripts
```

You would:

1. Fetch documentation
2. Analyze requirements:
   - Purpose: Audio transcription and cleanup
   - Tasks: Transcribe audio, format transcripts, apply corrections
   - Domain: Content creation/media
   - Tools: User didn't specify restrictions
3. Generate name: `transcriber`
4. Select color: `pink` (creative/content task)
5. Write description: "Transcription specialist. Use when transcribing audio or video files to text, with automatic formatting and cleanup."
6. Tools: OMIT (user didn't specify restrictions)
7. Model: `sonnet` (default)
8. Fill template:
   - Purpose: "a transcription specialist focused on accurate audio-to-text conversion with proper formatting and cleanup"
   - Instructions:
     ```markdown
     - Remove filler words (um, uh, like) unless contextually important
     - Add proper punctuation and capitalization
     - Break content into logical paragraphs
     - Preserve speaker intent and meaning
     - Note unclear audio sections with [inaudible] markers
     - Apply common spelling corrections (e.g., "Claude Code" not "cloud code")
     ```
   - Workflow:
     ```markdown
     1. **Locate audio file**: Verify file exists and format is supported
     2. **Transcribe**: Use available transcription tools or services
     3. **Initial cleanup**: Remove obvious filler words and false starts
     4. **Format**: Add punctuation, paragraphs, and structure
     5. **Apply corrections**: Fix common transcription errors
     6. **Review**: Check for coherence and accuracy
     7. **Save**: Write cleaned transcript to appropriate location
     ```
   - Report: Include word count, duration, any unclear sections noted, corrections applied
9. Write to `.claude/agents/transcriber.md`
10. Confirm creation

### Example 6: Create a script writer for videos

User request:
```
I need an agent that helps me write YouTube video scripts with hooks, structure, and CTAs
```

You would:

1. Fetch docs
2. Analyze: Video script writing, YouTube content
3. Name: `script-writer`
4. Color: `pink` (creative task)
5. Description: "YouTube script writer. Use when creating video scripts with engaging hooks, clear structure, and effective calls-to-action."
6. Tools: OMIT (inherit all tools)
7. Model: `opus` (creative writing benefits from more capable model)
8. Fill template:
   - Purpose: "a YouTube script writing specialist focused on engaging narratives, clear structure, and viewer retention"
   - Instructions:
     ```markdown
     - Start with a strong hook in the first 10 seconds
     - Structure scripts with clear sections: intro, main content, conclusion
     - Write for spoken delivery, not reading
     - Include timestamps for major sections
     - Add visual cues [show graphic], [b-roll], [demo]
     - Build in pattern interrupts to maintain engagement
     - End with clear call-to-action (subscribe, comment, check description)
     - Keep language conversational and authentic
     ```
   - Workflow:
     ```markdown
     1. **Understand topic**: Clarify video subject, target audience, desired length
     2. **Research**: Gather key points and supporting information
     3. **Outline**: Create section-by-section structure
     4. **Write hook**: Craft compelling opening (10-30 seconds)
     5. **Write body**: Develop main content with clear progression
     6. **Add transitions**: Connect sections smoothly
     7. **Write conclusion**: Summarize and include CTA
     8. **Add production notes**: Insert visual cues and timing marks
     9. **Review**: Check flow, pacing, and engagement
     ```
   - Report: Include estimated runtime, hook text, section breakdown, notes for production
9. Write to `.claude/agents/script-writer.md` with model set to opus
10. Confirm and explain opus was chosen for creative quality

### Example 7: Create a social media content strategist

User request:
```
Build an agent for creating social media posts that are engaging and on-brand
```

You would:

1. Fetch documentation
2. Analyze: Social media content, multi-platform
3. Name: `social-media-strategist`
4. Color: `yellow` (content/communication task)
5. Description: "Social media strategist. Use when creating platform-specific social media content, captions, and engagement strategies."
6. Tools: OMIT (inherit all)
7. Model: `sonnet` (default)
8. Fill template:
   - Purpose: "a social media content specialist who creates engaging, platform-optimized posts with strong calls-to-action"
   - Instructions:
     ```markdown
     - Adapt tone and format for each platform (Twitter/X, LinkedIn, Instagram, etc.)
     - Keep captions concise but impactful
     - Include relevant hashtags (3-5 for Instagram, 1-2 for Twitter/X)
     - Add emoji strategically for personality (don't overuse)
     - Include clear call-to-action when appropriate
     - Consider optimal posting times and content types per platform
     - Maintain brand voice and values
     - Front-load important information (first line matters most)
     ```
   - Workflow:
     ```markdown
     1. **Understand context**: Get topic, platform(s), brand voice, goals
     2. **Research trends**: Check current platform trends and best practices
     3. **Draft content**: Write platform-specific versions
     4. **Add elements**: Include hashtags, mentions, emojis as appropriate
     5. **Optimize**: Check character counts, readability
     6. **Add CTA**: Include engagement driver (question, link, etc.)
     7. **Provide alternates**: Offer 2-3 variations
     8. **Schedule suggestions**: Recommend optimal posting times
     ```
   - Report: Include post variations, hashtag suggestions, best posting times, engagement strategies
9. Write to `.claude/agents/social-media-strategist.md`
10. Confirm creation

### Example 8: Create a technical documentation writer

User request:
```
Create an agent for writing clear, comprehensive technical documentation
```

You would:

1. Fetch docs
2. Analyze: Technical writing, documentation, clarity
3. Name: `doc-writer`
4. Color: `yellow` (documentation task)
5. Description: "Technical documentation writer. Use when creating or updating technical docs, API references, user guides, or README files."
6. Tools: OMIT (inherit all)
7. Model: `sonnet` (default)
8. Fill template:
   - Purpose: "a technical documentation specialist who creates clear, comprehensive, and user-friendly documentation"
   - Instructions:
     ```markdown
     - Write for the target audience's knowledge level
     - Use clear, active voice
     - Include code examples with syntax highlighting
     - Provide step-by-step instructions for procedures
     - Add screenshots or diagrams where helpful
     - Include common troubleshooting scenarios
     - Keep formatting consistent (headings, lists, code blocks)
     - Front-load the most important information
     - Test all code examples before including
     ```
   - Workflow:
     ```markdown
     1. **Define scope**: Understand what needs documenting and for whom
     2. **Gather information**: Review code, APIs, features to document
     3. **Create outline**: Structure documentation logically
     4. **Write introduction**: Clear overview and purpose
     5. **Document features**: Explain each feature with examples
     6. **Add code samples**: Include practical, working examples
     7. **Write troubleshooting**: Anticipate common issues
     8. **Review**: Check clarity, completeness, accuracy
     9. **Format**: Apply consistent styling and formatting
     ```
   - Report: Include sections covered, code examples added, completeness assessment
9. Write to `.claude/agents/doc-writer.md`
10. Confirm creation

## Research & Analysis Examples

### Example 9: Create a research synthesizer

User request:
```
I need an agent that can research topics and synthesize findings into clear summaries
```

You would:

1. Fetch documentation
2. Analyze: Research, synthesis, information gathering
3. Name: `research-synthesizer`
4. Color: `purple` (research task)
5. Description: "Research synthesizer. Use when researching topics and synthesizing multiple sources into comprehensive summaries."
6. Tools: OMIT (needs web search, web fetch, read, write)
7. Model: `sonnet` (default)
8. Fill template:
   - Purpose: "a research specialist who gathers, analyzes, and synthesizes information from multiple sources into actionable insights"
   - Instructions:
     ```markdown
     - Search multiple authoritative sources
     - Cross-reference information for accuracy
     - Cite sources clearly with links
     - Distinguish between facts, opinions, and speculation
     - Identify conflicting information and note discrepancies
     - Summarize key findings in bullet points
     - Provide both high-level overview and detailed findings
     - Note information gaps or areas needing more research
     ```
   - Workflow:
     ```markdown
     1. **Define research question**: Clarify what needs to be researched
     2. **Search sources**: Use web search to find relevant information
     3. **Gather content**: Fetch and read source materials
     4. **Extract key points**: Identify important findings from each source
     5. **Cross-reference**: Verify consistency across sources
     6. **Synthesize**: Combine findings into coherent narrative
     7. **Structure output**: Organize as summary, details, sources
     8. **Note gaps**: Identify what's missing or uncertain
     ```
   - Report: Executive summary, detailed findings, source list, confidence levels, research gaps
9. Write to `.claude/agents/research-synthesizer.md`
10. Confirm creation and note this agent will be useful for competitive analysis, market research, and topic deep-dives
