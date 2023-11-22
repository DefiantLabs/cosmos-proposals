# App Design

## Overview

The Slack bot application works in the following manner:

1. Watches particular blockchains configured at startup time
2. Connects to a particular Slack channel ID for notification sending
3. Requests active proposals on the configured blockchains
4. Sends notifications for new active proposals
5. Keeps track of previously send notifications to prevent duplicates

## System

### Python Slack API

The application is built using Python [Slack SDK](https://slack.dev/python-slack-sdk/), Slack's official Python development framework for building Slack Bots.

It provides convenient wrappers around the methods needed to interact with the Slack Application and APIs, including installation, authentication, permissions and events.

### Datastore Backing

The application uses [MongoDB](https://pymongo.readthedocs.io/en/stable/index.html) to store required information in a database.

It stores the following information:

1. Channels: Slack channels configured in the application. These are used to track which proposal notifications have been sent to prevent duplicates.
2. Chains: Blockchain values that the application has watched.
3. Proposals: On-chain Active Proposals that have been seen by the application. These are used to keep track of which proposal notifications have been sent to channels.

### Chain Registry

The application uses the [Cosmos Chain Registry](https://github.com/cosmos/chain-registry) to interact with chain REST servers and receive data required by the application.

The application requests data on active proposals on the blockchain.

### Infrastructure

The application will be built with an application server and a database backend. It will be deployed on a bot-specific basis with environment configurations pointing to different channels in a Slack workspace.
