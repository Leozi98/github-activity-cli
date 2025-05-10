# GitHub Activity CLI - Advanced Version


## Features

### Key Features
- 🗃️ **Caching System**: Local activity data storage for 10 minutes
- 🔍 **Advanced Filtering**:
  - Filter by event types (PushEvent, IssuesEvent, etc.)
  - Filter by specific repositories
- 📤 **Multi-Format Output**:
  - Text (default)
  - JSON
  - YAML
  - Formatted table
- 💎 **Data Enrichment**: Additional repository details (stars, forks, description)
- 🎨 **Colored Output**: Terminal color support
- ⚠️ **Rate Limit Handling**: Detailed API rate limit information
- 🔑 **Token Authentication**: GitHub Personal Access Token support

## Installation

```bash
#Install dependencies (YAML support optional)
pip install pyyaml
```
### Basic Command
```BASH
python github_activity.py <username> [options]
```
### Example Commands
Table format with colors
```bash
python github_activity.py microsoft --format table --color --limit 5 
```
### JSON output with PushEvent filter
```bash
python github_activity.py torvalds --format json --types PushEvent
```
### Repository-specific activities with enrichment
```bash
python github_activity.py google --repos google/go-cloud --enrich
```
### YAML output without caching
```bash
python github_activity.py facebook --format yaml --no-cache
```
https://roadmap.sh/projects/github-user-activity

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
