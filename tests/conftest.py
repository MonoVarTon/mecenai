import os

# Tests always run offline on the scripted model, whatever is in a local .env.
os.environ["MECENAI_MODEL"] = "scripted"
