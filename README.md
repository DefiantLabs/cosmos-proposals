# Cosmos Proposals Tracker

An application to create Slack notifications for new Cosmos Proposals.

## App Slack Bot Requirements

The Application will need the following configurations in a Slack Workspace App.

### Prerequisites

A Slack application will need to be created in the Workspace.

You will be following steps 1 to 3 here to setup the minimum viable Slack Application: https://api.slack.com/start/quickstart

### Scopes Required

Scopes provide Slack Apps with the necessary permissions to interact with the Slack API. Scopes are configured on the Slack App configuration page in the OAuth & Permissions section.

This application requires the following scopes:

1. channels:read
2. chat:write
3. groups:read

### Workspace Installation

The Slack App must be explicitly installed in the Workspace it is built in. This is a manual step.

### Bot Token

You will need to copy and save the Bot Token for the application. The Bot Token  Scopes can be found on the Slack App configuration page in the OAuth & Permissions section.

The Bot Token is provided to the application as an environment variable.

### Channel Install

The Slack App bot must be added to the channel you intend to have it send messages to. You must add the bot by "@"-ing the bot inside the specific channel.

### Channel ID

The Slack Channel ID must be configured in the application. This value is added in the JSON config file. You can find the Channel ID by clicking the Slack Channel dropdown while navigated to the channel looking at the bottom of the pop-up modal.
