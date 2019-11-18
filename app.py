import requests
import clearbit
import pandas as pd
import sys
import os
from dotenv import load_dotenv
import csv
from flask import Flask, request, make_response

app = Flask(__name__)

load_dotenv()

clearbit.key = os.getenv("CLEARBIT_KEY")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_contributors(repos_list):
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
		contributors = requests.get(url = "{}?client_id={}&client_secret={}".format(repo[0], client_id, client_secret))
		forks = requests.get(url = "{}?client_id={}&client_secret={}".format(repo[1], client_id, client_secret))
		stars = requests.get(url = "{}?client_id={}&client_secret={}".format(repo[2], client_id, client_secret))
		for user in contributors.json(): 
			github_handles.append(user["login"])
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
					try:
						email = user_activity_data.json()[index]["payload"]["commits"][0]["author"]["email"]
						emails.append(email)
						break
					except:
						continue
				else:
					continue
	return emails

def enrich_emails(emails):
	users = []
	for e in emails:
		try:
			person = clearbit.Person.find(email=e, stream=True)
		except Exception as error:
			person = None
			print(error)
		if person != None:
			g_handle = person["github"]["handle"]
			l_handle = person["linkedin"]["handle"]
			github = "https://github.com/{}".format(g_handle) if g_handle != None else None
			linkedin = "https://www.linkedin.com/{}".format(l_handle) if l_handle != None else None
			users.append({"name":person['name']['fullName'], "email":person["email"], "location":person["location"], "github":github, "linkedin":linkedin, "personal website":person["site"]})
	return users

@app.route('/', methods=['GET', 'POST'])
def form_example():
	if request.method == 'POST':
		org = request.form.get('github_org')
		github_url = "https://api.github.com/orgs/{}/repos?client_id={}&client_secret={}".format(org, client_id, client_secret)
		r = requests.get(url = github_url).json()
		if "message" in r:
			return '''<form method="POST">
              		  GitHub Org: <input type="text" name="github_org" placeholder="stripe-ctf">
              		  <input type="submit" value="Submit"><br>
          		  </form>
          		  <p>It'll take a few mins for the csv to be generated.<p>
				  <h2>"{}" is not a valid organization on GitHub.<h2>'''.format(org)
		contributors_list = get_contributors(r)
		github_handles = get_github_handles(contributors_list)
		emails = get_emails(github_handles)
		users = enrich_emails(emails)
		df = pd.DataFrame(users)
		resp = make_response(df.to_csv())
		resp.headers["Content-Disposition"] = "attachment; filename=github_profiles.csv"
		resp.headers["Content-Type"] = "text/csv"
		return resp
		
	return '''<form method="POST">
              GitHub Org: <input type="text" name="github_org" placeholder="stripe-ctf">
              <input type="submit" value="Submit"><br>
          </form>
          <p>It'll take a few mins for the csv to be generated.<p>'''

if __name__ == "__main__":
    app.run(debug=True)