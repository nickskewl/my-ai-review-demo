import os
import subprocess
import sys
import json
import requests
from openai import OpenAI

# Required environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
GITHUB_SHA = os.getenv("GITHUB_SHA")  # Needed for check run
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([GITHUB_TOKEN, GITHUB_REPOSITORY, GITHUB_SHA, OPENAI_API_KEY]):
    print("❌ Missing one or more required environment variables.")
    sys.exit(1)

def get_git_diff():
    result = subprocess.run(["git", "diff", "origin/main...HEAD"], capture_output=True, text=True)
    return result.stdout

def call_openai_review(diff):
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = "You're a senior engineer. For each issue found in this git diff, suggest improvement in format:\n\nFile: <filename>\nLine: <line number>\nSuggestion: <comment>"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": diff}
        ],
        max_tokens=600
    )
    return response.choices[0].message.content

def parse_to_annotations(raw_review):
    annotations = []
    for block in raw_review.strip().split("\n\n"):
        try:
            lines = block.splitlines()
            file_line = lines[0].split(":")[1].strip()
            line_num = int(lines[1].split(":")[1].strip())
            message = lines[2].split(":", 1)[1].strip()

            annotations.append({
                "path": file_line,
                "start_line": line_num,
                "end_line": line_num,
                "annotation_level": "notice",
                "message": message
            })
        except Exception:
            continue  # Skip malformed block
    return annotations[:50]  # GitHub allows up to 50 annotations per check run

def create_github_check_run(annotations):
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/check-runs"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "name": "AI Code Review",
        "head_sha": GITHUB_SHA,
        "status": "completed",
        "conclusion": "neutral",
        "output": {
            "title": "AI Code Review Suggestions",
            "summary": f"{len(annotations)} suggestion(s) found.",
            "annotations": annotations
        }
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print("✅ AI review check run created.")
    else:
        print("❌ Failed to create check run:", response.status_code, response.text)

def main():
    diff = get_git_diff()
    if not diff.strip():
        print("No changes detected.")
        return

    review = call_openai_review(diff)
    annotations = parse_to_annotations(review)
    create_github_check_run(annotations)

if __name__ == "__main__":
    main()
