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
        # Check if we're in a TAN status flow context
        events = tracker.events
        is_tan_context = False
        for event in reversed(events[-10:]):  # Check last 10 events
            if event.get("event") == "action" and event.get("name") == "utter_ask_tan_number":
                is_tan_context = True
                break
        
        # Try to extract PAN from entities first
        pan_entities = tracker.latest_message.get("entities", [])
        pan = None
        
        for entity in pan_entities:
            if entity.get("entity") == "pan_number":
                pan = entity.get("value", "").strip().upper()
                break
        
        # If no entity found, try to extract from text
        if not pan:
            last_user_msg = (tracker.latest_message.get("text") or "").strip().upper()
            import re
            if re.fullmatch(r"[A-Za-z]{5}\d{4}[A-Za-z]", last_user_msg):
                pan = last_user_msg
        
        # If we're in TAN context and got a PAN-formatted input, redirect to TAN action
        if is_tan_context and pan:
            # This is a PAN format in TAN context, redirect to TAN action
            return ActionCheckTANStatus().run(dispatcher, tracker, domain)
        
        if not pan:
            # If not a valid PAN format, provide helpful error message
            last_user_msg = (tracker.latest_message.get("text") or "").strip()
            
            # Check if this looks like a TAN format instead of PAN
            import re
            if re.fullmatch(r"[A-Za-z]{4}\d{5}[A-Za-z]", last_user_msg.upper()):
                dispatcher.utter_message(text="Invalid PAN format. Please enter your 10-character PAN (e.g., ABCDE1234E).")
                return []
            
            # Check if this is an invalid PAN format intent or if it looks like an invalid PAN
            latest_intent = tracker.latest_message.get("intent", {}).get("name", "")
            is_invalid_pan = (latest_intent == "invalid_pan_format" or 
                            (len(last_user_msg) > 0 and not re.fullmatch(r"[A-Za-z]{5}\d{4}[A-Za-z]", last_user_msg.upper())))
            
            if is_invalid_pan:
                dispatcher.utter_message(text="Invalid PAN format. Please enter your 10-character PAN (e.g., ABCDE1234E).")
            else:
                dispatcher.utter_message(text="Please enter your 10-character PAN (e.g., ABCDE1234E).")
            return []
        
        # Call backend API
        base_url = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
        try:
            resp = requests.post(f"{base_url}/api/pan/status", json={"pan_number": pan}, timeout=5)
            if resp.ok:
                data = resp.json()
                message = data.get("message") or f"Your PAN {data.get('pan_number','')} status is in progress."
                dispatcher.utter_message(text=message)
                return []
        except Exception:
            pass
        # Fallback friendly message if API is unreachable
        dispatcher.utter_message(text="Your PAN application is in progress. Please check back later.")
        return []


class ActionCheckTANStatus(Action):
    def name(self) -> Text:
        return "action_check_tan_status"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Check if we're in a PAN status flow context
        events = tracker.events
        is_pan_context = False
        is_tan_context = False
        for event in reversed(events[-10:]):  # Check last 10 events
            if event.get("event") == "action":
                if event.get("name") == "utter_ask_pan_number":
                    is_pan_context = True
                    break
                elif event.get("name") == "utter_ask_tan_number":
                    is_tan_context = True
                    break
        
        # Try to extract TAN from entities first
        tan_entities = tracker.latest_message.get("entities", [])
        tan = None
        
        for entity in tan_entities:
            if entity.get("entity") == "tan_number":
                tan = entity.get("value", "").strip().upper()
                break
        
        # If no entity found, try to extract from text
        if not tan:
            last_user_msg = (tracker.latest_message.get("text") or "").strip().upper()
            import re
            if re.fullmatch(r"[A-Za-z]{4}\d{5}[A-Za-z]", last_user_msg):
                tan = last_user_msg
        
        # If we're in PAN context and got a TAN-formatted input, redirect to PAN action
        if is_pan_context and tan:
            # This is a TAN format in PAN context, redirect to PAN action
            return ActionCheckPANStatus().run(dispatcher, tracker, domain)
        
        if not tan:
            # If not a valid TAN format, provide helpful error message
            last_user_msg = (tracker.latest_message.get("text") or "").strip()
            
            # Check if this looks like a PAN format instead of TAN
            import re
            if re.fullmatch(r"[A-Za-z]{5}\d{4}[A-Za-z]", last_user_msg.upper()):
                dispatcher.utter_message(text="Invalid TAN format. Please enter your 10-character TAN (e.g., ABCD12345E).")
                return []
            
            # Check if this is an invalid TAN format intent or if it looks like an invalid TAN
            latest_intent = tracker.latest_message.get("intent", {}).get("name", "")
            is_invalid_tan = (latest_intent == "invalid_tan_format" or 
                            (len(last_user_msg) > 0 and not re.fullmatch(r"[A-Za-z]{4}\d{5}[A-Za-z]", last_user_msg.upper())))
            
            if is_invalid_tan:
                dispatcher.utter_message(text="Invalid TAN format. Please enter your 10-character TAN (e.g., ABCD12345E).")
            else:
                dispatcher.utter_message(text="Please enter your 10-character TAN (e.g., ABCD12345E).")
            return []
        
        # Call backend API
        base_url = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
        try:
            resp = requests.post(f"{base_url}/api/tan/status", json={"tan_number": tan}, timeout=5)
            if resp.ok:
                data = resp.json()
                message = data.get("message") or f"Your TAN {data.get('tan_number','')} status is in progress."
                dispatcher.utter_message(text=message)
                return []
        except Exception:
            pass
        # Fallback friendly message if API is unreachable
        dispatcher.utter_message(text="Your TAN application is in progress. Please check back later.")
        return []