# Syncplay Fork - Ready System Removed

This is a fork of Syncplay that removes the ready system. All users will always appear as ready to other users, regardless of their actual ready state.

## What's Changed

### Core Changes
- **Always Ready**: All users appear as ready at all times
- **Hidden UI**: Ready button and ready indicators are hidden from the interface
- **Disabled Commands**: Ready-related console commands are disabled but show informative messages
- **Protocol Compatible**: Maintains compatibility with standard Syncplay servers and clients

### Technical Details

#### Client-side Changes (`syncplay/client.py`)
- `SyncplayUser.isReady()` - Always returns `True`
- `SyncplayUser.isReadyWithFile()` - Returns `True` when file present, `None` when no file
- `SyncplayUser.setReady()` - Does nothing (no-op)
- `SyncplayUserlist.areAllUsersInRoomReady()` - Always returns `True`
- `SyncplayUserlist.areAllOtherUsersInRoomReady()` - Always returns `True`
- `SyncplayUserlist.areAllRelevantUsersInRoomReady()` - Always returns `True`
- `SyncplayUserlist.readyUserCount()` - Returns total user count (everyone is ready)
- `SyncplayUserlist.usersInRoomNotReady()` - Returns empty string
- `SyncplayUserlist.isReady()` - Always returns `True`
- `SyncplayUserlist.isReadyWithFile()` - Always returns `True`
- `SyncplayUserlist.setReady()` - Does nothing (no-op)
- `toggleReady()` and `changeReadyState()` - Do nothing (no-op)
- `_toggleReady()` - Simplified to handle only pause/unpause without ready state changes

#### Server-side Changes (`syncplay/server.py`)
- `Watcher.isReady()` - Always returns `True`
- `Watcher.setReady()` - Does nothing (no-op)

#### GUI Changes (`syncplay/ui/gui.py`)
- Ready button is hidden (`setVisible(False)`)
- Ready indicators always show as ready in user list
- `changeReadyState()` - Does nothing (no-op)
- `updateReadyState()` - Hides ready button

#### Console UI Changes (`syncplay/ui/consoleUI.py`)
- Ready toggle command (`t`) shows informative message
- Set ready commands (`sr`, `snr`) show informative message  
- User list always shows users as ready

## Compatibility

### With Standard Syncplay Users
- **Users without this fork**: Will always see you as ready
- **You see other users**: Always appear as ready to you
- **Synchronization**: Works normally (pause/play/seek still sync)
- **Autoplay**: Functions normally since everyone appears ready

### With Standard Syncplay Servers
- **Full compatibility**: Connects to any Syncplay server normally
- **Protocol intact**: All network communication works as expected
- **No server changes needed**: Works with existing Syncplay infrastructure

## Why This Fork?

The ready system can sometimes be annoying or unnecessary in certain use cases:
- **Private sessions**: Where all participants are always ready
- **Automated setups**: Where ready state management is not needed
- **Simplified usage**: For users who find the ready system confusing
- **Always-on scenarios**: Where media should play regardless of ready state

## Installation

1. Clone this fork: `git clone <this-repository>`
2. Install normally following standard Syncplay installation instructions
3. The ready system changes are automatically active

## Testing

Run the included test script to verify the changes:
```bash
python test_ready_fork.py
```

## Original Syncplay

This fork is based on the original Syncplay project. For the standard version with the ready system intact, visit: https://github.com/Syncplay/syncplay

## License

Same license as the original Syncplay project.