from fastapi import APIRouter, UploadFile, File, HTTPException
import random

router = APIRouter()

@router.post("/analyze")
async def analyze_tire(file: UploadFile = File(...)):
    try:
        # Read the image (we're not actually processing it in this mock version)
        await file.read()  # Just read the file but don't use it

        # Generate a random condition score for demo purposes
        condition_score = random.uniform(0.3, 0.9)

        # Generate analysis results
        results = {
            "condition": condition_score,
            "treadDepth": f"{(condition_score * 10):.1f}mm",
            "wearPattern": "Even wear" if condition_score > 0.7 else "Uneven wear",
            "estimatedLife": f"{int(condition_score * 20000)} km",
            "recommendations": []
        }

        # Add recommendations based on condition
        if condition_score > 0.8:
            results["recommendations"] = [
                "Tire is in excellent condition",
                "Continue regular maintenance",
                "Check pressure monthly"
            ]
        elif condition_score > 0.6:
            results["recommendations"] = [
                "Consider rotation in next 5,000 km",
                "Monitor tread wear patterns",
                "Check alignment in next service"
            ]
        else:
            results["recommendations"] = [
                "Schedule tire replacement soon",
                "Reduce speed in wet conditions",
                "Check for uneven wear patterns"
            ]

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))