from openai import OpenAI
import os
import subprocess
import requests
from github import Github

def get_git_diff():
    result = subprocess.run(["git", "diff", "origin/main...HEAD"], capture_output=True, text=True)
    return result.stdout

def call_openai_review(diff):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system_prompt = "You are a senior software engineer. Review the following GitHub pull request diff for potential bugs, code smells, style issues, and offer constructive suggestions."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": diff}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content

def post_comment_to_pr(review_text):
    token = os.getenv("GITHUB_TOKEN")
    pr_url = os.getenv("PR_URL")
    if not (token and pr_url):
        print("❌ Missing GITHUB_TOKEN or PR_URL")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    comment_url = f"{pr_url}/comments"
    response = requests.post(comment_url, headers=headers, json={"body": review_text})

    if response.status_code == 201:
        print("✅ Successfully commented on the PR")
    else:
        print(f"❌ Failed to comment on PR: {response.status_code} {response.text}")

def create_check_run(review_text):
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    commit_sha = os.getenv("GITHUB_SHA")

    if not (token and repo_name and commit_sha):
        print("❌ Missing GITHUB_TOKEN, GITHUB_REPOSITORY, or GITHUB_SHA")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    url = f"https://api.github.com/repos/{repo_name}/check-runs"
    payload = {
        "name": "AI Code Review",
        "head_sha": commit_sha,
        "status": "completed",
        "conclusion": "neutral",
        "output": {
            "title": "AI Review Suggestions",
            "summary": review_text[:65535]  # Limit output size
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        print("✅ AI review check run created.")
    else:
        print(f"❌ Failed to create check run: {response.status_code} {response.text}")

def main():
    diff = get_git_diff()
    if not diff.strip():
        print("No changes detected for review.")
        return

    review = call_openai_review(diff)
    print("AI Review:\n", review)

    post_comment_to_pr(review)
    create_check_run(review)

if __name__ == "__main__":
    main()
