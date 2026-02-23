# TelcoCLI AI Agent

A Strands-powered AI assistant for TelcoCLI operations, providing intelligent guidance and support for AWS Telco infrastructure management.

## Features

- **Comprehensive Knowledge Base**: Automatically built from TelcoCLI codebase
- **Session Management**: Persistent conversations with unique session IDs
- **Smart Tools**: 
  - Command information and search
  - AWS error explanation and troubleshooting
  - Best practices and recommendations
- **Documentation Tagging**: Responses tagged as AWS Official, Best Practice, or Warnings
- **AWS Integration**: Respects AWS credentials and region configuration

## Installation

### Prerequisites

- Python 3.9 or higher
- AWS credentials configured
- TelcoCLI installed

### Install Dependencies

```bash
cd TelcoCLI/telcocli_agent
pip install -r requirements.txt
```

### Build Knowledge Base

The knowledge base is automatically built on first use, but you can manually build it:

```bash
cd TelcoCLI/telcocli_agent
python -m knowledge_base.builder
```

This will:
- Parse all TelcoCLI commands
- Extract documentation, parameters, and examples
- Create `knowledge_base/commands.json`
- Create `knowledge_base/aws_errors.json`

## Usage

### Command Line Interface

#### Ask a Question

```bash
telcocli ask "How do I create a VPN certificate?"
```

#### Continue a Conversation

```bash
# First question creates a session
telcocli ask "What commands are available for partners?"

# Use the session ID to continue
telcocli ask "How do I delete a partner?" --session <session-id>
```

#### List Previous Sessions

```bash
telcocli ask --list-sessions
```

#### Verbose Mode

```bash
telcocli ask "Help with dedicated hosts" --verbose
```

#### Rebuild Knowledge Base

```bash
telcocli ask "Any question" --build-kb
```

### Python API

```python
from telcocli_agent import create_agent

# Create agent
agent = create_agent(verbose=True)

# Ask a question
response = agent.ask("What commands manage VPN certificates?")
print(response)

# Get session ID for later
session_id = agent.get_session_id()

# Continue conversation
response = agent.ask("How do I revoke a certificate?", session_id=session_id)
print(response)

# List recent sessions
sessions = agent.list_sessions(limit=10)
for session in sessions:
    print(f"Session: {session['session_id']}")
    print(f"Messages: {session['total_messages']}")
```

## Architecture

```
telcocli_agent/
├── __init__.py              # Package exports
├── agent.py                 # Main TelcoCLIAgent class
├── tools.py                 # Custom Strands tools
├── session_manager.py       # Session persistence
├── requirements.txt         # Dependencies
└── knowledge_base/          # Knowledge base module
    ├── __init__.py
    ├── builder.py           # Parses codebase
    ├── loader.py            # Loads KB data
    ├── commands.json        # Generated command docs
    └── aws_errors.json      # AWS error mappings
```

## How It Works

### 1. Knowledge Base

The knowledge base builder:
- Scans `src/telco_cli/commands/` directory
- Uses AST parsing to extract command metadata
- Generates structured JSON documentation
- Includes AWS error codes and solutions

### 2. Agent

The agent uses:
- **Model**: Amazon Bedrock Claude 4 Sonnet
- **Tools**: 3 custom tools for command info, search, and error explanation
- **System Prompt**: Defines expertise and response formatting
- **Session Manager**: Tracks conversation history

### 3. Tools

Three core tools:

1. **get_command_info_tool**: Get detailed command documentation
2. **search_commands_tool**: Find commands by keyword or use case
3. **explain_aws_error_tool**: Troubleshoot AWS errors

### 4. Sessions

Sessions are stored in `~/.telcocli/sessions/` as JSON files:
- Unique UUID for each session
- Conversation history
- Tool usage tracking
- Timestamps

## Response Tags

The agent tags responses for clarity:

- `[AWS Official]` - Documented AWS behavior
- `[Best Practice]` - Experience-based recommendations
- `[WARNING]` - Security-sensitive operations
- `[Alternative]` - AWS CLI alternatives when TelcoCLI doesn't support an operation

## Configuration

### AWS Credentials

The agent respects standard AWS credential configuration:

```bash
# Environment variables
export AWS_PROFILE=my-profile
export AWS_DEFAULT_REGION=us-west-2

# Or use command flags
telcocli ask "question" --profile my-profile --region us-west-2
```

### Model Configuration

To use a different model, modify `agent.py`:

```python
from strands.models import BedrockModel

model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2",
    temperature=0.3
)

agent = TelcoCLIAgent(model=model)
```

## Examples

### Example 1: Finding Commands

```bash
$ telcocli ask "What commands help with VPN?"

Found 3 command(s) matching 'vpn':

1. telcocli create-vpn
   Create a new VPN certificate for partner access
   Category: vpn

2. telcocli list-vpn-certificates
   List all VPN certificates
   Category: vpn

3. telcocli revoke-vpn-certificate
   Revoke a VPN certificate
   Category: vpn
```

### Example 2: Command Details

```bash
$ telcocli ask "How do I use create-vpn?"

Command: telcocli create-vpn
Description: Create a new VPN certificate for partner access

Parameters:
  --partner-name (required)
    Name of the partner
  --duration (optional)
    Certificate validity duration

Example Usage:
  telcocli create-vpn --partner-name nokia --duration 90d

[Best Practice] Always verify AWS credentials are configured before running commands.
[AWS Official] Use --profile and --region flags to specify AWS configuration.
```

### Example 3: Error Troubleshooting

```bash
$ telcocli ask "I got an AccessDenied error"

[AWS Official] Error: AccessDenied

Description: IAM permissions issue - the credentials don't have required permissions

Common Causes:
  1. Missing IAM policy permissions
  2. Incorrect AWS profile selected
  3. Session token expired
  4. Resource-based policy blocking access

[Best Practice] Troubleshooting Steps:
  1. Check IAM policies attached to your user/role
  2. Verify you're using the correct AWS profile with --profile
  3. Refresh your AWS credentials if using temporary credentials
  4. Check resource-based policies (e.g., S3 bucket policies)

[AWS Official] Documentation: https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html
```

## Troubleshooting

### Agent Dependencies Not Found

```bash
Error: TelcoCLI AI agent dependencies not installed.
```

**Solution**: Install dependencies:
```bash
pip install -r telcocli_agent/requirements.txt
```

### Knowledge Base Not Found

The knowledge base is automatically built on first use. To manually rebuild:

```bash
python -m telcocli_agent.knowledge_base.builder
```

### AWS Credentials Issues

Ensure AWS credentials are configured:

```bash
aws configure
# or
export AWS_PROFILE=my-profile
```

## Development

### Adding New Tools

1. Create tool function in `tools.py`:

```python
from strands import tool

@tool
def my_new_tool(param: str) -> str:
    """Tool description for the agent.
    
    Args:
        param: Parameter description
        
    Returns:
        Result description
    """
    # Implementation
    return result
```

2. Add to `get_all_tools()`:

```python
def get_all_tools():
    return [
        get_command_info_tool,
        search_commands_tool,
        explain_aws_error_tool,
        my_new_tool  # Add here
    ]
```

### Updating Knowledge Base

After adding new commands to TelcoCLI:

```bash
python -m telcocli_agent.knowledge_base.builder
```

## Limitations

- **Guidance Only**: The agent provides guidance but does not execute commands
- **AWS Bedrock Required**: Requires access to Amazon Bedrock with Claude 4
- **Knowledge Base**: Limited to commands in TelcoCLI codebase

## Future Enhancements (v2)

- Interactive assistant mode
- Command execution capability (with user approval)
- Advanced error troubleshooting with rollback procedures
- Integration with AWS CloudTrail for error analysis
- Multi-language support

## Support

For issues or questions:
1. Check this README
2. Review TelcoCLI documentation
3. Check session logs in `~/.telcocli/sessions/`

## License

Same as TelcoCLI parent project.
