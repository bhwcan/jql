# Python 3.5
import json
import html
import pprint
import atlassian
import readline
import atexit
import os
import textwrap
from datetime import datetime

if os.name == "nt":
  import msvcrt as m
else:
  import getch as m

from atlassian import Jira

#print(os.__file__)

#print(atlassian.__file__)

# local imports
import creds

class JQL:
  def __init__(self):
    self.configpath = os.path.expanduser("~")+os.path.sep+".jql"+os.path.sep
    self.colspath = ""
    self.querypath = self.configpath + "queries.json"
    self.prompt = "jql> "
    self.response = ""
    self.jira = None
    self.message = ""
    self.command_char = '!'
    self.command = ""
    self.pagesize = 20
    self.cols = []
    self.queries = {}
    self.trackedfields = ['Sprint', 'Story Points', 'assignee', 'status']

  def isCommand(self):
    #print(self.response)
    r = False
    if len(self.response) > 0:
      if self.response[0] == self.command_char:
        self.command = self.response[1:].lower()
        r = True
      elif self.response[0] == '?':
        self.command = "?"
        r = True
        
    return r

  def listcols(self):

    pprint.pprint(self.cols)

  def listqueries(self):

    pprint.pprint(self.queries)

  def treeprint(self, issue, level):

    points = 0.
    assignee = "Unassigned"
  
    fields = issue['fields']

    outstr = "| "*(level)
    outstr += "> {k:10.10}".format(k=issue['key'])
    outstr += " | {t:8.8}".format(t=fields['issuetype']['name'])
    if 'customfield_10106' in fields:
      if fields['customfield_10106']:
        points = fields['customfield_10106']
    outstr += " | {n:4.1f}".format(n=points)
    outstr += " | {n:14.14}".format(n=fields['status']['name'])
    if 'assignee' in fields:
      if fields['assignee']:
        assignee = fields['assignee']['displayName']
    outstr += " | {a:22.22}".format(a=assignee)
    outstr += " | " + fields['summary']

    print(outstr)

  def treeissue(self, key):

    data = self.jira.jql("key = " + key)
    for issue in data['issues']:
      self.issuewalk(issue)

  def issuewalk(self, i, level=0):

    self.treeprint(i, level)
    childquery = "\"Parent Link\" = " + i['key']
    data = self.jira.jql(childquery)
    for issue in data['issues']:
      self.issuewalk(issue, level+1)
    
  def trackIssue(self, key):
    
    ijql = "id = " + key.upper()

    try:
      data = self.jira.jql(ijql)
    except:
      print("Error: issue", key.upper(), "not found")
      return

    fields = data['issues'][0]['fields']
    points = ""
    if fields['customfield_10106']:
      points = "{:.1f}".format(fields['customfield_10106'])
    ct = datetime.strptime(fields['created'][:19],'%Y-%m-%dT%H:%M:%S')
    typeis = fields['issuetype']['name']
    if fields['issuetype']['subtask']:
      typeis = "{} of {}".format(fields['issuetype']['name'], fields['parent']['key'])
    #print("tracked changes", self.trackedfields)
    #exit(1)

    pt = ct
    rct = None
    rctby = ""
    opentime = pt - ct
    dt = opentime
    dct = opentime

    inSprint = False
    sprintTime = opentime
    sprintCount = 0
    inDev = False
    devTime = opentime
    inBlock = False
    blockTime = opentime

    print("\t", ct, fields['creator']['displayName'], "created" )

    changelog = self.jira.get_issue_changelog(key)
    for jiraChange in changelog['histories']:

      #pprint.pprint(jiraChange)
      #exit(10)
      tracked = False
      #print("\n", "changed timestamp", jiraChange['created'][:19], "by", jiraChange['author']['displayName'])
      for items in jiraChange['items']:

        # log changes
        outstr = jiraChange['created'][:10] +" " + jiraChange['created'][11:19] + " " +\
          jiraChange['author']['displayName'] + " changed " + items['field']
        if items['field'] != "description" and items['field'] != "summary":
          if items['fromString']:
            outstr += " from \'" + items['fromString'] + "\'"
          if items['toString']:
            outstr += " to \'" + items['toString'] + "\'"
        print("\t", outstr)

        if items['field'] in self.trackedfields:
          #print("\t[{}]".format(items['field']), "to", '"{}"'.format(items['toString']))
          tracked = True
        #else:
        #  print("\t[{}]".format(items['field']))
      if tracked:
        nt = datetime.strptime(jiraChange['created'][:19],'%Y-%m-%dT%H:%M:%S')
        dt = nt - pt
        dct = nt - ct
        #print("elapsed time since last tracked is", dt, "since created is", dct, "In Sprint", inSprint, "In Dev", inDev)
        if inSprint:
          sprintTime += dt
        if inDev:
          devTime += dt
        if inBlock:
          blockTime += dt
        pt = nt

      for items in jiraChange['items']:
        if items['field'] == "Sprint":
          if len(items['toString']) > 0:
            inSprint = True
            sprintCount += 1
          else:
            inSprint = False
        if items['field'] == "status":
          if items['toString'] in ['In Development', 'Ready For Testing', 'Testing']:
            inDev = True
          else:
            inDev = False
          if items['toString'] in ['Blocked', 'Test Blocked']:
            inBlock = True
          else:
            inBlock = False
          if items['toString'] == "Closed":
            inSprint = False
            opentime = dct
            rct = nt
            rctby = jiraChange['author']['displayName']

    nt = datetime.now()
    dt = nt - pt
    dct = nt - ct
    if opentime.seconds <= 0:
      opentime = dct
    if inSprint:
      sprintTime += dt
    if inDev:
      devTime += dt
    if inBlock:
      blockTime += dt
    
    #print("elapsed time since last tracked is", dt, "since created is", dct, "In Sprint", inSprint, "In Dev", inDev)
    assignee = "Unasigned"
    if fields['assignee']:
      assignee = fields['assignee']['displayName']
    print("\nFinal status", key.upper(), fields['status']['name'], typeis, "assignee", assignee, "Story Points", points)
    print(fields['summary'], "\n")
    if rct:
      print("Closed on", rct, "by", rctby)
      print("Since created to closed time", opentime)
    else:
      print("Since created", opentime)
    print("In Sprint time", sprintTime, "for", sprintCount, "sprints")
    print("In Development time", devTime)
    if blockTime.seconds > 0:
      print("Blocked time", blockTime)
    
    return

  def printIssue(self, key):
   
    ijql = "id = " + key.upper()

    try:
      data = self.jira.jql(ijql)
    except:
      print("Error: issue", key.upper(), "not found")
      return
    
    for jira_issue in data['issues']:
      fields = jira_issue['fields']

    print("\n")
    print(jira_issue['key'], " - ", html.escape(fields['summary']), '\n')
    resolution = "Unresolved"
    if fields['resolution']:
        resolution = fields['resolution']['name']
    print("{:20.20}{:30.30}{:20.20}{:20.20}".format("Status:",fields['status']['name'],"Resolution:",resolution))
    versions = "None"
    if fields['fixVersions']:
        versions = (', '.join(ss['name'] for ss in fields['fixVersions']))
    typeis = fields['issuetype']['name']
    if fields['issuetype']['subtask']:
      typeis = "{} of {}".format(fields['issuetype']['name'], fields['parent']['key'])
    print("{:20.20}{:30.30}{:20.20}{:}".format("Type:",typeis,"Fix Versions:",versions))
    assignee = "Unassigned"
    if fields['assignee']:
        assignee = fields['assignee']['displayName']
    components = "None"
    if fields['components']:
        components = (', '.join(ss['name'] for ss in fields['components']))
    print("{:20.20}{:30.30}{:20.20}{:}".format("Assignee:",assignee,"Components:",components))
    report = "None"
    if fields['reporter']:
      report = fields['reporter']['displayName']
    labels = "None"
    if fields['labels']:
      labels = ", ".join(fields['labels'])
    print("{:20.20}{:30.30}".format("Reporter:",report))
    print("{:20.20}{:}".format("Labels:",labels))
    epic = "None"
    if fields['customfield_10101']:
        epic = fields['customfield_10101']
    created = "None"
    if fields['created']:
        created=fields['created'][0:10]+" "+fields['created'][11:16]
    print("{:20.20}{:30.30}{:20.20}{:}".format("Epic Link:",epic,"Created:",created))
    severity = "None"
    if fields['priority']:
        severity = fields['priority']['name']
    updated = "None"
    if fields['updated']:
        updated = fields['updated'][0:10]+" "+fields['updated'][11:16]
    print("{:20.20}{:30.30}{:20.20}{:}".format("Severity:",severity,"Updated:",updated))
    points = ""
    if fields['customfield_10106']:
        points = "{:.1f}".format(fields['customfield_10106'])
    resolved="None"
    if fields['resolutiondate']:
        resolved = fields['resolutiondate'][0:10]+" "+fields['resolutiondate'][11:16]
    print("{:20.20}{:30.30}{:20.20}{:}".format("Story Points:",points,"Resolved:",resolved))
    if fields['description']:
        desclines = fields['description'].splitlines()
        print("\nDescription\n-----------")
        for line in desclines:
          if len(line) > 100:
            for l in textwrap.wrap(line,100):
              print(l)
          else:
            print(line)

  def runquery(self, name):

    if name in self.queries:
      query = "".join(self.queries[name]["query"])
      if "columns" in self.queries[name]:
        self.loadcolumns(jql.configpath + self.queries[name]["columns"])
      print(query)
      readline.add_history(query)
      self.response = query
      self.queryIssues()
    else:
      print("not found")
      
  def dumpIssue(self, key, search):

    pf = ""
    
    ijql = "id = " + key.upper()
    print(ijql)

    try:
      data = self.jira.jql(ijql)
    except:
      print("Error: issue", key.upper(), "not found")
      return
    
    for jira_issue in data['issues']:
      fields = jira_issue['fields']

    c = 1
    pf = pprint.pformat(fields)
    lines = pf.splitlines()
    for line in lines:
      if search == "" or line.find(search) > 0:
        print("{:4d}:{:}".format(c,line))
      c = c + 1
  
  def helpcols(self):

    print("Help Columns:")

    print("\tThe display columns are loaded from a json file containing an arrary of key value pairs")
    print("\tEach column entry must have \'title\', \'field\', \'width\', \'type\'")
    print("\ttitle: column heading")
    print("\tfield: field in JIRA issue")
    print("\twidth: column total width in characters, field will be truncated")
    print("\ttype: one of int, str, float, list, date")
    print("\t\tint: a whole number in JIRA")
    print("\t\tstr: a text field in JIRA")
    print("\t\tfloat: a number with decimal places must have a \'precision\'")
    print("\t\tlist: a list field in JIRA, \'precision\' may be used for the length of each entry")
    print("\t\tdate: a date field in JIRA")
    print("\n")
    
  def listcmds(self):

    print("!list")
    print("\tcols: list the columns currently displayed for searches")
    print("\tcmds: display this nice list of commands")
    print("\tqueries: list the saved queries from", self.querypath)
    print("!help or !?")
    print("\tcols: list the columns help")
    print("\tcmds: display this nice list of commands")
    print("!dump")
    print("\t<jira_issue> <search_string>: dictionary pretty print of the issue fields with search")
    print("!track")
    print("\t<jira_issue>: real time tracking of changes")
    print("!tree")
    print("\t<jira_issue>: print out parent link relationship")
    print("!print")
    print("\t<jira_issue>: formatted print of jira issue")
    print("!load")
    print("\tcols: loads columns from json file", self.colspath)
    print("!run")
    print("\tname: run named save query from", self.querypath)
    print("!set")
    print("\tpagesize: set rows to print before pause, must be >= 1 and <= 500, current value:", self.pagesize)
    print("!quit or !q")
    print("\tYou're done")
    print("\n")

  def runCommand(self):
    r = False
    cmds = self.command.split()

    if len(cmds) > 0:
      if cmds[0] == "list":
        if len(cmds) > 1:
          if cmds[1] == "cols":
            self.listcols()
            r = True
          if cmds[1] == "cmds":
            self.listcmds()
            r = True
          if cmds[1] == "query" or cmds[1] == "queries":
            self.listqueries()
            r = True
      elif cmds[0] == "dump":
        if len(cmds) > 1:
          if len(cmds) < 3:
            cmds.append("")
          self.dumpIssue(cmds[1],cmds[2])
          r = True
      elif cmds[0] == "run" or cmds[0] == "r":
        if len(cmds) > 1:
          self.runquery(cmds[1])
          r = True
      elif cmds[0] == "print":
        if len(cmds) > 1:
          self.printIssue(cmds[1])
          r = True
      elif cmds[0] == "track":
        if len(cmds) > 1:
          self.trackIssue(cmds[1])
          r = True
      elif cmds[0] == "tree":
        if len(cmds) > 1:
          self.treeissue(cmds[1])
          r = True
      elif cmds[0] == "load":
        if len(cmds) > 1:
          if cmds[1] == "cols":
            if len(cmds) > 2:
              self.loadcolumns(jql.configpath + cmds[2])
            else:
              self.loadcolumns(self.colspath)
            r = True
          if cmds[1] == "query" or cmds[1] == "queries":
            self.loadqueries(self.querypath)
            r = True
      elif cmds[0] == "help" or cmds[0] == "?":
        if len(cmds) > 1:
          if cmds[1] == "cols":
            self.helpcols()
            print("Current columns:")
            self.listcols()
            r = True
          elif cmds[1] == "cmds":
            self.listcmds()
            r = True
        else:
          self.helpcols()
          self.listcmds()
          r = True
      elif cmds[0] == "set":
        if len(cmds) > 1:
          if cmds[1] == "pagesize":
            if len(cmds) > 2:
              newsize = 0
              try:
                newsize = int(cmds[2])
              except:
                newsize = -1
              if newsize > 0 and newsize <= 500:
                print("changing pagesize from", self.pagesize, "to", newsize)
                self.pagesize = newsize
                r = True
            
    if not r:
        print("Error invalid command:",self.command)

    return r

  def run(self):
    while True:
      self.response = input(self.prompt)
      if self.isCommand():
        if self.command == "quit" or self.command == "q":
          break
        else:
          self.runCommand()
      else:
        if len(self.response) > 0:
          self.queryIssues()
        

  def next(self):
    r = 'n'
    s = wait()
    if len(s) < 1:
      r = 'n'
    else:
      r = s[0]
      if r not in "npqb":
        r = 'n'

    if r == 'q':
      print("<quit>")
    elif r == 'p' or r == 'b':
      r = 'p'
      print("<prev>")
    else:
      print("<next>")
      
    return r

  def titles(self):

    str = "\n"
    str2 = ""
    for col in self.cols:
      if col['type'] == "str" or col['type'] == "list" or col['type'] == "date":
        str += "{t:<{l}} ".format(t=col['title'],l=col['width'])
      else:
        str += "{t:>{l}} ".format(t=col['title'],l=col['width'])
      for j in range(0,col['width']):
        str2 += "-"
      str2 += ' '

    str += "\n" + str2

    return str

  def getNames(self, data, p):

    names = []
    first = True
    #print("getNames", p)
    
    for v in data:
      name = ""
      i = v.find('name=')
      if i > 0:
        e = v[i:].find(',')
        #print("e", e)
        if p > 0:
          if e > (p+5):
            e = p+5
        name = v[i+5:i+e]
        names.append(name)

      #print(names)
    #return ', '.join(sorted(names, reverse=True))
    return(names)
    
  def printrow(self, columns):

    ml = 0
    for cc in columns:
      if len(cc) > ml:
        ml = len(cc)
    #print("max length", ml)
    
    for l in range(ml):
      str = ""
      c = 0
      for col in self.cols:
        #print(columns[c][0], len(columns[c][0]), col['width'])
        if l < len(columns[c]):
          str += "{n:{l}.{l}} ".format(n=columns[c][l],l=col['width'])
        else:
          str += "{n:{l}.{l}} ".format(n="",l=col['width'])
        c = c + 1
      print(str)
    #exit(0)
  
  def queryIssues(self):
    
    c = 1
    start = 0
    limit = self.pagesize

    try:
      data = self.jira.jql(self.response, start=start, limit=limit)
    except:
      print("Error: invalid query")
      return
    print(data['total'], "row" if data['total'] == 1 else "rows", "selected.")
    
    while c <= data['total']:

      print(self.titles())

      for jira_issue in data['issues']:
        columns = []

        fields = jira_issue['fields']

        for col in self.cols:
          i = 0
          s = ""
          r = 0.0
          l = []
          if col['field'] == "row":
            i = c
          elif col['field'] == "key":
            s = jira_issue['key']
          else:
            if col['field'] in fields:
              if col['type'] == "date":
                  #print(fields[col['field']])
                  s = fields[col['field']][0:10]+" "+fields[col['field']][11:16]
              elif col['type'] == "str":
                if fields[col['field']]:
                  if type(fields[col['field']]) is dict:
                    if 'displayName' in fields[col['field']]:
                      s = fields[col['field']]['displayName']
                    elif 'name' in fields[col['field']]:
                      s = fields[col['field']]['name']
                  else:
                    s = fields[col['field']]
                    #s = html.escape(fields[col['field']])
              elif col['type'] == "int":
                i = fields[col['field']]
              elif col['type'] == "float":
                if fields[col['field']]:
                  r = fields[col['field']]
              elif col['type'] == "list":
                if type(fields[col['field']]) is list:
                  if col['field'] == "customfield_10105":
                    if 'precision' in col:
                      p = col['precision']
                    else:
                      p = 0
                    l = self.getNames(fields[col['field']],p)
                  elif col['field'] == "labels":
                    if 'precision' in col:
                      for ss in fields[col['field']]:
                        l.append(ss[:col['precision']])
                    else:
                      l = fields[col['field']]
                  else:
                    if 'precision' in col:
                      for ss in fields[col['field']]:
                        l.append(ss['name'][:col['precision']])
                    else:
                      for ss in fields[col['field']]:
                        l.append(ss['name'])
              else:
                continue

          if col['type'] == "str" or col['type'] == 'date':
            if 'precision' in col:
              columns.append(textwrap.wrap("{n:.{p}}".format(n=s,p=col['precision']), col['width']))
            else:
              columns.append(textwrap.wrap(s, col['width']))
          elif col['type'] == 'list':
            columns.append(l)
          elif col['type'] == "int":
            columns.append(textwrap.wrap("{n:{w}d}".format(n=i,w=col['width']), col['width']))
          elif col['type'] == "float":
            columns.append(textwrap.wrap("{n:{w}.{d}f}".format(n=r,w=col['width'],d=col['precision']), col['width']))
          else:
            continue

        self.printrow(columns)
            
        c = c + 1
        #print(c)

      if c <= data['total']:
        cmd = self.next()
        if cmd == 'q':
          break
      
        if cmd == 'n':
          start = start + limit

        if cmd == 'p':
          start = start - limit
          if start < 0:
            start = 0
          c = start + 1

      data = self.jira.jql(self.response,start=start,limit=limit)
      
    return

  def loadqueries(self, filename):

    print("loading queries from", filename)

    r = True
    try:
      f = open(filename)
      self.queries = json.load(f)
      f.close()
    except:
      print("Error: json file", filename)
      r = False
    return r
    
  def loadcolumns(self, filename):

    print("loading columns from", filename)

    r = True
    try:
      f = open(filename)
      self.cols = json.load(f)
      f.close()
      self.colspath = filename
    except:
      print("Error: json file", filename)
      r = False
      return r
    
    #pprint.pprint(self.cols)

    c = 1
    keys = ['title', 'field', 'width', 'type']
    for col in self.cols:
      for k in keys:
        if k not in col:
          print("Error: column", c, "must have", k)
          r = False
      if not r:
        break
      #print(col)
      if col['type'] == "float":
        if 'precision' not in col:
          print("Error: column", c, "must have", "precision")
          r = False
          break
            
      c = c + 1

    return r

    
jql = JQL()

def wait():
  ar = ""
  d = m.getch()
  if os.name == "nt":
    # emergency exit for debug
    if d == b'!':
      exit(6)
    # special characters stick S in front
    if d == b'\xe0':
      dd = m.getch()
      ar = "S"+dd.decode("utf-8")
    else:
      ar = d.decode("utf-8")
  else:
    if d == '!':
      exit(6)
    if d == '\x1b':
      dd = m.getch()+m.getch()
      if dd == "[A":
        ar = "SH"
      elif dd == "[B":
        ar = "SP"
      else:
        ar = dd
    else:
      ar = d
  return ar

def main(creds):

  histfile = jql.configpath + ".history"
  try:
    readline.read_history_file(histfile)
    readline.set_history_length(1000)
  except FileNotFoundError:
    pass
  
  atexit.register(readline.write_history_file, histfile)
  
  # connect to jira
  try:
    jql.jira = Jira(url=creds.jira_page,
                    username=creds.username,
                    password=creds.jira_token)
  except:
    print("Error: unable to connect to jira check credentials in file:")
    print("      ", creds.json_file_path)
    exit(1)

  if not jql.loadcolumns(jql.configpath + "default.cols"):
    exit(2)

  if not jql.loadqueries(jql.querypath):
    print("Unable to load:", jql.querypath)
    
  #exit()
  
  print("Connected to ", creds.jira_page)
  #exit()
  
  jql.run()
  print("Done.")

if __name__ == "__main__":
  creds = creds.Creds()
  main(creds)

