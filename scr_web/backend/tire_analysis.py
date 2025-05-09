from fastapi import APIRouter, UploadFile, File, HTTPException
#import tensorflow as tf
import numpy as np
#from PIL import Image
import io

router = APIRouter()

# Load the model
#model = tf.keras.models.load_model("assets/model_2025_01_19_20_27_18.h5")

#@router.post("/analyze")
#async def analyze_tire(file: UploadFile = File(...)):
#    try:
#        # Read and preprocess the image
#        contents = await file.read()
#        image = Image.open(io.BytesIO(contents))
#        image = image.resize((224, 224))  # Resize to match model input size
#        image = np.array(image)
#        image = np.expand_dims(image, axis=0)
        
#        # Make prediction
#        prediction = model.predict(image)
#        condition_score = float(prediction[0][0])  # Assuming model outputs a single score
        
#        # Generate analysis results
#        results = {
#            "condition": condition_score,
#            "treadDepth": f"{(condition_score * 10):.1f}mm",
#            "wearPattern": "Even wear" if condition_score > 0.7 else "Uneven wear",
#            "estimatedLife": f"{int(condition_score * 20000)} km",
#            "recommendations": []
#        }
        
#        # Add recommendations based on condition
#        if condition_score > 0.8:
#            results["recommendations"] = [
#                "Tire is in excellent condition",
#                "Continue regular maintenance",
#                "Check pressure monthly"
#            ]
#        elif condition_score > 0.6:
#            results["recommendations"] = [
#                "Consider rotation in next 5,000 km",
#                "Monitor tread wear patterns",
#                "Check alignment in next service"
#            ]
#        else:
#            results["recommendations"] = [
#                "Schedule tire replacement soon",
#                "Reduce speed in wet conditions",
#                "Check for uneven wear patterns"
#            ]
            
#        return results
        
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))