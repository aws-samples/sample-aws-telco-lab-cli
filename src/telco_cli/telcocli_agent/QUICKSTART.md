# TelcoCLI AI Agent - Quick Start Guide

> **📝 Note on Example Data**
> 
> All examples in this guide use **example AWS account IDs and resource identifiers**:
> - Account IDs: `123456789012`, `987654321098`
> - Session IDs: `550e8400-e29b-41d4-a716-446655440000`
> - Profile names: `my-profile`, `my-bedrock-profile`
> 
> Replace these with your actual values when using the agent.

Get started with the TelcoCLI AI Agent in 5 minutes!

## Step 1: Install Dependencies

```bash
cd TelcoCLI/telcocli_agent
pip install -r requirements.txt
```

This installs:
- `strands-agents` - The Strands AI framework
- `strands-agents-tools` - Community tools
- `boto3` - AWS SDK for Python

## Step 2: Configure AWS Credentials

Ensure you have AWS credentials configured:

```bash
# Option 1: Use AWS CLI
aws configure

# Option 2: Set environment variables
export AWS_PROFILE=my-profile
export AWS_DEFAULT_REGION=us-west-2
```

## Step 3: Build Knowledge Base (Optional)

The knowledge base is automatically built on first use, but you can build it manually:

```bash
python -m knowledge_base.builder
```

Output:
```
Knowledge base saved to .../commands.json
Total commands: 23
AWS errors knowledge base saved to .../aws_errors.json
```

## Step 4: Ask Your First Question

```bash
telcocli ask "What commands are available for VPN management?"
```

The agent will:
1. Create a new session
2. Search the knowledge base
3. Provide detailed information
4. Give you a session ID for follow-up questions

## Step 5: Continue the Conversation

Use the session ID from step 4:

```bash
telcocli ask "How do I create a VPN certificate?" --session <session-id>
```

## Common Use Cases

### 1. Find Commands

```bash
telcocli ask "What commands help with partners?"
telcocli ask "How do I manage dedicated hosts?"
telcocli ask "Show me outpost commands"
```

### 2. Get Command Help

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

### 4. Best Practices

```bash
telcocli ask "What's the best way to manage partner accounts?"
telcocli ask "How should I configure VPN certificates?"
telcocli ask "What are the prerequisites for EKS deployment?"
```

## Tips

### Use Verbose Mode

See detailed session information:

```bash
telcocli ask "your question" --verbose
```

### List Previous Sessions

```bash
telcocli ask --list-sessions
```

### Rebuild Knowledge Base

After updating TelcoCLI commands:

```bash
telcocli ask "any question" --build-kb
```

### Use Specific AWS Profile/Region

```bash
telcocli ask "your question" --profile prod --region us-east-1
```

## Understanding Responses

The agent tags responses for clarity:

- **[AWS Official]** - Documented AWS behavior with links
- **[Best Practice]** - Experience-based recommendations
- **[WARNING]** - Security-sensitive operations
- **[Alternative]** - AWS CLI alternatives when needed

## Example Session

```bash
$ telcocli ask "How do I create a VPN for a partner?"

Question: How do I create a VPN for a partner?

Agent:
To create a VPN certificate for a partner, use the create-vpn command.

Command: telcocli create-vpn
Description: Create a new VPN certificate for partner access

Parameters:
  --partner-name (required)
    Name of the partner
  --duration (optional)
    Certificate validity duration (default: 90 days)

Example Usage:
  telcocli create-vpn --partner-name nokia --duration 90d

[Best Practice] Always verify AWS credentials are configured before running commands.
[AWS Official] Use --profile and --region flags to specify AWS configuration.
[WARNING] VPN certificates grant network access - ensure proper partner vetting.

Session ID: 550e8400-e29b-41d4-a716-446655440000
Use --session 550e8400-e29b-41d4-a716-446655440000 to continue this conversation

$ telcocli ask "What if the partner name is invalid?" --session 550e8400-e29b-41d4-a716-446655440000

Question: What if the partner name is invalid?

Agent:
If you provide an invalid partner name, you'll likely encounter an error. Here's how to handle it:

[Best Practice] Troubleshooting Steps:
1. List existing partners first:
   telcocli list-partners

2. Verify the partner name matches exactly (case-sensitive)

3. If the partner doesn't exist, create it first:
   telcocli create-partner --name <partner-name> --email <email>

[Alternative] You can also check partner details:
   telcocli describe-partner --name <partner-name>

Session ID: 550e8400-e29b-41d4-a716-446655440000
```

## Next Steps

1. **Explore Commands**: Ask about different command categories
2. **Practice Troubleshooting**: Try explaining different error codes
3. **Learn Best Practices**: Ask for recommendations on various operations
4. **Read Full Documentation**: See [README.md](README.md) for complete details

## Troubleshooting

### "Agent dependencies not installed"

```bash
pip install -r telcocli_agent/requirements.txt
```

### "AWS credentials not configured"

```bash
aws configure
```

### "Knowledge base not found"

```bash
python -m knowledge_base.builder
```

## Getting Help

The agent itself can help you learn how to use it:

```bash
telcocli ask "How do I use the AI agent?"
telcocli ask "What can you help me with?"
telcocli ask "Show me example questions I can ask"
```

Happy automating! 🚀
