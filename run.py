'''coderadi'''

# ? Importing libraries
from main import *
import json

# ! Building database
with server.app_context():
    db.create_all()

# & Loading skills data
print(f"Adding skills to db...")
with open(SKILLS_FILE) as f:
    data = json.load(f)

# ! Updating skills in database
for category in data:
    for skill in data[category]:
        with server.app_context():
            if not (Skill.query.filter_by(skill=skill['hashtag'])).first():
                new_skill = Skill(
                    category=category,
                    skill=skill['hashtag'],
                )
                db.session.add(new_skill)
                db.session.commit()
                QTY += 1
print(f"Added {QTY} skill(s) to db.")

# ! Updating hosting
with server.app_context():
    add_basic_details()

# ! Creating all folders
for folder in FOLDERS:
    os.makedirs(folder, exist_ok=True)

# ! Running the server
if __name__ == "__main__":
    socket.run(
        server,
        debug=os.getenv('DEBUG'),
        host=os.getenv('HOST'),
        allow_unsafe_werkzeug=os.getenv('ALLOW_UNSAFE_WERKZEUG')
    )