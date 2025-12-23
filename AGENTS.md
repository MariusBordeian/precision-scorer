# AI Agent Collaboration Guide

This document describes how AI coding agents (Claude, Gemini, and others) have been used in the development of the Precision Shooting Scorer application.

## Overview

This project leverages AI coding agents as development partners to:
- Design system architecture
- Research technical approaches
- Generate implementation code
- Debug and optimize algorithms
- Create documentation

## Agent Contributions

### Architecture & Design
- Analyzed requirements and use cases
- Researched ISSF target specifications
- Compared technology stacks (Python vs Rust)
- Designed multi-stage image processing pipeline
- Created detailed algorithm specifications

### Implementation Approach
- Recommended Python + OpenCV stack for rapid development
- Provided code examples for core algorithms:
  - Target detection (Hough Circle Transform)
  - Hole detection (adaptive thresholding + blob detection)
  - Scoring calculation (ISSF decimal scoring)
  - Change detection (frame differencing)
- Outlined phased development strategy

### Documentation
- Created comprehensive architecture documentation
- Wrote project README and setup guides
- Documented algorithm details with code samples

## Working with AI Agents on This Project

### Context Files
When working with AI agents on this project, provide these key files for context:
1. `README.md` - Project overview
2. `docs/ARCHITECTURE.md` - Technical architecture
3. `targets/issf_50m_rifle.json` - Target specifications
4. Example images from `examples/` folder

### Effective Prompts

#### For Architecture Questions
```
"Review the current architecture in docs/ARCHITECTURE.md and suggest 
optimizations for [specific component]"
```

#### For Implementation
```
"Implement the [module name] according to the specification in 
docs/ARCHITECTURE.md, using the algorithm described in section X"
```

#### For Debugging
```
"The hole detection is producing false positives in [scenario]. 
Here's the current code: [paste code]. Suggest improvements based 
on the architecture's multi-stage filtering approach."
```

#### For Testing
```
"Create unit tests for the scoring module that verify ISSF decimal 
scoring rules as documented in the architecture"
```

### Best Practices

1. **Reference Architecture First**: Always point agents to `docs/ARCHITECTURE.md` for design decisions
2. **Provide Examples**: Share example images when discussing detection issues
3. **Incremental Development**: Follow the phased approach outlined in the architecture
4. **Preserve Decisions**: Document architectural decisions in this folder
5. **Test-Driven**: Ask agents to generate tests alongside implementation code

## Agent-Specific Files

Individual agents may have conversation logs and notes:
- `CLAUDE.md` - Claude conversation history and contributions
- `GEMINI.md` - Gemini conversation history and contributions

## Conversation History

### Initial Architecture Analysis (Date: 2025-12-22)
**Agent**: Gemini (Antigravity)

**Topics Covered**:
- Requirements analysis
- Technology stack comparison (Python vs Rust)
- Algorithm design for all core modules
- Development timeline estimation
- Risk mitigation strategies

**Key Decisions**:
- Chose Python over Rust for faster development
- Selected OpenCV as primary CV library
- Designed multi-stage hole detection pipeline
- Recommended manual calibration fallback

**Artifacts Created**:
- `docs/ARCHITECTURE.md` - Complete technical architecture
- Initial project structure

## Tips for Future Development

### When to Consult AI Agents

✅ **Good Use Cases**:
- Designing new features (provide architecture for consistency)
- Implementing algorithms (reference existing patterns)
- Debugging complex CV issues (share images and current code)
- Optimizing performance bottlenecks (agents can suggest profiling approaches)
- Writing tests (agents excel at comprehensive test coverage)

❌ **Less Effective**:
- Very simple file operations (faster to do manually)
- Bikeshedding decisions already made (trust the architecture)
- Domain-specific shooting rules (verify with ISSF documentation)

### Managing Agent Conversations

1. **Start with Context**: Share relevant docs at conversation start
2. **Reference Prior Work**: Link to previous agent conversations if building on their work
3. **Document Decisions**: Update agent files when making significant changes
4. **Version Control**: Commit after each major agent contribution

## Agent Limitations & Human Oversight

### Known Limitations
- **No Real Testing**: Agents can't run live webcam tests - humans must validate
- **Image Quality**: Agents can view images but not process them like OpenCV
- **Performance**: Agents estimate but can't profile actual runtime
- **ISSF Rules**: Always verify scoring rules against official ISSF documentation

### Required Human Validation
- ✋ Test with actual target images
- ✋ Verify scoring accuracy against known targets
- ✋ Validate webcam integration on real hardware
- ✋ Check cross-platform compatibility
- ✋ Review ISSF rule compliance

## Contributing with AI Agents

If you're using AI agents to contribute to this project:

1. **Read the architecture first**: `docs/ARCHITECTURE.md`
2. **Check agent notes**: Review `CLAUDE.md` and `GEMINI.md` for context
3. **Document your work**: Add your conversation summary to the appropriate agent file
4. **Preserve architectural consistency**: Don't let agents contradict established designs without good reason
5. **Test thoroughly**: AI-generated code must be tested on real targets

## Questions?

For questions about AI agent collaboration on this project, refer to:
- Individual agent conversation files (`CLAUDE.md`, `GEMINI.md`)
- Architecture documentation (`docs/ARCHITECTURE.md`)
- Project README (`README.md`)

---

**Remember**: AI agents are powerful development partners, but human judgment is essential for validating computer vision algorithms against real-world target images.
