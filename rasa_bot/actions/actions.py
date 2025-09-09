# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List

# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher


# class ActionHelloWorld(Action):

#     def name(self) -> Text:
#         return "action_hello_world"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#         dispatcher.utter_message(text="Hello World!")

#         return []




# D:\PAN2.o\ChatBot_PAN2.o\actions.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import os
import requests

class ActionHelloWorld(Action):
    def name(self) -> Text:
        return "action_hello_world"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Hello from custom action!")
        return []


class ActionCheckPANStatus(Action):
    def name(self) -> Text:
        return "action_check_pan_status"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Try to extract PAN from latest user message
        last_user_msg = (tracker.latest_message.get("text") or "").strip().upper()
        pan = last_user_msg
        # Call backend API (static response for now)
        base_url = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
        try:
            resp = requests.post(f"{base_url}/api/pan/status", json={"pan_number": pan}, timeout=5)
            if resp.ok:
                data = resp.json()
                message = data.get("message") or f"PAN {data.get('pan_number','')} status: {data.get('status','unknown')}"
                dispatcher.utter_message(text=message)
                return []
        except Exception:
            pass
        # Fallback friendly message if API is unreachable
        dispatcher.utter_message(text="Your PAN application is in progress. Please check back later.")
        return []
