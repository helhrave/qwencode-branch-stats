# main

Repository: sdd-metrics-0.1.0  
Branch: main  
Sessions: 1  
Observation span: 2026-09-18T08:34:17.649Z — 2026-09-18T08:38:47.354Z

## Cost by model

| Model | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---:|---:|---:|---:|---:|---:|
| routerai/qwen/qwen3.8-flash | 7 | 190,255 | 121,984 | 3,253 | 1,306 | 3.209983 |

Total cost: 3.209983

## Cost by agent

| Agent | Runs | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| Explore | 1 | 2 | 21,522 | 10,240 | 490 | 33 | 0.369342 |
| main | — | 5 | 168,733 | 111,744 | 2,763 | 1,273 | 2.840641 |

## Sessions

| Session | Title | Models | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---|---|---:|---:|---:|---:|---:|---:|
| f153466e… | — | routerai/qwen/qwen3.8-flash | 7 | 190,255 | 121,984 | 3,253 | 1,306 | 3.209983 |

## Overall usage

Requests: 7  
Input tokens: 190,255  
Cached input tokens: 121,984  
Output tokens: 3,253  
Reasoning tokens: 1,306  
Total tokens: 193,508  
API duration: 88.511 s  
Tool calls: 24  
MCP calls: 2  
Subagent runs: 1  
Tool duration: 75.185 s  
Subagent duration: 14.870 s

## Session details

### f153466e-afa7-4709-abbb-b91cfd8fc1fc

Session: f153466e-afa7-4709-abbb-b91cfd8fc1fc  
Started: 2026-09-18T08:34:17.649Z  
Ended: 2026-09-18T08:38:47.354Z  
Cost: 3.209983  
Models: routerai/qwen/qwen3.8-flash  
Agents: Explore, main  
Tool calls: 24  
MCP calls: 2  
Subagent runs: 1

## Tools

| Tool | Calls | Success | Failed | Duration |
|---|---:|---:|---:|---:|
| agent | 2 | 1 | 0 | 21.469 s |
| mcp__gitlab__get_mcp_server_version | 2 | 1 | 0 | 5.049 s |
| read_file | 12 | 5 | 1 | 27.632 s |
| run_shell_command | 6 | 3 | 0 | 14.459 s |
| tool_search | 2 | 1 | 0 | 6.576 s |

## MCP

| Server | Tool | Calls | Success | Failed | Duration |
|---|---|---:|---:|---:|---:|
| gitlab | get_mcp_server_version | 2 | 1 | 0 | 5.049 s |

## Subagents

| Agent | Runs | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| Explore | 1 | 2 | 21,522 | 10,240 | 490 | 33 | 0.369342 |

## Data quality / warnings

No warnings.
