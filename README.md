# jql

jql is a command line interface to JQL Atlassian's Jira Query Language. It needs to be able to authenticate with a Jira instance, and then at the JQL> prompt you type your query. I developed this when I was writing company custom Jira reports and found it very useful to be able to query JQL and see the issue information from within my development environment.

## Dependancies

- Atlassian Python API

        pip install atlassian-python-api

- getch 1.0
  - Linux and Mac, PC uses msvcrt

        pip install getch
  
## Programs

jql.py - main program

creds.py - Atlassian credentials

## Credentials

creds.py looks in **os.environ["HOME"]/.creds/atlasian\_creds.json** for tokens and connect strings. 

Three entries are needed for JQL:

1. atlassian\_username: jira identification
2. jira\_token: jira API token
3. jira\_page: connection url

### Sample json:

    {
        "atlassian_username": "john.doe@mail.com",
        "jira_token":         "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "jira_page":          "https://johndoe.atlassian.net"
    }

## Running JQL

    python jql.py
    
    loading columns from /home/jdoe/.jql/default.cols
    loading queries from /home/jdoe/.jql/queries.json
    Connected to  https://johndoe.atlassian.net
    jql> 

## Enter JQL Query

    jql> type not in (Bug, Epic) and project = JQL
    3 rows selected.

     Row Key              Type         Summary                                                      Status         Points 
    ---- ---------------- ------------ ------------------------------------------------------------ -------------- ------ 
       1 JQL-6            Story        Add class for custom fields to support multiple instances    To Do             8.0 
       2 JQL-3            Task         Test and confirm API access to Jira Software Free Plan       Done              3.0 
       3 JQL-2            Task         Create github project for source and documentation           Done              1.0 
    jql> 
    
## Commands

These are jql program commands not part of the JQL language. All commands are preseded by a bang(!).

    jql> !help cmds
    !list
	    cols: list the columns currently displayed for searches
	    cmds: display this nice list of commands
	    queries: list the saved queries from /home/bwalton/.jql/queries.json
    !help or !?
	    cols: list the columns help
	    cmds: display this nice list of commands
    !dump
	    <jira_issue> <search_string>: dictionary pretty print of the issue fields with search
    !comment
	    <jira_issue>: print out comments
    !tree
	    <jira_issue>: print out parent link relationship
    !print
	    <jira_issue>: formatted print of jira issue
    !load
	    cols <filename>: loads columns from json filename or default /home/bwalton/.jql/default.cols
    !run
	    name: run named save query from /home/bwalton/.jql/queries.json
    !set
	    pagesize: set rows to print before pause, must be >= 1 and <= 500, current value: 20
    !quit or !q
	    You're done

## Display Columns

### !help cols

    jql> !help cols
    Help Columns:
	    The display columns are loaded from a json file containing an arrary of key value pairs
	    Each column entry must have 'title', 'field', 'width', 'type'
	    title: column heading
	    field: field in JIRA issue
	    width: column total width in characters, field will be truncated
	    type: one of int, str, float, list, date
		    int: a whole number in JIRA
		    str: a text field in JIRA
		    float: a number with decimal places must have a 'precision'
		    list: a list field in JIRA, 'precision' may be used for the length of each entry
		    date: a date field in JIRA


    Current columns:
    [{'field': 'row', 'title': 'Row', 'type': 'int', 'width': 4},
     {'field': 'key', 'title': 'Key', 'type': 'str', 'width': 16},
     {'field': 'issuetype', 'title': 'Type', 'type': 'str', 'width': 12},
     {'field': 'summary', 'title': 'Summary', 'type': 'str', 'width': 60},
     {'field': 'status', 'title': 'Status', 'type': 'str', 'width': 14},
     {'field': 'customfield_10016',
      'precision': 1,
      'title': 'Points',
      'type': 'float',
      'width': 6}]
    jql> 

Note: custom fields can be handled in the column by putting the name in the field. The precision field represents the number of decimals in a float number. It can also be used with a list to define the width of each entry.

### default.cols

This is the default.cols file in HOME/.jql from the example. Most fields from Jira including custom fields can be handled by one of the five types defined.

    [
        {
            "title": "Row",
            "field": "row",
            "width": 4,
            "type": "int"
        },
        {
            "title": "Key",
            "field": "key",
            "width": 16,
            "type" : "str"
        },
        {
            "title": "Type",
            "field": "issuetype",
            "width": 12,
            "type": "str"
        },
        {
            "title": "Summary",
            "field": "summary",
            "width": 60,
            "type": "str"
        },
        {
            "title": "Status",
            "field": "status",
            "width": 14,
            "type": "str"
        },
        {
            "title": "Points",
            "field": "customfield_10016",
            "width": 6,
            "type": "float",
            "precision": 1
        }
    ]

## Saved Queries

A useful feature in jql is the ability to save commonly used queries. The queries have to be manually entered into the queries.json file in the HOME/.jql directory. 

### !list queries

    jql> !list queries
    {'all': {'columns': 'default.cols',
             'query': ['created >= -30d order by created DESC']},
     'backlog': {'columns': 'default.cols',
                 'query': ['sprint is EMPTY and ',
                           'type not in (Epic) and ',
                           'status not in ("Done") order by rank']},
     'epics': {'columns': 'default.cols',
               'query': ['type = Epic and status not in ("Closed") order by rank']},
     'sprint': {'columns': 'sprint.cols',
                'query': ['sprint in opensprints() order by rank']}}
    jql> 


### Sample queries.json

    {
        "sprint": {
            "query": [
                "sprint in opensprints() order by rank"
            ],
            "columns": "sprint.cols"
        },
        "backlog": {
            "query": [
                "sprint is EMPTY and ",
                "type not in (Epic) and ",
                "status not in (\"Done\") order by rank"
            ],
            "columns": "default.cols"
        },
        "epics": {
            "query": [
                "type = Epic and status not in (\"Closed\") order by rank"
            ],
            "columns": "default.cols"
        },
        "all": {
            "query": [
                "created >= -30d order by created DESC"
            ],
            "columns": "default.cols"
        }
    }

### Query Format

 - query_name: name to call queries from run command
 - query: an array of query lines. The array is for readability as all the lines get concatenated to create the query.
 - columns: a query specific columns file for the query as you may want different information than the defaults. These columns do stay in affect until a new column file is loaded. To return to defaults use !load cols command.


### Run Query

    jql> !run sprint
    loading columns from /home/jdoe/.jql/sprint.cols
    sprint in opensprints() order by rank
    2 rows selected.

    Row Key          Type         Summary                        Status         Points Sprints              
    --- ------------ ------------ ------------------------------ -------------- ------ -------------------- 
      1 SPRIN-1      Story        Create scrum board             To Do             2.0 SPRIN Sprint 1       
      2 SPRIN-3      Story        create data                    To Do             8.0 SPRIN Sprint 1       
    jql> 


## Other Commands

### dump

!dump <issue_id>

- dump the contents of the Jira issues fields data as a pretty print of the dict created from the raw json.

### comment

!comment <issue_id>

- list the comments on the issue by date/time and author

        jql> !comment JQL-8
        2024-02-19 23:04 - J Doe
            json file had a comma after last entry of the array. No fix required.
        jql> 

### tree

!tree <issue_id>

- follow the parent link relationship. Useful for listing issue

        jql> !tree JQL-1
        > JQL-1      | Epic     |  0.0 | ...
        | > JQL-9 | Bug   | 0.0 | Done  | ...
        | > JQL-6 | Story | 0.0 | To Do | ...
        | > JQL-3 | Task  | 0.0 | Done  | ...
        | > JQL-2 | Task  | 0.0 | Done  | ...
        jql> 

### print

!print <issue_id>

- text print of Jira Issue.

        jql> !print JQL-1


        JQL-1  -  JQL Port 

        Status:             To Do                         Resolution:         Unresolved          
        Type:               Epic                          Fix Versions:       None
        Assignee:           Unassigned                    Components:         None
        Reporter:           J Doe                      
        Labels:             None
        Parent Link:        None                          Created:            2023-12-04 14:19
        Severity:           Medium                        Updated:            2024-02-19 10:56

        Description
        -----------
        Port JQL tools to free plan

### load

!load cols

    jql> !load cols
    loading columns from /home/jdoe/.jql/default.cols
    jql> 

### set

!set pagesize 30

- Set the page size for query output.

### quit

!q or !quit

- exit program
