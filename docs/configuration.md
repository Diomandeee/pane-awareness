# Configuration Reference

pane-awareness uses a layered configuration system with sensible defaults. Most users won't need a config file at all.

## Config File Locations

Loaded in priority order (first found wins):

1. **Environment variable**: `PANE_AWARENESS_CONFIG=/path/to/config.toml`
2. **Project-local**: `.pane-awareness.toml` in current working directory
3. **User-global**: `~/.config/pane-awareness/config.toml`
4. **Built-in defaults**: No file needed

Config files support TOML (Python 3.11+) with JSON fallback for Python 3.9-3.10.

## Full Reference

```toml
[general]
# Directory for state files (pane_registry.json, pane_claims.json, etc.)
# Default: ~/.config/pane-awareness/state
state_dir = ""

# Hours of inactivity before a pane is considered stale
stale_hours = 2.0

# Extra words to filter from topic extraction (your username, hostname, etc.)
# These are auto-detected from $USER and $HOME, but you can add more
identity_noise_extra = []

# Base directories for project name extraction
# When a pane's CWD is under one of these, the immediate subdirectory is the project name
project_base_dirs = ["~/projects", "~/Desktop", "~/src", "~/code", "~/work"]

[topics]
# Maximum number of topics to extract per prompt
max_topics = 8

# Size of the rolling topic trajectory window
trajectory_window_size = 10

# Additional stop words to filter (beyond the built-in ~80)
extra_stop_words = []

[convergence]
# Initial convergence threshold (auto-adjusted by the calibration engine)
threshold = 0.8

# Bounds for auto-calibration
threshold_min = 0.6
threshold_max = 0.95
threshold_step = 0.05

# Minutes before a prediction expires without resolution
prediction_ttl_min = 60

# Maximum stored predictions
predictions_cap = 50

# Minutes after resolution before a prediction is considered resolved
resolution_window_min = 5

[claims]
# Minutes before a contested claim can be force-released
contest_timeout_min = 5

# Maximum entries in the claims log
log_cap = 200

[messages]
# Maximum entries in the message log
log_cap = 500

# Maximum read messages stored per pane
read_cap = 100

[quadrant]
# Terminal detection method: auto, terminal, iterm2, linux
# "auto" tries Terminal.app, then iTerm2, then xdotool
terminal = "auto"

[domains]
# Map domain names to topic keywords for proximity detection
# Uncomment and customize for your project:
#
# auth = ["authentication", "login", "jwt", "oauth", "session", "token"]
# database = ["sql", "migration", "schema", "query", "postgres", "mysql"]
# api = ["endpoint", "rest", "graphql", "route", "handler"]
# frontend = ["react", "component", "css", "layout", "form"]
# testing = ["test", "e2e", "playwright", "jest", "mock"]
# infra = ["docker", "kubernetes", "ci", "deploy", "nginx"]

# Port-to-domain mapping for claim inference
# When a claim is on "port:8000", it maps to the corresponding domain
# [domains.ports]
# 3000 = "frontend"
# 5432 = "database"
# 8000 = "api"
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PANE_AWARENESS_CONFIG` | Path to config file |
| `PANE_AWARENESS_STATE_DIR` | Override state directory (takes precedence over config) |
| `VAULT_PATH` | Obsidian vault path (for vault_writer extension) |

## JSON Config (Python 3.9-3.10)

If TOML is not available, you can use JSON:

```json
{
  "general": {
    "state_dir": "",
    "stale_hours": 2.0
  },
  "topics": {
    "max_topics": 8
  },
  "convergence": {
    "threshold": 0.8
  },
  "domains": {
    "auth": ["authentication", "login", "jwt"]
  }
}
```

Save as `.pane-awareness.json` alongside where you'd put the `.toml` file.
