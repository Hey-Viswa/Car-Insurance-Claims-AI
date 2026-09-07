"""
Enterprise Database Adapter for Vanguard ClaimOS
Supports Neon Serverless PostgreSQL with automatic SQLite local fallback
"""

import os
import json
import sqlite3
from typing import Optional, List, Dict, Any

# Connection String from Environment or User Provided Neon Serverless Database
NEON_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_enkrBljx35SA@ep-damp-tooth-aeq9sb5v-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claims.db")

USE_POSTGRES = False

try:
    import psycopg2
    import psycopg2.extras
    # Test connection on module load
    test_conn = psycopg2.connect(NEON_DATABASE_URL, connect_timeout=5)
    test_conn.close()
    USE_POSTGRES = True
    print("[DB] Neon Serverless PostgreSQL connected successfully.")
except Exception as e:
    print("[DB] Neon PostgreSQL connection failed, defaulting to SQLite:", e)
    USE_POSTGRES = False


def get_pg_connection():
    return psycopg2.connect(NEON_DATABASE_URL)


def get_sqlite_connection():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables on Neon PostgreSQL and local SQLite."""
    # 1. Initialize PostgreSQL if available
    if USE_POSTGRES:
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id TEXT PRIMARY KEY,
                    auth_token TEXT,
                    policy_number TEXT,
                    claimant_name TEXT,
                    vehicle_vin TEXT,
                    incident_date TEXT,
                    incident_description TEXT,
                    overall_severity TEXT,
                    repair_cost_tier TEXT,
                    damage_area_pct REAL,
                    deformation_flag INTEGER,
                    estimated_cost_usd TEXT,
                    estimated_cost_inr TEXT,
                    deductible_usd TEXT,
                    deductible_inr TEXT,
                    decision TEXT,
                    status_label TEXT,
                    badge_type TEXT,
                    action_note TEXT,
                    turnaround TEXT,
                    created_at TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS session_state (
                    session_key TEXT PRIMARY KEY,
                    state_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("[DB] Neon PostgreSQL tables verified/created.")
        except Exception as err:
            print("[DB] Error initializing PostgreSQL:", err)

    # 2. Always maintain local SQLite for edge reliability
    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                auth_token TEXT,
                policy_number TEXT,
                claimant_name TEXT,
                vehicle_vin TEXT,
                incident_date TEXT,
                incident_description TEXT,
                overall_severity TEXT,
                repair_cost_tier TEXT,
                damage_area_pct REAL,
                deformation_flag INTEGER,
                estimated_cost_usd TEXT,
                estimated_cost_inr TEXT,
                deductible_usd TEXT,
                deductible_inr TEXT,
                decision TEXT,
                status_label TEXT,
                badge_type TEXT,
                action_note TEXT,
                turnaround TEXT,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS session_state (
                session_key TEXT PRIMARY KEY,
                state_json TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("[DB] SQLite database initialized at:", SQLITE_PATH)
    except Exception as err:
        print("[DB] Error initializing SQLite:", err)


def insert_claim(claim_data: dict):
    """Inserts a new claim into Neon PostgreSQL and local SQLite."""
    summary = claim_data.get("claim_summary", {})
    record = (
        claim_data["claim_id"],
        claim_data["auth_token"],
        summary.get("policy_number", claim_data.get("policy_number", "")),
        summary.get("claimant", claim_data.get("claimant_name", "")),
        summary.get("vehicle_vin", claim_data.get("vehicle_vin", "")),
        summary.get("incident_date", claim_data.get("incident_date", "")),
        summary.get("incident_description", claim_data.get("incident_description", "")),
        summary.get("damage_severity", claim_data.get("overall_severity", "")),
        summary.get("repair_tier", claim_data.get("repair_cost_tier", "")),
        claim_data.get("damage_area_pct", 0.0),
        claim_data.get("deformation_flag", 0),
        claim_data.get("estimated_net_settlement_usd", claim_data.get("estimated_cost_usd", "")),
        claim_data.get("estimated_net_settlement_inr", claim_data.get("estimated_cost_inr", "")),
        claim_data.get("deductible_usd", "$250"),
        claim_data.get("deductible_inr", "INR 5,000"),
        claim_data.get("decision", "APPROVED"),
        claim_data.get("status_label", "Approved"),
        claim_data.get("badge_type", "APPROVED"),
        claim_data.get("action_note", ""),
        claim_data.get("turnaround", "24 Hours"),
        claim_data.get("submission_time", "")
    )

    # Insert into Neon PostgreSQL
    if USE_POSTGRES:
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO claims (
                    claim_id, auth_token, policy_number, claimant_name, vehicle_vin,
                    incident_date, incident_description, overall_severity, repair_cost_tier,
                    damage_area_pct, deformation_flag, estimated_cost_usd, estimated_cost_inr,
                    deductible_usd, deductible_inr, decision, status_label, badge_type,
                    action_note, turnaround, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (claim_id) DO UPDATE SET
                    status_label = EXCLUDED.status_label,
                    decision = EXCLUDED.decision;
            """, record)
            conn.commit()
            cur.close()
            conn.close()
            print(f"[DB-NEON] Claim {claim_data['claim_id']} persisted to Neon PostgreSQL.")
        except Exception as e:
            print(f"[DB-NEON] Failed to insert claim into Neon: {e}")

    # Mirror into local SQLite
    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO claims (
                claim_id, auth_token, policy_number, claimant_name, vehicle_vin,
                incident_date, incident_description, overall_severity, repair_cost_tier,
                damage_area_pct, deformation_flag, estimated_cost_usd, estimated_cost_inr,
                deductible_usd, deductible_inr, decision, status_label, badge_type,
                action_note, turnaround, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, record)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB-SQLITE] Failed to insert claim into SQLite: {e}")


def fetch_all_claims() -> List[Dict[str, Any]]:
    """Retrieves all historical claims, querying Neon PostgreSQL first."""
    if USE_POSTGRES:
        try:
            conn = get_pg_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM claims ORDER BY created_at DESC;")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            claims = []
            for r in rows:
                claims.append(dict(r))
            return claims
        except Exception as e:
            print("[DB-NEON] Error fetching from Neon, falling back to SQLite:", e)

    # SQLite fallback
    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM claims ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()
        claims = [dict(r) for r in rows]
        return claims
    except Exception as e:
        print("[DB-SQLITE] Error fetching from SQLite:", e)
        return []


def fetch_claim_by_id(claim_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single claim by reference ID."""
    if USE_POSTGRES:
        try:
            conn = get_pg_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM claims WHERE claim_id = %s;", (claim_id,))
            r = cur.fetchone()
            cur.close()
            conn.close()
            if r:
                return dict(r)
        except Exception as e:
            print("[DB-NEON] Error fetching claim from Neon:", e)

    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,))
        r = cur.fetchone()
        conn.close()
        if r:
            return dict(r)
    except Exception as e:
        print("[DB-SQLITE] Error fetching claim from SQLite:", e)
    return None


def save_session_state(state: dict, session_key: str = "active_appraisal") -> bool:
    """Saves user active appraisal UI state so page reloads never lose progress."""
    state_str = json.dumps(state)

    if USE_POSTGRES:
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO session_state (session_key, state_json)
                VALUES (%s, %s)
                ON CONFLICT (session_key) DO UPDATE SET
                    state_json = EXCLUDED.state_json,
                    updated_at = CURRENT_TIMESTAMP;
            """, (session_key, state_str))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("[DB-NEON] Error saving session state to Neon:", e)

    # Save to SQLite
    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO session_state (session_key, state_json, updated_at)
            VALUES (?, ?, datetime('now'))
        """, (session_key, state_str))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("[DB-SQLITE] Error saving session state to SQLite:", e)
        return False


def get_session_state(session_key: str = "active_appraisal") -> Optional[Dict[str, Any]]:
    """Retrieves active appraisal UI state."""
    if USE_POSTGRES:
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("SELECT state_json FROM session_state WHERE session_key = %s;", (session_key,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[0]:
                return json.loads(row[0])
        except Exception as e:
            print("[DB-NEON] Error retrieving session state from Neon:", e)

    # SQLite
    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT state_json FROM session_state WHERE session_key = ?", (session_key,))
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
    except Exception as e:
        print("[DB-SQLITE] Error retrieving session state from SQLite:", e)
    return None
