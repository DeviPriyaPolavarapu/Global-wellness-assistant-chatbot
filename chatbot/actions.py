# actions.py
import json
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

# Load KB once
with open("health_kb.json", "r", encoding="utf-8") as f:
    HEALTH_KB = json.load(f)

# Normalize keys for case-insensitive matching
HEALTH_KB_NORMALIZED = {k.lower(): v for k, v in HEALTH_KB.items()}


class ActionProvideConditionInfo(Action):

    def name(self) -> Text:
        return "action_provide_condition_info"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        condition = tracker.get_slot("condition")

        # Debug logging
        print("DEBUG - Extracted condition slot:", condition)

        if condition:
            condition_key = condition.lower().strip()
            if condition_key in HEALTH_KB_NORMALIZED:
                info = HEALTH_KB_NORMALIZED[condition_key]

                # Debug logging
                print(f"DEBUG - Found info for condition: {condition_key}")

                dispatcher.utter_message(
                    text=(
                        f"{info['description']}\n\n"
                        f"Symptoms: {', '.join(info['symptoms'])}\n"
                        f"First Aid: {', '.join(info['first_aid'])}\n"
                        f"Prevention: {', '.join(info['prevention'])}\n"
                        f"{info['disclaimer']}"
                    )
                )
            else:
                print(f"DEBUG - Condition not found in KB: {condition_key}")
                dispatcher.utter_message(
                    text="Sorry, I don't have information on that condition."
                )
        else:
            print("DEBUG - No condition slot found")
            dispatcher.utter_message(
                text="Sorry, I don't have information on that condition."
            )

        return []
