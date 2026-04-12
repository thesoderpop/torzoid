# Modules and APIs

Authored by Alexis Eleanor Fagan.

## Module layout

### `torzoid-agent`
Background service process.
Responsibilities:
- lifecycle management,
- telemetry collection,
- policy execution,
- actuation dispatch,
- UI bridge.

### `torzoid-policy`
Profile-aware policy engine.
Responsibilities:
- foreground protection logic,
- reclaim candidate scoring,
- fractal scheduling decisions,
- mode-specific safety budgets.

### `torzoid-telemetry`
Telemetry adapters.
Responsibilities:
- system memory pressure collection,
- per-process metrics,
- app classification,
- burst tracing integration.

### `torzoid-store`
Durable replay/compression layer.
Responsibilities:
- checkpointing,
- journaling,
- hot/cold metadata,
- replay budget accounting,
- optional tiny-pointer object-store integration.

### `torzoid-actuator`
Action adapters.
Responsibilities:
- OS-specific reclaim operations,
- background process parking,
- service throttling,
- profile-aware action selection,
- rollback on regression.

### `torzoid-ui`
Tray/UI layer.
Responsibilities:
- show profile,
- show memory savings,
- show recent actions,
- per-app allow/block lists,
- temporary pause / safe mode toggle.

## Internal API shapes

### Telemetry event
```json
{
  "timestamp_ms": 0,
  "host": "machine-id",
  "memory_pressure": 0.0,
  "cpu_pressure": 0.0,
  "io_pressure": 0.0,
  "foreground_pid": 0,
  "foreground_name": "game.exe",
  "processes": []
}
```

### Process score input
```json
{
  "pid": 0,
  "name": "discord.exe",
  "working_set_mb": 0.0,
  "private_mb": 0.0,
  "fault_rate": 0.0,
  "background": true,
  "foreground_related": false,
  "restart_cost": 0.0,
  "user_protected": false,
  "reclaimable_cache_mb": 0.0
}
```

### Reclaim decision
```json
{
  "timestamp_ms": 0,
  "profile": "gaming",
  "reason": "memory_pressure_high",
  "actions": [
    {
      "type": "park_process",
      "target": 1234,
      "expected_ram_mb": 350,
      "risk": "low"
    }
  ]
}
```

### Scheduler budget
```json
{
  "system_budget": {
    "target_free_mb": 0,
    "max_cpu_pct": 0.0,
    "max_replay_ops_per_sec": 0.0
  },
  "class_budget": {
    "foreground_protection": "high",
    "background_reclaim": "medium"
  }
}
```

## Suggested public control API

### `GET /v1/status`
Returns current profile, pressure, recent actions, and estimated savings.

### `POST /v1/profile`
Sets active profile.

Request body:
```json
{"profile":"gaming"}
```

### `POST /v1/pause`
Pauses automatic actions.

### `POST /v1/resume`
Resumes automatic actions.

### `POST /v1/apps/protect`
Marks an app as protected.

Request body:
```json
{"match":"eldenring.exe"}
```

### `POST /v1/apps/block`
Blocks Torzoid from acting on a matched app.

### `GET /v1/actions`
Returns a recent action log.

### `GET /v1/recommendations`
Returns suggested memory-saving actions without applying them.

## Safety contract

1. No destructive action without user opt-in.
2. Protected apps may not be reclaimed except in explicit aggressive mode rules.
3. Every action must be logged and reversible where possible.
4. The policy engine must rate-limit repeated reclaim attempts.
5. Observe mode may never change system state.
