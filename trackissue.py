
  self.trackedfields = ['Sprint', 'Story Points', 'assignee', 'status']

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

