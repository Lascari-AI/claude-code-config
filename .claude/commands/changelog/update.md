---
description: Update CHANGELOG.md from git commits - transforms technical commits into user-friendly entries
argument-hint: "[PR#] | [tag..HEAD] | [7d/2w] | (empty for auto)"
allowed-tools: Read, Write, Edit, Bash(git:*), Bash(gh:*), Glob, Grep, AskUserQuestion
model: sonnet
---

# Changelog Update

> Knowledge: `.claude/skills/changelog/SKILL.md` - changelog conventions and format

<purpose>
Update CHANGELOG.md by analyzing git commits and transforming technical changes
into user-friendly changelog entries. Focus on user-facing impact, not implementation.
</purpose>

<variables>
TARGET = $ARGUMENTS
CHANGELOG_PATH = CHANGELOG.md
</variables>

<workflow>
    <phase id="1" name="determine_range">
        <description>Figure out which commits to analyze</description>
        <actions>
            <action>Parse TARGET to determine commit range</action>
            <action>
                **If TARGET is empty:**
                - Look for existing CHANGELOG.md and find last version tag
                - If no changelog: use all commits since first commit or last 2 weeks
                - If has versions: use commits since last tagged version
            </action>
            <action>
                **If TARGET is a PR number (digits only):**
                ```bash
                gh pr view {TARGET} --json commits,title,body -q '.commits[].oid'
                ```
            </action>
            <action>
                **If TARGET is a range (contains `..'):**
                Use directly: `git log {TARGET} --oneline`
            </action>
            <action>
                **If TARGET is time-based (7d, 2w, 1m):**
                ```bash
                git log --since="{N} days ago" --oneline
                ```
            </action>
        </actions>
        <output>
            Store: COMMIT_RANGE (e.g., "v1.2.0..HEAD" or list of SHAs)
        </output>
    </phase>

    <phase id="2" name="gather_commits">
        <description>Get commit details for analysis</description>
        <actions>
            <action>
                Get commit messages with conventional commit parsing:
                ```bash
                git log {COMMIT_RANGE} --pretty=format:"%H|%s|%b---END---"
                ```
            </action>
            <action>
                Parse each commit into:
                - SHA
                - Type (feat/fix/perf/etc from prefix)
                - Scope (if present in parentheses)
                - Description
                - Body (if present)
            </action>
        </actions>
    </phase>

    <phase id="3" name="filter_and_categorize">
        <description>Determine which commits are user-facing</description>
        <decision_framework>
            <include>
                - `feat:` → Features
                - `fix:` → Fixes
                - `perf:` → Improvements (if user-noticeable)
                - Breaking changes (from body or `!` suffix) → Breaking Changes
                - Security fixes → Security
            </include>
            <exclude>
                - `refactor:` - internal restructuring
                - `test:` - test changes
                - `chore:` - maintenance
                - `style:` - formatting
                - `docs:` - unless user-facing documentation
                - `ci:` - pipeline changes
                - `build:` - build system
            </exclude>
        </decision_framework>
        <actions>
            <action>Group commits by category</action>
            <action>Identify commits that should be merged (multiple commits for one feature)</action>
        </actions>
    </phase>

    <phase id="4" name="transform_entries">
        <description>Convert technical commits to user-friendly entries</description>
        <principles>
            1. **Lead with benefit** - What can users do now?
            2. **Use user language** - Avoid technical jargon
            3. **Be specific when helpful** - "Fixed login on Safari" not "Fixed browser bug"
            4. **Bold feature names** - **Dark Mode**: Description...
            5. **Keep it brief** - One line per entry when possible
        </principles>
        <actions>
            <action>
                For each included commit, draft user-friendly text:

                Technical: `feat(auth): add JWT middleware with refresh tokens`
                User-friendly: **Secure Sessions**: Added automatic session refresh for uninterrupted use

                Technical: `fix: resolve race condition in checkout flow`
                User-friendly: Fixed an issue where orders could occasionally fail during checkout
            </action>
        </actions>
    </phase>

    <phase id="5" name="present_draft">
        <description>Show proposed changes for approval</description>
        <actions>
            <action>
                Present the draft changelog entries:
                ```markdown
                ## Proposed Changelog Entries

                Based on {N} commits ({range}):

                ### Features
                - **Feature Name**: Description

                ### Improvements
                - Improvement description

                ### Fixes
                - Fixed issue description

                ---

                **Excluded** ({M} commits):
                - refactor: internal restructuring (3 commits)
                - chore: dependency updates (2 commits)
                ```
            </action>
            <action>
                Ask for confirmation:
                1. Accept as-is
                2. Edit entries
                3. Include more commits
                4. Cancel
            </action>
        </actions>
    </phase>

    <phase id="6" name="update_changelog">
        <description>Apply approved entries to CHANGELOG.md</description>
        <actions>
            <action>
                **If CHANGELOG.md exists:**
                - Read current content
                - Find `[Unreleased]` section (or create one)
                - Merge new entries into appropriate categories
                - Preserve existing entries
            </action>
            <action>
                **If CHANGELOG.md doesn't exist:**
                - Create with standard header
                - Add `[Unreleased]` section with new entries
            </action>
            <action>
                Use Edit tool to update the file
            </action>
        </actions>
        <format>
            ```markdown
            # Changelog

            All notable changes to this project are documented in this file.

            ## [Unreleased]

            ### Features

            - **New Feature**: What users can now do

            ### Improvements

            - What got better

            ### Fixes

            - What was broken and is now fixed

            ---

            ## [Previous versions below...]
            ```
        </format>
    </phase>

    <phase id="7" name="summary">
        <description>Report what was done</description>
        <output>
            ```markdown
            ## Changelog Updated

            **Range analyzed**: {commit range}
            **Commits included**: {N} of {total}

            ### Added to [Unreleased]
            - Features: {count}
            - Improvements: {count}
            - Fixes: {count}

            ### Next Steps
            1. Review CHANGELOG.md for accuracy
            2. Commit the changelog update
            3. (Before release) Move entries to versioned section
            ```
        </output>
    </phase>
</workflow>

<examples>
    <example name="After PR merge">
        `/changelog:update 142`
        → Analyze commits from PR #142, add user-facing changes to [Unreleased]
    </example>

    <example name="Since last release">
        `/changelog:update v2.1.0..HEAD`
        → All commits since v2.1.0 tag
    </example>

    <example name="Recent changes">
        `/changelog:update 7d`
        → Last 7 days of commits
    </example>

    <example name="Auto-detect">
        `/changelog:update`
        → Automatically determine range from existing changelog/tags
    </example>
</examples>

<important_rules>
    1. Never include internal changes (refactor, test, chore) unless they have user impact
    2. Always present draft for approval before updating the file
    3. Preserve existing changelog content - merge, don't replace
    4. Use consistent formatting matching existing changelog style
    5. Bold feature names for scannability
</important_rules>
