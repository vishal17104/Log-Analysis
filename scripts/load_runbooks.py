import os
from backend.database import SessionLocal
from backend import crud

db = SessionLocal()
runbooks_dir = "runbooks"

for filename in os.listdir(runbooks_dir):
    if filename.endswith('.md'):
        with open(os.path.join(runbooks_dir, filename), 'r') as f:
            content = f.read()
            title = filename.replace('.md', '').replace('_', ' ').title()

            tags = []
            if 'database' in content.lower() or 'postgres' in content.lower():
                tags.append('database')
            if 'api' in content.lower():
                tags.append('api')

            crud.create_runbook(db, filename, content, title, tags)

db.close()
print("Runbooks loaded from files")