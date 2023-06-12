import os
from dotenv import load_dotenv
load_dotenv()

#slack API
slack_token = os.environ.get("SLACK_TOKEN")
#SLACK_CHANNEL
slack_channel = os.environ.get("SLACK_CHANNEL")