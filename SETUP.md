# Where each file goes

Unzip into C:\dev\InsightGlobal so the layout is:

    InsightGlobal\
      .claude\commands\frame.md
      .claude\commands\data.md
      .claude\commands\architect.md
      .claude\commands\checkpoint.md
      backend\app\main.py
      backend\app\__init__.py
      backend\app\agents\__init__.py
      backend\app\tools\__init__.py
      backend\data\.gitkeep
      scratch\.gitkeep
      CLAUDE.md
      run.ps1
      .env.example
      .gitignore

Then:

    copy .env.example .env      # and paste your real key into .env
    .\run.ps1

Check http://localhost:8000/api/health
Expect: {"status":"ok","model":"claude-sonnet-5","api_key_loaded":true}
