from openai import OpenAI
import os
import subprocess
from github import Github
import requests
import sys

# Get environment variables with error handling
github_token = os.getenv("GITHUB_TOKEN")
repo_name = os.getenv("GITHUB_REPOSITORY") 
pr_url = os.getenv("PR_URL")

# Validate required environment variables
if not github_token:
    print("❌ Error: GITHUB_TOKEN environment variable is required")
    sys.exit(1)

if not repo_name:
    print("❌ Error: GITHUB_REPOSITORY environment variable is required")
    sys.exit(1)

if not pr_url:
    print("❌ Error: PR_URL environment variable is required")
    sys.exit(1)

# Get PR number from environment or extract from URL
pr_number_env = os.getenv("PR_NUMBER")
if pr_number_env:
    try:
        pr_number = int(pr_number_env)
    except ValueError:
        print(f"❌ Error: Invalid PR_NUMBER environment variable: {pr_number_env}")
        sys.exit(1)
else:
    # Fallback: extract PR number from PR_URL
    try:
        pr_number = int(pr_url.split('/')[-1])
    except (ValueError, IndexError):
        print(f"❌ Error: Could not extract PR number from PR_URL: {pr_url}")
        sys.exit(1)

print(f"📝 Processing PR #{pr_number} for repository {repo_name}")


def get_git_diff():
    result = subprocess.run(["git", "diff", "origin/main...HEAD"], capture_output=True, text=True)
    return result.stdout


def call_openai_review(diff):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        sys.exit(1)
    
    try:
        client = OpenAI(api_key=openai_api_key)
        system_prompt = "You are a senior software engineer. Review the following GitHub pull request diff for potential bugs, code smells, style issues, and offer constructive suggestions."
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": diff}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error calling OpenAI API: {e}")
        sys.exit(1)


def post_comment_to_pr(review):
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }
    comment_url = f"{pr_url}/comments"
    data = {"body": f"## 🤖 AI Code Review\n\n{review}"}

    response = requests.post(comment_url, headers=headers, json=data)
    if response.status_code == 201:
        print("✅ AI review comment posted to PR.")
    else:
        print("❌ Failed to post comment:", response.status_code, response.text)


def main():
    diff = get_git_diff()
    if not diff.strip():
        print("No changes detected for review.")
        return

    review = call_openai_review(diff)
    print("AI Review:\n", review)
    post_comment_to_pr(review)


if __name__ == "__main__":
    main()
