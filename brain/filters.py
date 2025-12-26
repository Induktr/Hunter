import re

class ContentFilter:
    """
    Class for primary vacancy filtering.
    """
    
    STOP_WORDS = [
        r"casino", r"crypto", r"sales", r"gambling", r"office",
        r"казино", r"крипта", r"продажи", r"гемблинг", r"офис"
    ]
    
    KEY_WORDS = [
        r"react", r"frontend", r"js", r"typescript", r"next\.js",
        r"python", r"backend", r"node" 
    ]

    @classmethod
    def check(cls, text: str) -> bool:
        """
        Runs both Hard and Soft filters.
        Returns True if passed, False otherwise.
        """
        if not text:
            return False
            
        text_lower = text.lower()

        # Hard Filter: Stop words
        for stop_word in cls.STOP_WORDS:
            if re.search(stop_word, text_lower):
                return False

        # Soft Filter: Key words
        found_key = False
        for key_word in cls.KEY_WORDS:
            if re.search(key_word, text_lower):
                found_key = True
                break
        
        if not found_key:
            return False

        return True
