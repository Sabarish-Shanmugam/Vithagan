import os
import yaml
import logging
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, config_path="config/ai_settings.yaml"):
        """
        Initialize the Gemini Client with settings from the config file.
        """
        self.config = self._load_config(config_path)
        self.api_key = self._get_api_key()
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = self.config.get("model_name", "gemini-1.5-flash")
        self.system_prompt = self.config.get("system_prompt", "")

    def _load_config(self, config_path):
        """
        Load configuration from YAML file.
        """
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Config file not found at {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            raise

    def _get_api_key(self):
        """
        Retrieve API key from config or environment variable.
        """
        api_key = self.config.get("api_key")
        if not api_key:
            # Securely retrieve from environment variable
            api_key = os.environ.get("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("API Key not found. Please set it in config/ai_settings.yaml or GOOGLE_API_KEY env var.")
        
        return api_key

    def generate_yaml(self, user_prompt):
        """
        Generate YAML configuration from user prompt using Gemini.
        """
        try:
            logger.info(f"Sending request to Gemini model: {self.model_name}")
            
            response = self.client.models.generate_content(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.2, # Low temperature for more deterministic output
                ),
                contents=[user_prompt]
            )
            
            if not response.text:
                raise ValueError("Empty response received from Gemini.")

            cleaned_yaml = self._clean_output(response.text)
            self._validate_yaml(cleaned_yaml)
            
            return cleaned_yaml

        except Exception as e:
            logger.error(f"Error generating YAML: {e}")
            raise

    def _clean_output(self, text):
        """
        Remove markdown code blocks if present.
        """
        text = text.strip()
        if text.startswith("```yaml"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
            
        return text.strip()

    def _validate_yaml(self, yaml_str):
        """
        Basic validation to ensure the output is valid YAML.
        """
        try:
            parsed = yaml.safe_load(yaml_str)
            if not isinstance(parsed, dict):
                raise ValueError("Generated YAML is not a dictionary.")
            if "requirements" not in parsed:
                raise ValueError("Generated YAML missing 'requirements' key.")
            return True
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML generated: {e}")

if __name__ == "__main__":
    # Simple test
    try:
        client = GeminiClient()
        print("GeminiClient initialized successfully.")
    except Exception as e:
        print(f"Initialization failed: {e}")
