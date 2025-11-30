import json
import os
from typing import List, Dict, Any
from app.core.config import settings

class GmailService:
    def __init__(self, dataset_path: str = None):
        self.dataset_path = dataset_path or settings.DATASET_PATH

    def list_messages(self) -> List[Dict[str, Any]]:
        """
        Reads the local JSON dataset and returns list of emails.
        """
        if not os.path.exists(self.dataset_path):
            print(f"Dataset not found at {self.dataset_path}")
            return []
            
        with open(self.dataset_path, 'r') as f:
            data = json.load(f)
            
        return data.get("emails", [])

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """
        Finds a specific message in the dataset.
        """
        emails = self.list_messages()
        for email in emails:
            if email.get("message_id") == message_id:
                return email
        return None
