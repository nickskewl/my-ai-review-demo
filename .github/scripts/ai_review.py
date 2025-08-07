from openai import OpenAI
import os
import subprocess
import requests
from github import Github

def get_git_diff():
    result = subprocess.run(["git", "diff", "origin/main...HEAD"], capture_output=True, text=True)
    return result.stdout

def call_openai_review(diff):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable is required")
        return None
        
    try:
        client = OpenAI(api_key=api_key)
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
    except Exception as e:
        print(f"❌ Error calling OpenAI API: {e}")
        return None

def post_comment_to_pr(review_text):
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    
    if not (token and repo_name and pr_number):
        print("❌ Missing GITHUB_TOKEN, GITHUB_REPOSITORY, or PR_NUMBER")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Use the correct GitHub API endpoint for issue comments (works for PRs)
    comment_url = f"https://api.github.com/repos/{repo_name}/issues/{pr_number}/comments"
    data = {"body": f"## 🤖 AI Code Review\n\n{review_text}"}
    
    print(f"🔍 Posting comment to: {comment_url}")
    response = requests.post(comment_url, headers=headers, json=data)

    if response.status_code == 201:
        print("✅ Successfully commented on the PR")
    else:
        print(f"❌ Failed to comment on PR: {response.status_code} {response.text}")
        print("💡 Make sure repository has 'Read and write permissions' enabled in Settings > Actions > General")

def create_check_run(review_text):
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    commit_sha = os.getenv("GITHUB_SHA")

    if not (token and repo_name and commit_sha):
        print("❌ Missing GITHUB_TOKEN, GITHUB_REPOSITORY, or GITHUB_SHA for check run")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
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

    print(f"🔍 Creating check run for commit: {commit_sha}")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        print("✅ AI review check run created.")
    else:
        print(f"❌ Failed to create check run: {response.status_code} {response.text}")
        print("💡 Make sure repository has 'checks: write' permission enabled")

def main():
    diff = get_git_diff()
    if not diff.strip():
        print("No changes detected for review.")
        return

    review = call_openai_review(diff)
    if not review:
        print("❌ Failed to generate AI review. Exiting.")
        return
        
    print("AI Review:\n", review)
    
    # Try to post comment to PR
    post_comment_to_pr(review)
    
    # Try to create check run as alternative/additional method
    create_check_run(review)

if __name__ == "__main__":
    main()
