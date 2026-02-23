# How to Invoke the TelcoCLI AI Agent

> **📝 Note on Example Data**
> 
> All examples use **example AWS account IDs, session IDs, and profile names**:
> - Account IDs: `123456789012`
> - Session IDs: `550e8400-e29b-41d4-a716-446655440000`
> - Profile names: `your-profile`, `my-bedrock-profile`
> 
> Replace these with your actual values.

Complete guide on invoking and using the TelcoCLI Strands AI agent.

## Prerequisites

Before invoking the agent, ensure you have:

1. **Installed dependencies**:
```bash
cd TelcoCLI/telcocli_agent
pip install -r requirements.txt
```

2. **AWS credentials configured**:
```bash
aws configure
# or
export AWS_PROFILE=your-profile
export AWS_DEFAULT_REGION=us-west-2
```

## Method 1: Command Line Interface (Recommended)

### Basic Usage

```bash
# Ask a single question
telcocli ask "What commands are available for VPN management?"
```

### With Options

```bash
# Continue a previous conversation
telcocli ask "How do I create a VPN?" --session <session-id>

# Use verbose mode for detailed output
telcocli ask "Help with partners" --verbose

# List previous sessions
telcocli ask --list-sessions

# Rebuild knowledge base
telcocli ask "any question" --build-kb

# Use specific AWS profile/region
telcocli ask "your question" --profile prod --region us-east-1
```

### Complete CLI Syntax

```bash
telcocli ask <query> [OPTIONS]

Options:
  --session <id>        Continue a previous conversation
  --list-sessions       Show recent conversation sessions
  --verbose            Show detailed session information
  --build-kb           Rebuild knowledge base before querying
  --profile <name>     AWS profile to use
  --region <name>      AWS region to use
```

## Method 2: Python API

### Simple Usage

```python
from telcocli_agent import create_agent

# Create the agent
agent = create_agent()

# Ask a question
response = agent.ask("What commands help with VPN?")
print(response)
```

### With Session Management

```python
from telcocli_agent import create_agent

# Create agent
agent = create_agent(verbose=True)

# First question (creates new session)
response = agent.ask("What commands are available for partners?")
print(response)

# Get the session ID
session_id = agent.get_session_id()
print(f"Session ID: {session_id}")

# Continue the conversation
response = agent.ask("How do I delete a partner?", session_id=session_id)
print(response)
```

### Advanced Usage

```python
from telcocli_agent import TelcoCLIAgent, SessionManager
from strands.models import BedrockModel

# Custom configuration
session_manager = SessionManager()
model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2",
    temperature=0.3
)

# Create agent with custom settings
agent = TelcoCLIAgent(
    session_manager=session_manager,
    model=model,
    verbose=True
)

# Use the agent
response = agent.ask("Your question here")
print(response)
```

### List and Manage Sessions

```python
from telcocli_agent import create_agent

agent = create_agent()

# List recent sessions
sessions = agent.list_sessions(limit=10)
for session in sessions:
    print(f"Session: {session['session_id']}")
    print(f"Created: {session['created_at']}")
    print(f"Messages: {session['total_messages']}")
    print()

# Load a specific session
session_id = "your-session-id-here"
response = agent.ask("Continue conversation", session_id=session_id)
```

## Method 3: Direct Python Script

Create a file `my_agent_script.py`:

```python
#!/usr/bin/env python3
"""Example script to use TelcoCLI agent."""

import sys
from telcocli_agent import create_agent

def main():
    # Create agent
    agent = create_agent(verbose=True)
    
    # Get question from command line or use default
    question = sys.argv[1] if len(sys.argv) > 1 else "What commands are available?"
    
    # Ask the agent
    print(f"\nQuestion: {question}\n")
    response = agent.ask(question)
    print(f"\nAnswer:\n{response}\n")
    
    # Show session info
    session_id = agent.get_session_id()
    print(f"Session ID: {session_id}")
    print("Use this ID to continue the conversation later.")

if __name__ == "__main__":
    main()
```

Run it:
```bash
python my_agent_script.py "How do I manage VPN certificates?"
```

## Method 4: Interactive Python Session

```python
# Start Python interpreter
python

# Import and create agent
>>> from telcocli_agent import create_agent
>>> agent = create_agent(verbose=True)

# Ask questions interactively
>>> agent.ask("What commands help with outposts?")
# ... response ...

>>> agent.ask("Tell me more about describe-outpost")
# ... response ...

# Get session ID
>>> session_id = agent.get_session_id()
>>> print(session_id)
```

## Method 5: Jupyter Notebook

```python
# Cell 1: Setup
from telcocli_agent import create_agent
agent = create_agent(verbose=True)

# Cell 2: Ask questions
response = agent.ask("What commands are available for partner management?")
print(response)

# Cell 3: Continue conversation
session_id = agent.get_session_id()
response = agent.ask("How do I create a partner?", session_id=session_id)
print(response)

# Cell 4: List sessions
sessions = agent.list_sessions()
for s in sessions:
    print(f"{s['session_id']}: {s['total_messages']} messages")
```

## Common Use Cases

### 1. Find Commands

```bash
telcocli ask "What commands help with VPN?"
telcocli ask "Show me partner management commands"
telcocli ask "How do I work with dedicated hosts?"
```

### 2. Get Command Details

```bash
telcocli ask "How do I use list-partners?"
telcocli ask "What parameters does create-vpn take?"
telcocli ask "Show me an example of describe-outpost"
```

### 3. Troubleshoot Errors

```bash
telcocli ask "I got an AccessDenied error"
telcocli ask "What does InvalidParameterValue mean?"
telcocli ask "How do I fix ResourceNotFound?"
```

### 4. Learn Best Practices

```bash
telcocli ask "What's the best way to manage VPN certificates?"
telcocli ask "How should I configure partner accounts?"
telcocli ask "What are the prerequisites for EKS deployment?"
```

### 5. Multi-turn Conversations

```bash
# First question
telcocli ask "What commands manage partners?"
# Note the session ID from output

# Follow-up questions
telcocli ask "How do I create a partner?" --session <session-id>
telcocli ask "What about deleting a partner?" --session <session-id>
telcocli ask "Can I list all partners?" --session <session-id>
```

## Understanding the Output

### Response Format

```
Question: Your question here

Agent:
[Response with tagged information]

[AWS Official] - Documented AWS behavior
[Best Practice] - Recommended approach
[WARNING] - Security-sensitive operation
[Alternative] - AWS CLI alternative

Session ID: 550e8400-e29b-41d4-a716-446655440000
Use --session 550e8400-e29b-41d4-a716-446655440000 to continue this conversation
```

### Session Information (Verbose Mode)

```
Session: 550e8400-e29b-41d4-a716-446655440000
Messages: 4 | Tools used: 2
```

## Troubleshooting

### "Agent dependencies not installed"

```bash
cd TelcoCLI/telcocli_agent
pip install -r requirements.txt
```

### "AWS credentials not configured"

```bash
aws configure
# or
export AWS_PROFILE=your-profile
```

### "Knowledge base not found"

The knowledge base is built automatically on first use. To rebuild manually:

```bash
cd TelcoCLI/telcocli_agent
python -m knowledge_base.builder
```

### "Command not found: telcocli"

Ensure TelcoCLI is installed:

```bash
cd TelcoCLI
pip install -e .
```

## Tips for Best Results

1. **Be Specific**: Ask clear, specific questions
   - ✅ "How do I create a VPN certificate for partner Nokia?"
   - ❌ "VPN stuff"

2. **Use Sessions**: Continue conversations for related questions
   ```bash
   telcocli ask "What commands manage partners?"
   telcocli ask "How do I use create-partner?" --session <id>
   ```

3. **Leverage Tags**: Pay attention to response tags
   - `[AWS Official]` = Documented behavior
   - `[Best Practice]` = Recommended approach
   - `[WARNING]` = Be careful!

4. **Ask for Examples**: Request working examples
   ```bash
   telcocli ask "Show me a complete example of creating a VPN"
   ```

5. **Troubleshoot Errors**: Paste error messages
   ```bash
   telcocli ask "I got this error: AccessDenied when running list-partners"
   ```

## Quick Reference

| Task | Command |
|------|---------|
| Ask question | `telcocli ask "question"` |
| Continue conversation | `telcocli ask "question" --session <id>` |
| List sessions | `telcocli ask --list-sessions` |
| Verbose output | `telcocli ask "question" --verbose` |
| Rebuild KB | `telcocli ask "question" --build-kb` |
| Python API | `from telcocli_agent import create_agent` |

## Next Steps

- Read [QUICKSTART.md](QUICKSTART.md) for a 5-minute tutorial
- See [README.md](README.md) for complete documentation
- Try the example questions above
- Explore different command categories

Happy automating! 🚀
