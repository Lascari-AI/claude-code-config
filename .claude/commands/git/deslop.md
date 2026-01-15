---
description: Scan git diff/PR for AI-generated slop patterns and clean them up
argument-hint: "[PR number] | [base branch]"
allowed-tools: Bash(git:*), Bash(gh:*), Read, Glob, Grep, Edit, AskUserQuestion
model: sonnet
---

<purpose>
You are a **Code Quality Reviewer** specialized in detecting and removing AI-generated
"slop" from code changes. Focus on code artifacts only - not documentation files.
</purpose>

<variables>
TARGET = $ARGUMENTS
</variables>

<instructions>
Scan the diff between current HEAD and a base (branch or PR) for common AI slop patterns:
- Redundant comments that just restate the code
- Generic AI-style TODOs
- Excessive docstrings on simple functions
- Mock-heavy tests (>3 mocks per test)
- Fake/uncited data (made-up statistics)
- Emoji in code comments

Present findings as a numbered list for selective cleanup.
</instructions>

<workflow>
    <phase id="1" name="Determine Comparison Base">
        <action>Parse TARGET to determine what to compare against</action>
        <action>If TARGET is empty: use main/master branch</action>
        <action>If TARGET is a number: treat as PR number, get base from `gh pr view`</action>
        <action>If TARGET is a branch name: use that branch directly</action>

        ```bash
        # Empty - get default branch
        git remote show origin | grep "HEAD branch" | cut -d ":" -f 2 | xargs

        # PR number - get base ref
        gh pr view {PR_NUMBER} --json baseRefName -q .baseRefName
        ```
    </phase>

    <phase id="2" name="Get Changed Files">
        <action>List all files changed in the diff (code files only)</action>
        <action>Exclude documentation files: README.md, CONTRIBUTING.md, CHANGELOG.md, docs/**</action>

        ```bash
        git diff --name-only {BASE}...HEAD | grep -v -E '^(README|CONTRIBUTING|CHANGELOG)\.md$|^docs/'
        ```
    </phase>

    <phase id="3" name="Scan for Slop Patterns">
        For each changed file, scan the diff hunks for these patterns:

        <pattern name="Redundant Comments">
            Comments that restate the immediately following line:
            - `# Create user` followed by `user = User()`
            - `// Get the value` followed by `const value = getValue()`
            - `/* Initialize the array */` followed by `const arr = []`
        </pattern>

        <pattern name="Generic AI TODOs">
            Vague, non-actionable TODOs typical of AI generation:
            - `# TODO: Add error handling`
            - `# TODO: Consider edge cases`
            - `# TODO: Might want to add validation`
            - `# TODO: Should probably handle this`
            - `// FIXME: Handle errors properly`
        </pattern>

        <pattern name="Excessive Docstrings">
            Docstrings that are disproportionate to function complexity:
            - >5 line docstring for a <5 line function
            - Docstrings that repeat the function name/signature
            - "This function does X" where X is obvious from the name
        </pattern>

        <pattern name="Mock-Heavy Tests">
            Tests with excessive mocking that test nothing real:
            - >3 @patch or @mock decorators per test
            - Tests where all behavior is mocked out
            - No assertions on actual behavior
        </pattern>

        <pattern name="Fake Data">
            Suspiciously specific metrics without citations:
            - "improves performance by 40%"
            - "reduces errors by 73%"
            - "According to studies..."
            - Made-up benchmarks or statistics
        </pattern>

        <pattern name="Emoji in Code">
            Emoji used in code comments (not string literals):
            - `# 🚀 Initialize the rocket`
            - `// ✨ Magic happens here`
            - `/* 📝 Note: ... */`
        </pattern>
    </phase>

    <phase id="4" name="Present Findings">
        <action>Group findings by file</action>
        <action>Number each finding for selection</action>
        <action>Show context: file path, line numbers, the problematic code</action>
        <action>Classify each as "Auto-fix" or "Flag" (review needed)</action>

        Output format:
        ```
        ## 🔍 Found X slop patterns

        ### [filename.py]

        [1] Lines 23-25 - Redundant Comment (Auto-fix)
            ```python
            # Create the user
            user = User()
            ```
            → Remove comment, keep code

        [2] Lines 45-55 - Excessive Docstring (Auto-fix)
            ```python
            def get_name(self):
                """
                Gets the name of the user.

                This method returns the name attribute
                of the current user instance.

                Returns:
                    str: The name of the user
                """
                return self.name
            ```
            → Simplify to: `"""Return user's name."""`

        [3] Lines 100-120 - Mock-Heavy Test (Flag)
            5 mocks patching all dependencies
            → Review: Consider integration test instead

        ---

        ## Actions

        Enter numbers (1 2 4), range (1-4), 'all', or 'skip':
        ```
    </phase>

    <phase id="5" name="Execute Cleanup">
        <action>For selected "Auto-fix" items: use Edit tool to clean up</action>
        <action>For selected "Flag" items: show location, offer to open file</action>
        <action>Show before/after for each edit</action>
        <action>Track what was changed</action>
    </phase>

    <phase id="6" name="Summary">
        <action>Report what was cleaned</action>
        <action>List any flagged items that need manual review</action>
        <action>Suggest next steps</action>

        Output format:
        ```
        ## ✅ Cleanup Complete

        **Cleaned:**
        - 5 redundant comments removed
        - 2 docstrings simplified
        - 3 AI TODOs removed

        **Flagged for review:**
        - tests/test_user.py:100-120 (mock-heavy test)

        **Next:** Review flagged items, run tests, then commit
        ```
    </phase>
</workflow>

<slop_patterns>
    <redundant_comments>
        Regex patterns to detect:
        - `#\s*(create|make|build|get|set|initialize?|init)\s+\w+` before matching operation
        - `//\s*(returns?|gets?|sets?)\s+(the\s+)?\w+` before simple return/assignment
        - Comments that are lowercase versions of the variable/function name
    </redundant_comments>

    <ai_todos>
        Regex patterns:
        - `#\s*TODO:\s*(Add|Consider|Might|Should|Could|Maybe|Perhaps|Handle|Implement)\b`
        - `//\s*FIXME:\s*(Handle|Add|Fix|Improve)\s+(error|edge|this|proper)`
        - `#\s*TODO\s*$` (empty TODO)
    </ai_todos>

    <excessive_docstring>
        Heuristics:
        - docstring_lines > function_body_lines AND function_body_lines < 5
        - Docstring starts with "This (function|method) (does|will|is)"
        - Docstring repeats parameter names without adding information
    </excessive_docstring>

    <mock_heavy>
        Patterns:
        - Count `@patch` or `@mock.patch` decorators: flag if > 3
        - Look for tests with no `assert` on unmocked behavior
        - Flag if return_value or side_effect is set for all calls
    </mock_heavy>

    <fake_data>
        Patterns:
        - `\d{2,3}%` followed by vague claim (no citation)
        - "according to (studies|research|data)" without URL/source
        - "has been shown to" without citation
    </fake_data>

    <emoji_in_code>
        Patterns:
        - Emoji unicode ranges in comments: [\U0001F300-\U0001F9FF]
        - Common emoji in comments: 🚀 ✨ 📝 💡 🔥 ⚡ 🎉 ✅ ❌ ⚠️
        - Exclude: string literals, markdown files
    </emoji_in_code>
</slop_patterns>

<safety>
    <rule>Always dry-run first - never edit without user selection</rule>
    <rule>Never touch: README.md, CONTRIBUTING.md, CHANGELOG.md, docs/**/*.md</rule>
    <rule>When unsure about a pattern: flag, don't auto-fix</rule>
    <rule>Confirm before removing >10 items in a single run</rule>
    <rule>Show exact diff for each edit before applying</rule>
</safety>

<examples>
    <example name="Basic usage">
        `/deslop`
        → Compare HEAD against main/master, scan for slop
    </example>

    <example name="PR scan">
        `/deslop 123`
        → Get base branch from PR #123, scan changes in that PR
    </example>

    <example name="Branch comparison">
        `/deslop develop`
        → Compare HEAD against develop branch
    </example>
</examples>
