# Brainstorming

## Description

Interactive design refinement methodology for turning rough ideas into fully-formed designs through collaborative dialogue. Use this skill during creative development phases before implementation begins.

## When to Use

- Designing new features with unclear requirements
- Exploring architecture decisions
- Refining user requirements
- Breaking down complex problems
- When multiple valid approaches exist

## When NOT to Use

- Clear "mechanical" processes with known implementation
- Simple bug fixes with obvious solutions
- Tasks with explicit requirements already defined

---

## Three-Phase Process

### Phase 1: Understanding

**Goal**: Clarify requirements through sequential questioning.

**Rules**:
- Ask only ONE question per message
- If a topic needs more exploration, break it into multiple questions
- Prefer multiple-choice questions over open-ended when possible
- Wait for user response before next question

**Example**:
```
BAD: "What authentication method do you want, and should we support SSO,
      and what about password requirements?"

GOOD: "Which authentication method should we use?
       a) Username/password only
       b) OAuth (Google, GitHub)
       c) Both options"
```

### Phase 2: Exploration

**Goal**: Present alternatives with clear trade-offs.

**Process**:
1. Present 2-3 different approaches
2. Lead with the recommended option
3. Explain trade-offs for each
4. Let user choose direction

**Format**:
```markdown
## Approach 1: [Name] (Recommended)
[Description]
- Pros: [Benefits]
- Cons: [Drawbacks]

## Approach 2: [Name]
[Description]
- Pros: [Benefits]
- Cons: [Drawbacks]

Which approach aligns better with your goals?
```

### Phase 3: Design Presentation

**Goal**: Present validated design in digestible chunks.

**Rules**:
- Break design into 200-300 word sections
- Validate incrementally after each section
- Cover: architecture, components, data flow, error handling, testing
- Be flexible - allow user to request clarification or changes

**Sections to Cover**:
1. Architecture overview
2. Component breakdown
3. Data flow
4. Error handling
5. Testing considerations

---

## Core Principles

### YAGNI Ruthlessly

Remove unnecessary features aggressively:
- Question every "nice to have"
- Start with minimal viable design
- Add complexity only when justified
- "We might need this later" = remove it

### One Question at a Time

Sequential questioning produces better results:
- Gives user time to think deeply
- Prevents overwhelming with choices
- Creates natural conversation flow
- Allows follow-up on unclear points

### Multiple-Choice Preference

When possible, provide structured options:
- Reduces cognitive load
- Surfaces your understanding
- Makes decisions concrete
- Still allow "Other" option

---

## Output Format

After design validation, document to timestamped markdown:

```markdown
# Design: [Feature Name]
Date: [YYYY-MM-DD]

## Summary
[2-3 sentences]

## Architecture
[Architecture decisions]

## Components
[Component breakdown]

## Data Flow
[How data moves through system]

## Error Handling
[Error scenarios and handling]

## Testing Strategy
[Testing approach]

## Open Questions
[Any remaining unknowns]
```

---

## Post-Design Workflow

After design is validated:
1. Commit design document to version control
2. Optionally proceed to implementation
3. Use `writing-plans` skill for detailed task breakdown
4. Use `executing-plans` skill for implementation

---

## MCP Integration

This skill leverages MCP servers for enhanced brainstorming:

### Sequential Thinking (Primary)
```
Use Sequential Thinking for structured exploration:
- Track design options as thought sequences
- Build confidence in recommendations incrementally
- Allow for revisions as user provides feedback
- Document reasoning chain for design decisions
```

### Memory
```
Persist design decisions across sessions:
- Store design concepts as entities
- Create relations between components
- Recall user preferences from previous sessions
- Build project design knowledge over time
```

### Context7
```
For informed technology choices:
- Fetch current library documentation
- Compare capabilities accurately
- Ground recommendations in real data
```

---
