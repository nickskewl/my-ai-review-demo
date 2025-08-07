import openai
import os
import subprocess

def get_git_diff():
    result = subprocess.run(["git", "diff", "origin/main...HEAD"], capture_output=True, text=True)
    return result.stdout

def call_openai_review(diff):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    system_prompt = "You are a senior software engineer. Review the following Git diff and provide feedback."
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": diff}
        ]
    )
    return response['choices'][0]['message']['content']

def main():
    diff = get_git_diff()
    if not diff.strip():
        print("No changes detected for review.")
        return

    review = call_openai_review(diff)
    print("AI Review:\n", review)

if __name__ == "__main__":
    main()