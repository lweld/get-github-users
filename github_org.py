import requests
import clearbit
import pandas as pd
import sys
import os

clearbit.key = os.environ.get("CLEARBIT_KEY")
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
github_org = "https://api.github.com/orgs/stripe-ctf/repos?client_id={}&client_secret={}".format(client_id, client_secret)

def get_contributors():
	r = requests.get(url = github_org)
	repos_list = r.json()
	contributors_list = []
	for repo in repos_list:
		repo_contributors = []
		repo_contributors.append(repo["contributors_url"])
		repo_contributors.append(repo["forks_url"])
		repo_contributors.append(repo["stargazers_url"])
		contributors_list.append(repo_contributors)
	return contributors_list

def get_github_handles(contributors_list):
	github_handles = []
	for repo in contributors_list:
		contributors = requests.get(url = repo[0])
		forks = requests.get(url = repo[1])
		stars = requests.get(url = repo[2])
		for user in contributors.json(): github_handles.append(user["login"])
		for user in forks.json(): github_handles.append(user["owner"]["login"])
		for user in stars.json(): github_handles.append(user["login"])
	github_handles = list(set(github_handles))
	return github_handles

def get_emails(github_handles):
	emails = []
	for handle in github_handles:
		github_profile = "https://api.github.com/users/{}/events/public?client_id={}&client_secret={}".format(handle, client_id, client_secret)
		user_activity_data = requests.get(url = github_profile)
		if len(user_activity_data.json()) > 0:
			for index in range(len(user_activity_data.json())):
				if index > len(user_activity_data.json()) - 1:
					break
				elif "commits" in user_activity_data.json()[index]["payload"]:
					email = user_activity_data.json()[index]["payload"]["commits"][0]["author"]["email"]
					emails.append(email)
					break
				else:
					continue
	return emails

def enrich_emails(emails):
	users = []
	for e in emails:
		try:
			person = clearbit.Person.find(email=e, stream=True)
		except:
			person = None
			print("Looks like a {} occurred.".format(sys.exc_info()[0]))
		if person != None:
			g_handle = person["github"]["handle"]
			l_handle = person["linkedin"]["handle"]
			github = "https://github.com/{}".format(g_handle) if g_handle != None else None
			linkedin = "https://www.linkedin.com/{}".format(l_handle) if l_handle != None else None
			users.append({"name":person['name']['fullName'], "email":person["email"], "location":person["location"], "github":github, "linkedin":linkedin, "personal website":person["site"]})
	return users

def write_to_excel(users):
	df = pd.DataFrame(users)
	df.to_csv("github_profiles.csv")

def main():
	contributors_list = get_contributors()
	github_handles = get_github_handles(contributors_list)
	emails = get_emails(github_handles)
	users = enrich_emails(emails)
	write_to_excel(users)
main()