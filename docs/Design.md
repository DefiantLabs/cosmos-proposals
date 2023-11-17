# App Design

## System

### Bolt

The application is built using Node [Bolt](https://api.slack.com/bolt), Slack's official Javascript framework for building Slack Applications.

It provides convenient wrappers around the methods needed to interact with the Slack Application and APIs, including installation, authentication, permissions and events.

### Datastore Backing

The application uses [Sequelize](https://sequelize.org/docs/v6/getting-started/) to store required information in a relational database.

### Chain Registry

The application uses the [Cosmos Chain Registry](https://github.com/cosmos/chain-registry) to interact with chain RPC servers and receive data required by the application.

### Infrastructure

The application will be built with an application server and a database backend. It will be available at a Redirect URL that will be specified when creating the Application in the Slack registry. This will make it available for Slack to make requests to based on user interaction.

## Commands

The application provides a few [Slack Slash Commands](https://api.slack.com/interactivity/slash-commands) to interact with the application Bot.

### `watch-proposals`

The `/watch-proposals` command will allow users to receive proposal notifications for the specified chains.

#### Text Parameters

The command will take in the following paramters in the `text` portion of the command:

```
<chain name>
```

#### Validations

The application will ensure that the chain specified in the text parameter exists in the chain registry.

#### Data Stored/Cleared

The application will store the following information for use when this command is received:

1. Workspace, Channel and User metadata - for use in identifying the watcher and sending notifications
2. Chain name - for use in proposal watching on the specified chain

#### Effects

The application will store the above information. During the main loop of the application, it will periodically watch the chains stored in the database for new Cosmos Proposals. It will push notifications to the Slack channel specified when a new Active Proposal is found.

#### Example Usage

```
/watch-proposals cosmoshub
```

### `/unwatch-proposals`

The `/unwatch-proposals` command will allow users to turn off text notifications for a specified chain.

#### Text Parameters

The command will take in the following paramters in the `text` portion of the command:

```
<chain name>
```

#### Validations

The application will ensure that the chain specified in the text parameter exists in the application datastore for the requesting channel.

#### Data Stored/Cleared

This command will clear data stored for the requesting channel.

### Effects

The application will no longer send notifications for the specified chain.

#### Example Usage

```
/unwatch-proposals cosmoshub
```

### `/unwatch-all-proposals`

The `/unwatch-all-proposals` command will allow users to turn off text notifications for an entire channel.

#### Text Parameters

None.

#### Validations

The application will ensure the requesting channel actually has chains being watched.

#### Data Stored/Cleared

This command will clear data stored for the requesting channel.

### Effects

The application will no longer send notifications for any chains previously watched.

#### Example Usage

```
/unwatch-all-proposals
```