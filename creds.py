import os
import json

class Creds:
  def __init__(self):
    self.json_file_path=os.environ["HOME"] + "/.creds/atlassian_creds.json"
    self.username = None
    self.password = None
    self.jira_token = None
    self.wiki_token = None
    self.jira_page = None

    if os.path.exists(self.json_file_path):
      with open(self.json_file_path) as json_file:
        creds_json = json.load(json_file)
        if "atlassian_username" in creds_json:
          self.username = creds_json["atlassian_username"]
        if "atlassian_password" in creds_json:
          self.password = creds_json["atlassian_password"]
        if ("jira_token") in creds_json:
          self.jira_token = creds_json["jira_token"]
        if ("wiki_token") in creds_json:
          self.wiki_token = creds_json["wiki_token"]
        if ("jira_page") in creds_json:
          self.jira_page = creds_json["jira_page"]

