"""
Automated Car Damage Assessment & Insurance Claims Engine
FastAPI Inference Microservice
Exposes /api/assess, /api/health, and /api/sample-images
"""

import os
import io
import time
import json
import base64
import pickle
import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms, models

import cv2
from skimage.feature import hog
from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
import pdf_generator
import academic_pdf_generator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
DATASET_VAL_DIR = os.path.join(BASE_DIR, "dataset", "data3a", "validation")

app = FastAPI(
    title="Car Damage Severity & Insurance Claims AI Engine",
    description="Multimodal CV Engine combining CNN (MobileNetV2), SVM+HOG, K-Means HSV Clustering, and Random Forest Ensemble.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model singletons
cnn_model = None
svm_model = None
rf_model = None

CLASS_INFO = {
    0: {
        "key": "01-minor",
        "name": "Minor Damage",
        "badge_color": "emerald",
        "description": "Superficial scratches, light paint scuffs, or minor cosmetic surface dents.",
        "payout_strategy": "Fast-Track Straight-Through Processing (STP Instant Approval)"
    },
    1: {
        "key": "02-moderate",
        "name": "Moderate Damage",
        "badge_color": "amber",
        "description": "Noticeable body panel deformation, bumper cracks, light fender collision.",
        "payout_strategy": "Automated Secondary Cost Appraisal & Digital Review"
    },
    2: {
        "key": "03-severe",
        "name": "Severe Damage",
        "badge_color": "rose",
        "description": "Structural frame deformation, major impact collision, potential suspension damage.",
        "payout_strategy": "Physical Field Appraiser Validation Mandatory"
    }
}

COST_TIER_INFO = {
    0: {
        "tier": "Low Tier",
        "badge": "LOW",
        "cost_usd": "$250 - $750",
        "cost_inr": "INR 18,000 - 55,000",
        "turnaround": "< 24 Hours",
        "action": "Immediate Automated Settlement Payout"
    },
    1: {
        "tier": "Medium Tier",
        "badge": "MEDIUM",
        "cost_usd": "$750 - $2,200",
        "cost_inr": "INR 55,000 - 1,65,000",
        "turnaround": "24 - 48 Hours",
        "action": "Authorized Bodyshop Repair Estimate Validation"
    },
    2: {
        "tier": "High Tier",
        "badge": "HIGH",
        "cost_usd": "$2,200 - $6,800+",
        "cost_inr": "INR 1,65,000 - 5,00,000+",
        "turnaround": "3 - 5 Days",
        "action": "Full Structural Loss / On-Site Inspection Appraisal"
    }
}


def load_models():
    global cnn_model, svm_model, rf_model
    cnn_path = os.path.join(ARTIFACTS_DIR, "cnn_model.pth")
    svm_path = os.path.join(ARTIFACTS_DIR, "svm_hog_model.pkl")
    rf_path = os.path.join(ARTIFACTS_DIR, "random_forest_model.pkl")

    if os.path.exists(cnn_path):
        weights = models.MobileNet_V2_Weights.DEFAULT
        model = models.mobilenet_v2(weights=weights)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_features, 128),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(128, 3)
        )
        model.load_state_dict(torch.load(cnn_path, map_location=DEVICE))
        model.to(DEVICE)
        model.eval()
        cnn_model = model
        print("[OK] MobileNetV2 CNN Model loaded.")

    if os.path.exists(svm_path):
        with open(svm_path, "rb") as f:
            svm_model = pickle.load(f)
        print("[OK] SVM + HOG Model loaded.")

    if os.path.exists(rf_path):
        with open(rf_path, "rb") as f:
            rf_model = pickle.load(f)
        print("[OK] Random Forest Model loaded.")


@app.on_event("startup")
def startup_event():
    database.init_db()
    load_models()


# Preprocessing transforms
val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


def process_image_cv(image_bytes: bytes):
    """Parses image and returns RGB, Grayscale, and Base64 original."""
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    rgb_arr = np.array(pil_img)
    gray_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2GRAY)
    return pil_img, rgb_arr, gray_arr


def run_member1_cnn(pil_img: Image.Image):
    """Member 1: MobileNetV2 damage severity classification."""
    global cnn_model
    if cnn_model is None:
        load_models()
    tensor_img = val_transform(pil_img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        outputs = cnn_model(tensor_img)
        probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]
    pred_id = int(np.argmax(probs))
    conf = float(probs[pred_id])
    return {
        "class_id": pred_id,
        "class_name": CLASS_INFO[pred_id]["name"],
        "confidence": round(conf * 100, 2),
        "probabilities": {
            "minor": round(float(probs[0]) * 100, 2),
            "moderate": round(float(probs[1]) * 100, 2),
            "severe": round(float(probs[2]) * 100, 2),
        },
        "description": CLASS_INFO[pred_id]["description"]
    }


def run_member2_svm_hog(gray_arr: np.ndarray):
    """Member 2: Classical SVM + HOG structural frame deformation detection."""
    global svm_model
    if svm_model is None:
        load_models()
    resized_gray = cv2.resize(gray_arr, (128, 128))
    features = hog(
        resized_gray,
        orientations=9,
        pixels_per_cell=(8, 8),
        cells_per_block=(2, 2),
        block_norm='L2-Hys',
        transform_sqrt=True
    ).reshape(1, -1)

    flag = int(svm_model.predict(features)[0])
    probs = svm_model.predict_proba(features)[0]
    deform_prob = round(float(probs[1]) * 100, 2)
    return {
        "deformation_flag": flag,
        "status": "STRUCTURAL DEFORMATION DETECTED" if flag == 1 else "FRAME STRUCTURALLY INTACT",
        "deformation_probability": deform_prob,
        "severity_grade": "Critical Chassis Damage" if flag == 1 else "Cosmetic Outer Panel",
        "hog_features_extracted": features.shape[1]
    }


def run_member3_kmeans_segmentation(rgb_arr: np.ndarray):
    """Member 3: Unsupervised K-Means HSV color-space pixel clustering."""
    h, w, _ = rgb_arr.shape
    scale_w, scale_h = 240, 240
    resized_rgb = cv2.resize(rgb_arr, (scale_w, scale_h))
    hsv = cv2.cvtColor(resized_rgb, cv2.COLOR_RGB2HSV)

    pixels = hsv.reshape((-1, 3)).astype(np.float32)

    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=3, n_init=3, max_iter=80, random_state=42)
    labels = kmeans.fit_predict(pixels)

    cluster_counts = np.bincount(labels)
    sorted_clusters = np.argsort(cluster_counts)
    damage_cluster = sorted_clusters[0] if cluster_counts[sorted_clusters[0]] > 50 else sorted_clusters[1]

    mask = (labels == damage_cluster).reshape((scale_h, scale_w)).astype(np.uint8) * 255
    kernel = np.ones((3, 3), np.uint8)
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_DILATE, kernel)

    # Resize mask back to original image dimensions
    mask_full = cv2.resize(mask_clean, (w, h), interpolation=cv2.INTER_NEAREST)

    # Compute percentage
    damaged_pixels = int(np.sum(mask_full > 0))
    total_pixels = w * h
    damage_area_pct = round((damaged_pixels / total_pixels) * 100.0, 2)

    # Generate visual heatmap overlay
    overlay = rgb_arr.copy()
    # Neon crimson red overlay on damage pixels: (255, 30, 80)
    overlay[mask_full > 0] = [239, 68, 68]
    blended = cv2.addWeighted(rgb_arr, 0.60, overlay, 0.40, 0)

    # Draw contours
    contours, _ = cv2.findContours(mask_full, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(blended, contours, -1, (244, 63, 94), 2)

    # Convert blended overlay to base64
    pil_overlay = Image.fromarray(blended)
    buf = io.BytesIO()
    pil_overlay.save(buf, format="JPEG", quality=85)
    overlay_base64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "damage_area_pct": damage_area_pct,
        "affected_pixels": damaged_pixels,
        "total_pixels": total_pixels,
        "cluster_count": 3,
        "visual_overlay_base64": overlay_base64
    }


def run_member4_random_forest_fusion(class_id: int, deform_flag: int, area_pct: float):
    """Member 4: Random Forest tabular fusion predicting repair cost tier."""
    global rf_model
    if rf_model is None:
        load_models()

    features = np.array([[class_id, deform_flag, area_pct]])
    tier_id = int(rf_model.predict(features)[0])
    probs = rf_model.predict_proba(features)[0]

    tier_meta = COST_TIER_INFO[tier_id]
    return {
        "tier_id": tier_id,
        "tier_name": tier_meta["tier"],
        "tier_badge": tier_meta["badge"],
        "estimated_cost_usd": tier_meta["cost_usd"],
        "estimated_cost_inr": tier_meta["cost_inr"],
        "turnaround_sla": tier_meta["turnaround"],
        "recommended_action": tier_meta["action"],
        "tier_probabilities": {
            "low": round(float(probs[0]) * 100, 2),
            "medium": round(float(probs[1]) * 100, 2),
            "high": round(float(probs[2]) * 100, 2)
        }
    }


@app.post("/api/assess")
async def assess_car_damage(file: UploadFile = File(...)):
    """
    Main multimodal assessment endpoint.
    Accepts image file, executes 4-member ensemble pipeline, returns structured appraisal.
    """
    try:
        contents = await file.read()
        pil_img, rgb_arr, gray_arr = process_image_cv(contents)

        # 1. Member 1: CNN
        m1_result = run_member1_cnn(pil_img)

        # 2. Member 2: SVM + HOG
        m2_result = run_member2_svm_hog(gray_arr)

        # 3. Member 3: K-Means HSV
        m3_result = run_member3_kmeans_segmentation(rgb_arr)

        # 4. Member 4: Random Forest Feature Fusion
        m4_result = run_member4_random_forest_fusion(
            class_id=m1_result["class_id"],
            deform_flag=m2_result["deformation_flag"],
            area_pct=m3_result["damage_area_pct"]
        )

        return {
            "status": "success",
            "filename": file.filename,
            "overall_severity": m1_result["class_name"],
            "repair_cost_tier": m4_result["tier_name"],
            "payout_strategy": CLASS_INFO[m1_result["class_id"]]["payout_strategy"],
            "member_outputs": {
                "member_1_cnn": m1_result,
                "member_2_svm_hog": m2_result,
                "member_3_kmeans": m3_result,
                "member_4_random_forest": m4_result
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@app.get("/api/sample-images")
def get_sample_images():
    """Returns a list of sample vehicle images from validation set for instant 1-click testing."""
    sample_meta = {
        "01-minor": {
            "vehicle_model": "2024 Honda Civic Sport",
            "vin": "1HGCR2F83HA109281",
            "policy_no": "POL-884920-IND",
            "incident_description": "Front bumper cosmetic scuff and clearcoat abrasion in parking garage."
        },
        "02-moderate": {
            "vehicle_model": "2023 Hyundai Creta SX",
            "vin": "MALC381CLPM194820",
            "policy_no": "POL-441920-IND",
            "incident_description": "Passenger fender collision and bumper panel deformation during intersection braking."
        },
        "03-severe": {
            "vehicle_model": "2025 Tata Harrier Fearless",
            "vin": "MAT624510P8920194",
            "policy_no": "POL-992140-IND",
            "incident_description": "High-speed highway impact with structural chassis crumple and radiator support collapse."
        }
    }

    samples = []
    if os.path.exists(DATASET_VAL_DIR):
        for class_folder in ["01-minor", "02-moderate", "03-severe"]:
            folder_p = os.path.join(DATASET_VAL_DIR, class_folder)
            if os.path.exists(folder_p):
                files = [f for f in os.listdir(folder_p) if f.lower().endswith(('.jpg', '.jpeg', '.png'))][:3]
                meta = sample_meta.get(class_folder, {})
                for f in files:
                    img_path = os.path.join(folder_p, f)
                    with open(img_path, "rb") as img_f:
                        b64 = "data:image/jpeg;base64," + base64.b64encode(img_f.read()).decode("utf-8")
                    samples.append({
                        "filename": f,
                        "expected_category": class_folder,
                        "label": CLASS_INFO[int(class_folder[:2])-1]["name"],
                        "vehicle_model": meta.get("vehicle_model", "Automotive Assessment Unit"),
                        "vin": meta.get("vin", "VIN-NOT-SPECIFIED"),
                        "policy_no": meta.get("policy_no", "POL-DEFAULT"),
                        "incident_description": meta.get("incident_description", "Vehicle damage inspection."),
                        "data_url": b64
                    })
    return {"samples": samples}


@app.get("/api/health")
def health_check():
    global cnn_model, svm_model, rf_model
    return {
        "status": "online",
        "device": str(DEVICE),
        "models_loaded": {
            "cnn_mobilenet_v2": cnn_model is not None,
            "svm_hog": svm_model is not None,
            "random_forest": rf_model is not None
        }
    }


class ClaimRequest(BaseModel):
    policy_number: str
    claimant_name: str
    vehicle_vin: str
    incident_date: str
    incident_description: str
    severity_grade: str
    repair_cost_tier: str
    estimated_cost_usd: str
    estimated_cost_inr: str
    damage_area_pct: float
    deformation_flag: int


@app.post("/api/file-claim")
def file_insurance_claim(claim: ClaimRequest):
    """
    Automated Claims Adjudication Engine.
    Evaluates damage metrics against underwriting thresholds to determine instant STP payout.
    """
    import random
    import hashlib

    claim_id = f"CLM-2026-{random.randint(10000, 99999)}"
    token_seed = f"{claim.policy_number}-{claim.vehicle_vin}-{time.time()}"
    auth_token = hashlib.sha256(token_seed.encode()).hexdigest()[:16].upper()

    # Adjudication Decision Tree
    if claim.deformation_flag == 0 and (claim.severity_grade == "Minor Damage" or claim.damage_area_pct < 18.0):
        decision = "INSTANT_STP_APPROVED"
        status_label = "Instant Payout Approved"
        badge_type = "APPROVED"
        action_note = "Straight-Through Processing (STP) triggered. 100% automated payout approved without manual adjuster delay."
        turnaround = "Immediate (< 2 Hours)"
        deductible_usd = "$250"
        deductible_inr = "INR 5,000"
    elif claim.deformation_flag == 0:
        decision = "PRE_AUTHORIZED_NETWORK_GARAGE"
        status_label = "Pre-Authorized Network Repair"
        badge_type = "PRE_AUTH"
        action_note = "Damage within cosmetic thresholds. Dispatched digital estimate authorization to nearest certified bodyshop."
        turnaround = "24 Hours"
        deductible_usd = "$500"
        deductible_inr = "INR 10,000"
    else:
        decision = "FIELD_APPRAISAL_DISPATCHED"
        status_label = "Physical Surveyor Required"
        badge_type = "FIELD_DISPATCH"
        action_note = "Structural frame deformation detected. Certified on-site automotive surveyor dispatched for chassis integrity audit."
        turnaround = "24 - 48 Hours"
        deductible_usd = "$1,000"
        deductible_inr = "INR 25,000"

    res_data = {
        "claim_id": claim_id,
        "auth_token": auth_token,
        "submission_time": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "decision": decision,
        "status_label": status_label,
        "badge_type": badge_type,
        "action_note": action_note,
        "turnaround": turnaround,
        "deductible_usd": deductible_usd,
        "deductible_inr": deductible_inr,
        "estimated_net_settlement_usd": claim.estimated_cost_usd,
        "estimated_net_settlement_inr": claim.estimated_cost_inr,
        "damage_area_pct": claim.damage_area_pct,
        "deformation_flag": claim.deformation_flag,
        "claim_summary": {
            "policy_number": claim.policy_number,
            "claimant": claim.claimant_name,
            "vehicle_vin": claim.vehicle_vin,
            "incident_date": claim.incident_date,
            "incident_description": claim.incident_description,
            "damage_severity": claim.severity_grade,
            "repair_tier": claim.repair_cost_tier,
            "damage_area": f"{claim.damage_area_pct}%",
            "frame_deformation": "YES (Structural)" if claim.deformation_flag == 1 else "NO (Intact)"
        }
    }

    # Persist claim to SQLite database
    database.insert_claim(res_data)
    print(f"[DB] Claim {claim_id} saved to SQLite.")

    return res_data


@app.get("/api/claims")
def list_claims():
    """Returns all historical insurance claims from SQLite database."""
    return {"claims": database.fetch_all_claims()}


@app.get("/api/claims/{claim_id}")
def get_claim(claim_id: str):
    """Fetches full claim record from SQLite."""
    claim = database.fetch_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@app.get("/api/claims/{claim_id}/pdf")
def download_claim_pdf(claim_id: str):
    """Generates and serves downloadable official Insurance Claim Settlement PDF."""
    claim = database.fetch_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    pdf_bytes = pdf_generator.generate_claim_pdf(claim)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Claim_Policy_{claim_id}.pdf"}
    )


@app.get("/api/defense-pdf")
def download_defense_dossier_pdf():
    """Generates and serves downloadable Academic Viva Defense Dossier & Model Telemetry PDF."""
    metrics_path = os.path.join(ARTIFACTS_DIR, "training_metrics.json")
    metrics_data = None
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                metrics_data = json.load(f)
        except Exception:
            pass
    pdf_bytes = academic_pdf_generator.build_academic_defense_pdf(metrics_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Vanguard_ClaimOS_Academic_Defense_Dossier.pdf"}
    )


class SessionStatePayload(BaseModel):
    state: dict


@app.post("/api/session-state")
def save_appraisal_session_state(payload: SessionStatePayload):
    """Persists active appraisal UI state into Neon PostgreSQL."""
    success = database.save_session_state(payload.state)
    return {"status": "success", "saved": success}


@app.get("/api/session-state")
def get_appraisal_session_state():
    """Retrieves active appraisal UI state from Neon PostgreSQL."""
    state = database.get_session_state()
    return {"status": "success", "state": state}


@app.get("/api/metrics")
def get_training_metrics():
    """Returns the comprehensive academic model metrics, confusion matrix, and feature importances."""
    metrics_path = os.path.join(ARTIFACTS_DIR, "training_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {
        "status": "training_in_progress",
        "message": "Metrics will be populated once training pipeline finishes."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
