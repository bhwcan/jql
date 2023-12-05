from atlassian import Jira

# local imports
import creds

#main

creds = creds.Creds()
jira = None

print("  username:", creds.username)
print("jira token:", creds.jira_token)

# connect to jira
try:
  jira = Jira(url=creds.jira_page,
              username=creds.username,
              password=creds.jira_token)
except:
  print("Error: unable to connect to jira check credentials in file:")
  print("      ", creds.json_file_path)
  print(jira)
  exit(1)

print("Connected to Jira")
