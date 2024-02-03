# tenant_management.config_manager.py
# Ayush

import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError

class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config_schema = {
    "type": "object",
    "properties": {
        "decision_thresholds": {
            "type": "object",
            "properties": {
                "should_be_warned_threshold": {"type": "number"},
                "warned_threshold": {"type": "number"},
                "should_be_cancelled_threshold": {"type": "number"},
                "cancelled_threshold": {"type": "number"},
                "should_be_sued_threshold": {"type": "number"},
                "lawsuit_threshold": {"type": "number"},
                "should_be_evicted_threshold": {"type": "number"},
                "eviction_threshold": {"type": "number"}
            },
            "required": ["should_be_warned_threshold", "warned_threshold", "should_be_cancelled_threshold", "cancelled_threshold", "should_be_sued_threshold", "lawsuit_threshold", "should_be_evicted_threshold", "eviction_threshold"]
                },
                "action_steps": {
                    "type": "object",
                    "properties": {
                        "should_be_warned": {
                            "type": "object",
                            "properties": {
                                "document_template": {"type": "string"},
                                "next_step_days": {"type": "number"}
                            },
                            "required": ["document_template", "next_step_days"]
                        },
                        "should_be_cancelled": {
                            "type": "object",
                            "properties": {
                                "document_template": {"type": "string"},
                                "next_step_days": {"type": "number"}
                            },
                            "required": ["document_template", "next_step_days"]
                        },
                        "should_be_evicted_threshold": {
                            "type": "object",
                            "properties": {
                                "document_template": {"type": "string"},
                                "legal_proceeding_start": {"type": "number"}
                            },
                            "required": ["document_template", "legal_proceeding_start"]
                        },
                        "should_be_sued": {
                            "type": "object",
                            "properties": {
                                "document_template": {"type": "string"},
                                "next_step_days": {"type": "number"}
                            },
                            "required": ["document_template", "next_step_days"]
                        }
                    },
                    "required": ["should_be_warned", "should_be_cancelled", "should_be_evicted_threshold", "should_be_sued"]
                }
            },
            "required": ["decision_thresholds", "action_steps"]
        }
        self.config_data = self.load_config()

    def validate_config(self, config):
        try:
            validate(instance=config, schema=self.config_schema)
        except ValidationError as e:
            raise ValueError(f"Configuration validation error: {e.message}")

    def load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                config = json.load(file)
                self.validate_config(config)
                return config
        except FileNotFoundError:
            default_config = self.default_config()
            self.save_config(default_config)
            return default_config
        except json.JSONDecodeError:
            print("Error reading the config file. Please check its format.")
            return self.default_config()
        except Exception as e:
            print(f"An error occurred: {e}")
            return self.default_config()

    def default_config(self):
        return {
            "decision_thresholds": {
                "should_be_warned_threshold": 30,
                "warned_threshold": 30,
                "should_be_cancelled_threshold": 60,
                "cancelled_threshold": 60,
                "should_be_sued_threshold": 90,
                "lawsuit_threshold": 90,
                "should_be_evicted_threshold": 100,
                "eviction_threshold": 100
            },
            "action_steps": {
                "should_be_warned": {
                    "document_template": "warning_template.txt",
                    "next_step_days": 30
                },
                "should_be_cancelled": {
                    "document_template": "cancellation_template.txt",
                    "next_step_days": 30
                },
                "should_be_evicted": {
                    "document_template": "eviction_template.txt",
                    "legal_proceeding_start": 10
                },
                "should_be_sued": {
                    "document_template": "lawsuit_template.txt",  
                    "next_step_days": 7 
                }
            }
        }

    def save_config(self, config=None):
        if config is not None:
            self.config_data = config
        try:
            self.validate_config(self.config_data)
            with open(self.config_path, 'w') as file:
                json.dump(self.config_data, file, indent=4)
            print("Configuration saved successfully.")
        except Exception as e:
            print(f"Failed to save configuration: {e}")

    def update_config(self, new_config_data):
        try:
            # Validate the new configuration data
            self.validate_config(new_config_data)
            
            # If validation passes, assign the new configuration to self.config_data
            self.config_data = new_config_data
            
            # Save the updated configuration to the file
            self.save_config()
        except Exception as e:
            print(f"Failed to update configuration: {e}")
            raise


    def get_config(self):
        return self.config_data
