import requests
import json
from decouple import config
import os


GITHUB_SECRET = config("GITHUB_SECRET")
GITHUB_USER = input("Enter github username: ")


def get_repos(user):
    r = requests.get(
        f"https://api.github.com/users/{user}/repos", auth=(GITHUB_USER, GITHUB_SECRET)
    )
    user_token_expire = int(
        requests.get(
            f"https://api.github.com/users/{user}", auth=(GITHUB_USER, GITHUB_SECRET)
        ).headers["X-RateLimit-Remaining"]
    )
    if user_token_expire < 10:
        print(
            f"Warning: {user_token_expire} request remains, please get new secret token soon."
        )

    if r.status_code != 200:
        print(f"User {user} does not exists.")
        return None
    repos = []
    for i in r.json():
        repo = dict()
        try:
            repo["id"] = i["id"]
            repo["full_name"] = i["full_name"]
            repo["svn_url"] = i["svn_url"]
        except KeyError as err:
            print(f"Undefined key: {err}")
        finally:
            repos.append(repo)
    return repos


def repos_to_json(repos):
    json_repos = json.dumps(repos)
    return json_repos


def save_to_json(json_string, filename=f"./json_data/{GITHUB_USER}.json"):
    try:
        with open(filename, "w", encoding="utf-8") as jf:
            jf.write(json_string)
    except FileNotFoundError:
        os.mkdir(os.path.join(os.getcwd(), filename.split("/")[1]))
        with open(filename, "w", encoding="utf-8") as jf:
            jf.write(json_string)


def main():
    repos = get_repos(GITHUB_USER)
    if not repos:
        return None
    json_repos = repos_to_json(repos)
    save_to_json(json_repos)


if __name__ == "__main__":
    main()
