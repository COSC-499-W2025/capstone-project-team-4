 CLI Documentation:
> --grant # Sets consent_granted = true
> --revoke # Sets consent_granted = false
> --external # allows sending data to external sources (LLMs/APIs) 
> --no_external # disallows sending data to external sources 
> status - prints json config 

Examples: 
> python -m src.main consent --grant 
```
Running in virtual env: True
Database initialized successfully.
Loaded: {'theme': 'dark', 'notifications': True}
Consent granted.

Current configuration:
{'consent_granted': True, 'external_allowed': False, 'external_last_notice_version': 0}
```
Example output, changes consent_granted to true and prints json file 
-----------------------------------------------
> python -m src.main consent --revoke   

> python -m src.main consent --external

> python -m src.main consent --no_external

> python -m src.main status 


