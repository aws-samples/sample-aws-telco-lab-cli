# Slack Webhook Integration

## Setup Instructions

### 1. Create Slack Incoming Webhook

1. Go to your Slack workspace
2. Navigate to **Apps** → **Incoming Webhooks**
3. Click **Add to Slack**
4. Select the channel for notifications (e.g., `#telcocli-ci`)
5. Copy the webhook URL (format: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX`)

### 2. Add Webhook to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `SLACK_WEBHOOK_URL`
5. Value: Paste your Slack webhook URL
6. Click **Add secret**

If `SLACK_WEBHOOK_URL` is **not** set, CI still passes: Slack notify steps are skipped (no `slack-github-action` error).

Use an **Incoming Webhook** URL (`https://hooks.slack.com/services/...`) unless you have confirmed your Slack **Workflow** trigger URL (`https://hooks.slack.com/triggers/...`) accepts the same JSON payload POSTed by `slackapi/slack-github-action@v1`.

### 3. Test the Integration

Push a commit or open a PR to trigger notifications.

## Notification Events

The workflow sends Slack notifications for:

- 🔔 **PR Opened** - New pull request created
- ✅ **PR Merged** - Pull request successfully merged
- ❌ **CI Failed** - Any CI workflow fails
- ✅ **CI Passed** - CI succeeds on the `main` branch

## Customization

Edit `.github/workflows/slack-notifications.yml` to:
- Add more event types
- Customize message format
- Change notification conditions
- Add @mentions for specific events

## Example Slack Message

```
✅ Pull Request Merged
Repository: aws-samples/sample-aws-telco-lab-cli
PR: #42 - Add GitHub Actions CI/CD
Merged by: awaiz-786
Branch: feature/ci-cd → main
```

## Troubleshooting

**Notifications not appearing?**
- Verify `SLACK_WEBHOOK_URL` secret is set correctly
- Check webhook URL is valid in Slack settings
- Ensure the Slack app has permission to post to the channel
- Review GitHub Actions logs for errors
