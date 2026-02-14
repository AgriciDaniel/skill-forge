# Proven Skill Workflow Patterns

## Pattern Selection Guide

| Pattern | Use When |
|---------|----------|
| Sequential Workflow | Steps must happen in order |
| Routing | Different inputs need different handling |
| Parallel Delegation | Independent tasks, need speed |
| Iterative Refinement | Quality improves with iteration |
| Context-Aware Selection | Same goal, different approaches by context |
| Scoring & Reporting | Need quantified analysis with priorities |
| Template Selection | Fill templates based on detected context |
| Hook-Enforced Gates | Must enforce hard rules automatically |
| Dynamic Context | Need real-time data at skill load time |
| Graceful Degradation | Tools/agents may be unavailable |
| Cross-Skill Delegation | One skill invokes another |

## Pattern 1: Sequential Workflow

Steps flow in order. Output of step N feeds into step N+1.
Each step has validation criteria and error recovery.

**Real example**: claude-seo page analysis (fetch -> parse -> analyze -> score)

## Pattern 2: Command Routing (Orchestrator)

Main skill routes to sub-skills via routing table + orchestration logic.

```markdown
## Quick Reference
| Command | Routes to |
|---------|-----------|
| /skill cmd1 | skills/skill-cmd1/SKILL.md |

## Orchestration Logic
- If command matches sub-skill, route directly
- If no command, enter interactive mode
- If ambiguous, ask for clarification
```

**Real example**: claude-seo routing 12 sub-skills (`/seo audit`, `/seo page`, etc.)

## Pattern 3: Parallel Delegation (Fan-out/Fan-in)

Spawn multiple subagents for independent analysis, then aggregate.

```markdown
1. Detect context type
2. Spawn subagents in parallel:
   - agent-1: [responsibility]
   - agent-2: [responsibility]
3. Collect results from all agents
4. Generate unified report with aggregate score
5. Create prioritized action plan
```

**Real example**: claude-seo full audit with 6 parallel agents -> Health Score (0-100)

## Pattern 4: Iterative Refinement

Generate, evaluate, improve in a loop until threshold met or max iterations.

**Real example**: Anthropic's doc-coauthoring skill
- Stage 1: Context gathering
- Stage 2: Section-by-section refinement
- Stage 3: Reader testing with sub-agent verification

## Pattern 5: Industry/Context Detection

Detect context type from signals, apply type-specific templates, thresholds,
scoring weights, and recommendations.

**Real example**: claude-seo industry detection
- SaaS: pricing page, /features, "free trial"
- E-commerce: /products, /cart, product schema
- Local: phone number, address, service area

## Pattern 6: Scoring & Reporting

Quantify analysis with weighted category scores and priority levels.

```markdown
## Scoring (0-100)
| Category | Weight |
|----------|--------|
| Category A | 30% |
| Category B | 25% |

## Priority Levels
- Critical: fix immediately
- High: fix within 1 week
- Medium: fix within 1 month
- Low: backlog
```

## Pattern 7: Template Selection

Select and fill templates based on detected context. Load from `assets/templates/`,
fill with analysis data, validate completeness.

**Real example**: claude-seo plan with 6 industry templates

## Pattern 8: Hook-Enforced Quality Gates

Use hooks to automatically enforce rules that instructions alone can't guarantee.

```yaml
hooks:
  Stop:
    - matcher: "*"
      hooks:
        - type: command
          command: "bash scripts/check-quality.sh"
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "bash scripts/lint.sh"
```

**Real example**: Anthropic's brand-guidelines (style enforcement),
webapp-testing (visual QA checks before completion)

## Pattern 9: Dynamic Context Injection

Inject real-time data into skill content at load time using `!` backtick syntax.

```markdown
Current branch: !`git branch --show-current`
Package version: !`cat package.json | jq -r '.version'`
```

Executed before skill content is sent to Claude. Useful for git-aware skills.

## Pattern 10: Graceful Degradation

Design for when tools or agents are unavailable. Always provide a sequential
fallback path for parallel delegation.

```markdown
Spawn subagents in parallel:
- agent-1: [task]
- agent-2: [task]
(If subagents unavailable, run analysis inline sequentially)
```

## Pattern 11: Cross-Skill Delegation

One skill invokes another via the Skill tool. Add `Skill(other-skill)`
to `allowed-tools`. Useful for shared toolkits.

**Real example**: Anthropic's ms-office-suite (docx, pptx, xlsx) share
an `office/` scripts directory for common operations.

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| The Monolith | Everything inlined in one SKILL.md | Split into sub-skills + references |
| Vague Directive | "Analyze and provide insights" | Specific steps, criteria, output format |
| Over-Engineered Tier 1 | Unnecessary sub-skills for simple tasks | Start simple, evolve when needed |
| Copy-Paste Skill | Duplicated content across sub-skills | Shared references in parent's references/ |
| Silent Failure | No error handling or fallbacks | "If X fails, then Y" for each step |
| AI Slop | Generic fonts, purple gradients, cliches | Explicit style bans in instructions |
| Tool Assumption | Assumes all tools always available | Check availability, provide fallbacks |
