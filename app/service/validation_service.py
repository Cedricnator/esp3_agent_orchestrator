from fastapi import UploadFile, HTTPException

class ValidationService:
    MAX_FILE_SIZE_MB = 5
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_MIME_TYPES = ["image/jpeg", "image/png"]

    def validate_image(self, image: UploadFile, image_bytes: bytes):
        """
        Validates the image file for MIME type and size.
        Raises HTTPException if invalid.
        """
        # 1. MIME Type Check
        if image.content_type not in self.ALLOWED_MIME_TYPES:
             raise HTTPException(
                 status_code=415, 
                 detail=f"Unsupported Media Type. Allowed: {', '.join(self.ALLOWED_MIME_TYPES)}"
             )

        # 2. Size Check
        if len(image_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413, 
                detail=f"Payload too large. Max size is {self.MAX_FILE_SIZE_MB}MB."
            )
        
        return True
