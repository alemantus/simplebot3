import requests
import json

class RosInterface:
    def __init__(self, url="http://localhost:8000", connector=None):
        """
        ROS Interface wrapper.
        :param url: URL for the REST API (default http://localhost:8000)
        :param connector: Optional connector object that implements call_service and send_action.
                          If provided, this will be used instead of REST calls.
        """
        self.url = url
        self.connector = connector

    def call_service(self, service_name, service_type, request):
        if self.connector:
            return self.connector.call_service(service_name, service_type, request)
            
        payload = {
            "service_name": service_name,
            "service_type": service_type,
            "request": request
        }
        try:
            response = requests.post(f"{self.url}/call_service", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_action(self, action_name, action_type, goal):
        if self.connector:
            return self.connector.send_action(action_name, action_type, goal)
            
        payload = {
            "action_name": action_name,
            "action_type": action_type,
            "goal": goal
        }
        try:
            response = requests.post(f"{self.url}/send_action_goal", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cancel_all_actions(self):
        if self.connector and hasattr(self.connector, 'cancel_all_actions'):
            return self.connector.cancel_all_actions()
        return {"success": False, "error": "Cancel not supported by connector"}
