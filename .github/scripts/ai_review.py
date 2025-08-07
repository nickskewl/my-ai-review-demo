from openai import OpenAI
import os
import subprocess
from github import Github

# Get environment variables
github_token = os.getenv("GITHUB_TOKEN")
repo_name = os.getenv("GITHUB_REPOSITORY")
pr_number = int(os.getenv("PR_NUMBER"))


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
        max_tokens=300
    )
    return response.choices[0].message.content


def post_comment_to_pr(review):
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(f"🤖 **AI Code Review Suggestions**\n\n{review}")


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
