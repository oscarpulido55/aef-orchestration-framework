python3 -m venv .firestorevenv
source .firestorevenv/bin/activate
python3 -m pip install google-cloud
python3 -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
python3 -m pip install --upgrade google-cloud-firestore