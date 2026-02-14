# Skill Testing & Validation Guide

## Three Testing Areas

### 1. Triggering Tests
Does the skill activate at the right times?

**Should trigger (test 5-10 queries):**
- Obvious task match
- Paraphrased requests
- Domain-specific keywords
- Casual phrasing

**Should NOT trigger (test 5-10 queries):**
- Unrelated topics
- Adjacent but different domains
- General questions Claude handles natively

**Edge cases (test 3-5 queries):**
- Ambiguous requests
- Multi-domain queries
- Partial keyword matches

### 2. Functional Tests
Does the skill produce correct outputs?

**Test each workflow:**
```
Test: [Workflow Name]
Given: [Input/context]
When: Skill executes workflow
Then:
  - [Expected output 1]
  - [Expected output 2]
  - [No errors]
```

**Test error handling:**
- Invalid inputs
- Missing dependencies
- Network failures (for web-fetching skills)
- Edge cases (empty data, very large data)

### 3. Performance Comparison
Is the skill better than no skill?

**Baseline (without skill):**
- How many messages to complete task?
- How many errors/retries?
- Token usage?
- Output quality?

**With skill:**
- Should reduce messages
- Should reduce errors
- Should reduce token usage
- Should improve consistency

## Testing in Claude Code

### Manual Testing
```
# Test triggering
> [type a query that should trigger]
> [observe if skill activates]

# Test full workflow
> /skill-name [command]
> [observe output quality]
```

### Scripted Testing
Create test cases as markdown:

```markdown
## Test Case 1: Basic Trigger
Input: "Help me audit my website's SEO"
Expected: seo skill activates, asks for URL
Pass criteria: Skill loads and follows workflow

## Test Case 2: Negative Trigger
Input: "What's the weather in London?"
Expected: seo skill does NOT activate
Pass criteria: Skill stays dormant

## Test Case 3: Full Workflow
Input: "/seo page https://example.com"
Expected:
- Page fetched successfully
- SEO elements analyzed
- Score generated (0-100)
- Recommendations provided
Pass criteria: All 4 outputs present and accurate
```

## Quality Metrics

### Quantitative
| Metric | Target |
|--------|--------|
| Trigger accuracy | 90%+ on relevant queries |
| False positive rate | <5% on unrelated queries |
| Workflow completion | 95%+ without user correction |
| Error recovery | 80%+ of errors handled gracefully |

### Qualitative
- Users don't need to prompt Claude about next steps
- Workflows complete without user correction
- Consistent results across sessions
- Output matches domain expert expectations

## Pre-Publish Checklist

### Structure
- [ ] SKILL.md exists (exact case)
- [ ] Folder name = kebab-case
- [ ] Name field matches folder name
- [ ] No README.md inside skill folder

### Frontmatter
- [ ] Valid YAML with --- delimiters
- [ ] Name: kebab-case, 1-64 chars
- [ ] Description: WHAT + WHEN + keywords
- [ ] Description: under 1024 chars
- [ ] No XML tags (< >)

### Instructions
- [ ] Specific and actionable
- [ ] Error handling included
- [ ] Examples provided
- [ ] Under 500 lines
- [ ] References linked, not inlined

### Scripts (if present)
- [ ] Docstrings with purpose/input/output
- [ ] CLI interface
- [ ] Structured JSON output
- [ ] Error handling
- [ ] Can run independently

### Testing
- [ ] 5+ trigger queries pass
- [ ] 5+ negative queries don't trigger
- [ ] Each workflow tested end-to-end
- [ ] Error handling tested
- [ ] Cross-references verified

## Iteration Signals

### Under-triggering (skill doesn't load)
- Add more trigger phrases to description
- Add domain keywords
- Make description more specific (counterintuitively)
- Add common paraphrases

### Over-triggering (skill loads incorrectly)
- Add negative triggers ("Do NOT use for...")
- Narrow the description scope
- Add disambiguation phrases

### Execution issues
- Add validation gates between steps
- Add "if X fails, then Y" paths
- Consider scripts for fragile operations
- Add more specific instructions (replace vague language)
