import os
from dotenv import load_dotenv

load_dotenv()

class KeyManager:
    def __init__(self):
        # Load keys from string "key1,key2,key3" -> list ["key1", "key2", "key3"]
        keys_str = os.getenv("GEMINI_API_KEYS", "")
        self.keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        
        if not self.keys:
            raise ValueError("❌ No Gemini Keys found in .env! Set GEMINI_API_KEYS.")
            
        self.current_index = 0
        print(f"🔑 KeyManager initialized with {len(self.keys)} keys.")

    def get_current_key(self):
        """Returns the currently active key."""
        return self.keys[self.current_index]

    def rotate(self):
        """Switches to the next key. Returns False if we've cycled through all."""
        next_index = (self.current_index + 1) % len(self.keys)
        
        if next_index == 0:
            # We looped back to the start. In a strict rotation, we might want to stop here 
            # or just warn that we are reusing keys.
            print("⚠️ KeyManager: Warning! Cycled through ALL keys. Reusing the first one.")
        
        self.current_index = next_index
        print(f"🔄 KeyManager: Rotated to Key #{self.current_index + 1}")
        return self.get_current_key()

# Create a singleton instance
key_rotator = KeyManager()