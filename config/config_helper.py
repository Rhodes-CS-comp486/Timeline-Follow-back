import os
import json
from flask import current_app

def load_questions():
    path = os.path.join(current_app.root_path,"config", "questions.json")
    with open(path) as f:
        return json.load(f)