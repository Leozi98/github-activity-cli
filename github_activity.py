import sys
import json
import argparse
import sqlite3
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta
from collections import defaultdict
import yaml  # Optional: pip install pyyaml

class GitHubActivityAdvanced:
    def __init__(self):
        self.cache_db = "github_activity.db"
        self._init_cache()
    
    def _init_cache(self):
        """Initialize SQLite cache database"""
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS activities
                         (username TEXT, data TEXT, timestamp DATETIME)''')

    def _get_cached_activities(self, username):
        """Get cached activities if within 10 minutes"""
        with sqlite3.connect(self.cache_db) as conn:
            cursor = conn.execute('''SELECT data FROM activities 
                                   WHERE username = ? AND 
                                   timestamp >= datetime('now', '-10 minutes')''',
                                (username,))
            result = cursor.fetchone()
            return json.loads(result[0]) if result else None

    def _cache_activities(self, username, data):
        """Store activities in cache"""
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute('DELETE FROM activities WHERE username = ?', (username,))
            conn.execute('INSERT INTO activities VALUES (?, ?, datetime("now"))',
                        (username, json.dumps(data)))

    def fetch_activities(self, username, token=None, use_cache=True):
        """Fetch activities with caching support"""
        if use_cache:
            cached = self._get_cached_activities(username)
            if cached:
                return cached

        url = f"https://api.github.com/users/{username}/events"
        headers = {'User-Agent': 'GitHub-Activity-CLI/2.0'}
        
        if token:
            headers['Authorization'] = f"token {token}"

        try:
            req = Request(url, headers=headers)
            with urlopen(req) as response:
                data = json.loads(response.read().decode())
                if use_cache:
                    self._cache_activities(username, data)
                return data
        except HTTPError as e:
            print(f"API Error: {e.code} {e.reason}")
            if e.headers.get('X-RateLimit-Remaining') == '0':
                reset_time = datetime.fromtimestamp(int(e.headers.get('X-RateLimit-Reset')))
                print(f"Rate limit exceeded. Reset at {reset_time}")
            sys.exit(1)
        except URLError as e:
            print(f"Connection Error: {e.reason}")
            sys.exit(1)

    def filter_activities(self, activities, filters):
        """Filter activities by type and/or repository"""
        filtered = []
        for activity in activities:
            event_type = activity.get('type')
            repo = activity.get('repo', {}).get('name', '')
            
            type_match = not filters.get('types') or event_type in filters['types']
            repo_match = not filters.get('repos') or repo in filters['repos']
            
            if type_match and repo_match:
                filtered.append(activity)
        return filtered

    def enrich_activity(self, activity):
        """Add additional information from other API endpoints"""
        repo_url = f"https://api.github.com/repos/{activity['repo']['name']}"
        try:
            with urlopen(Request(repo_url, headers={'User-Agent': 'GitHub-Activity-CLI'})) as response:
                repo_data = json.loads(response.read().decode())
                activity['repo_details'] = {
                    'stars': repo_data.get('stargazers_count'),
                    'forks': repo_data.get('forks_count'),
                    'description': repo_data.get('description')
                }
        except Exception as e:
            activity['repo_details'] = {'error': str(e)}
        return activity

    def format_output(self, activities, output_format='text', color=False):
        """Format output in different formats"""
        if output_format == 'json':
            return json.dumps(activities, indent=2)
        
        if output_format == 'yaml':
            return yaml.dump(activities, allow_unicode=True)
            
        if output_format == 'table':
            return self._format_table(activities, color)
        
        return self._format_text(activities, color)

    def _format_text(self, activities, color):
        """Text formatting with optional colors"""
        output = []
        colors = {
            'PushEvent': '\033[92m',
            'PullRequestEvent': '\033[94m',
            'IssuesEvent': '\033[93m',
            'reset': '\033[0m'
        }
        
        for act in activities:
            line = f"- {act['type']}: {act.get('message', '')}"
            if color and act['type'] in colors:
                line = f"{colors[act['type']]}{line}{colors['reset']}"
            output.append(line)
        return '\n'.join(output)

    def _format_table(self, activities, color):
        """Table formatting with columns"""
        table = ["\n| Date | Type | Repository | Details |",
                "|------|------|------------|---------|"]
        for act in activities:
            date = datetime.strptime(act['created_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M")
            row = f"| {date} | {act['type']} | {act['repo']['name']} | {act.get('message', '')} |"
            table.append(row)
        return '\n'.join(table)

def main():
    parser = argparse.ArgumentParser(description='Advanced GitHub Activity CLI')
    parser.add_argument('username', help='GitHub username')
    parser.add_argument('-l', '--limit', type=int, default=10, help='Number of activities to display')
    parser.add_argument('-t', '--token', help='GitHub personal access token')
    parser.add_argument('-f', '--format', choices=['text', 'json', 'yaml', 'table'], default='text')
    parser.add_argument('--types', nargs='+', help='Filter by event types (e.g., PushEvent IssuesEvent)')
    parser.add_argument('--repos', nargs='+', help='Filter by repositories')
    parser.add_argument('--no-cache', action='store_false', help='Disable caching')
    parser.add_argument('--color', action='store_true', help='Enable colored output')
    parser.add_argument('--enrich', action='store_true', help='Enrich with repo details')
    
    args = parser.parse_args()
    
    github = GitHubActivityAdvanced()
    
    try:
        # Fetch and process data
        activities = github.fetch_activities(args.username, args.token, args.no_cache)
        filtered = github.filter_activities(activities, {
            'types': args.types,
            'repos': args.repos
        })[:args.limit]
        
        # Optional data enrichment
        if args.enrich:
            filtered = [github.enrich_activity(a) for a in filtered]
        
        # Format output
        output = github.format_output(filtered, args.format, args.color)
        print(output)
        
    except json.JSONDecodeError:
        print("Error processing API response")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
