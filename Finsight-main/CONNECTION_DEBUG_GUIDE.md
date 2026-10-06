# FinSight Connection Debugging & Performance Guide

## 🔍 Connection Issues Root Cause Analysis

### Current Connection Architecture
The application has two critical external connections:
1. **Supabase** (PostgreSQL-based audit persistence)
2. **Gemini AI** (Google's generative AI API)

Both connections are checked via the sidebar "Check connections" button.

---

## 🐛 Common Connection Faults & Fixes

### **FAULT 1: Supabase Connection Timeout (Most Frequent)**

**Symptoms:**
- "Supabase audit_events is not reachable"
- Audit log not saving
- Slow page loads (5-30s delay)

**Root Causes:**
1. **Missing Environment Variables**
   ```
   SUPABASE_URL not set or empty
   SUPABASE_KEY not set or empty
   ```

2. **Network Connectivity**
   - Firewall blocking Supabase API calls
   - DNS resolution failure
   - ISP rate limiting

3. **Database Schema Mismatch**
   - Missing `audit_events` table
   - Incorrect column definitions (error code 42703)

**Fixes:**

```bash
# Step 1: Verify Environment
cat .env | grep -E "SUPABASE_(URL|KEY)"

# Step 2: Test connectivity
python3 -c "
from src.persistence import test_supabase_connection
ok, msg = test_supabase_connection()
print(f'Connection: {ok}')
print(f'Message: {msg}')
"

# Step 3: If schema error, run SQL fix
# In Supabase Dashboard > SQL Editor, execute:
CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50) NOT NULL,
    invoice_id VARCHAR(100),
    message TEXT,
    metadata JSONB,
    CONSTRAINT audit_events_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_audit_events_invoice_id ON audit_events(invoice_id);
CREATE INDEX idx_audit_events_created_at ON audit_events(created_at DESC);
```

**Advanced Debugging (High Latency Issue):**
```python
import time
import requests
from src.persistence import _secret

url = _secret("SUPABASE_URL")
if url:
    print(f"Testing: {url}")
    start = time.time()
    try:
        resp = requests.get(f"{url}/rest/v1/", timeout=5, 
                           headers={"apikey": _secret("SUPABASE_KEY")})
        elapsed = time.time() - start
        print(f"Response time: {elapsed:.2f}s, Status: {resp.status_code}")
        if elapsed > 2:
            print("⚠️ HIGH LATENCY - Consider:")
            print("  - Regional proximity (is your Supabase in the right region?)")
            print("  - Connection pooling (upgrade Supabase tier)")
            print("  - Batch operations (current code chunks at 500 rows)")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
```

---

### **FAULT 2: Gemini API Connection Failures**

**Symptoms:**
- "Gemini rejected the API key"
- "Gemini is temporarily overloaded"
- Copilot returns fallback deterministic answers
- "None of the Gemini models I tried are available"

**Root Causes:**
1. **Invalid/Expired API Key**
   - Key copied incorrectly (trailing spaces)
   - Key revoked from aistudio.google.com
   - Quota exhausted (free tier limit)

2. **Model Availability**
   - Model not available for the key's tier
   - Model deprecated (e.g., older gemini-1.5 models)

3. **Rate Limiting**
   - Free tier: ~10 requests/minute
   - Exceeding quota triggers exponential backoff retry

**Fixes:**

```bash
# Step 1: Validate API Key Format
python3 -c "
from src.ai import test_gemini_connection
ok, msg = test_gemini_connection()
print(f'Gemini OK: {ok}')
print(f'Message: {msg}')
"

# Step 2: Check current model chain
python3 -c "
from src.ai import _model_chain, _secret
models = _model_chain()
print(f'Model chain: {models}')
print(f'GEMINI_MODEL env: {_secret(\"GEMINI_MODEL\")}')
"

# Step 3: Manual test with detailed error
python3 << 'EOF'
from src.ai import _call_gemini
try:
    text, model = _call_gemini("Say hello")
    print(f"✓ Success with model: {model}")
    print(f"Response: {text}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}")
    print(f"Detail: {str(e)[:200]}")
EOF
```

**Rate Limiting Solution:**
The app has exponential backoff (lines 330-331 in `src/ai.py`):
```python
if kind == "provider_unavailable" and attempt < 2:
    time.sleep(1.0 * (2 ** attempt))  # 1s, 2s retry
    continue
```

For production use, upgrade to paid Gemini tier or implement request queuing.

---

## ⚡ Performance Optimization Roadmap

### **Issue 1: Slow Page Loads (Streamlit Rendering)**

**Current Bottlenecks:**
1. **Inline CSS** (600+ lines in style tag)
   - Parsed on every page render
2. **Re-rendering on every interaction**
   - Streamlit reruns entire script for each button click
3. **Large dataframes** displayed at full size

**Solutions:**

#### A. Move CSS to External File
```bash
# Create Finsight-main/.streamlit/custom.css
# Move CSS from figma_frontend.py style tag to this file
```

#### B. Optimize Dataframe Display
```python
# In figma_frontend.py, replace:
st.dataframe(shown[["invoice_id","vendor","amount",...]], width="stretch", hide_index=True)

# With:
@st.cache_data
def render_results_table(df):
    return df[["invoice_id","vendor","amount","category","status"]].head(50)

st.dataframe(render_results_table(shown), width="stretch", hide_index=True)
```

#### C. Add `@st.cache_data` to Heavy Operations
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def process_invoices_cached(df_hash):
    # Expensive operation
    return process_invoices(st.session_state.df)
```

#### D. Reduce JSON Serialization Overhead
Current: `json.dumps(_trusted_payload(results), ...)` for every Copilot question

```python
# Add to src/ai.py
@functools.lru_cache(maxsize=1)
def _trusted_payload_cached(results_hash):
    # Cache the payload
    return json.dumps(_trusted_payload(results))
```

---

### **Issue 2: Gemini Latency (AI Responses)**

**Current Round-Trip:**
1. User question → Streamlit
2. Build prompt (with full invoice data)
3. Send to Gemini API (~2-3s network latency)
4. Receive response
5. Re-render UI

**Optimization:**

```python
# Parallel processing for chart + text
import concurrent.futures

def ask_copilot_optimized(question):
    results = st.session_state.results
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start AI request immediately
        ai_future = executor.submit(ask_gemini, question, results)
        
        # Meanwhile, show UI
        st.info("🔄 Thinking...")
        
        # Wait for result
        answer, mode = ai_future.result(timeout=30)
        st.session_state.chat.append(("assistant", answer))
        st.rerun()
```

---

### **Issue 3: Database Query Performance**

**Current Problem:**
```python
client.table("audit_events")
    .select("created_at,event_type,invoice_id,message,metadata")
    .order("created_at", desc=True)
    .limit(200)  # Always fetches 200 rows
    .execute()
```

This fetches and serializes large JSONB `metadata` fields.

**Optimization:**

```python
# In src/persistence.py
def fetch_audit_events(limit=200):
    """Optimized: select only needed columns, use pagination."""
    try:
        client = _client()
        if client is None:
            return False, "SUPABASE_URL / SUPABASE_KEY are not configured."
        
        # Paginate to avoid large transfers
        page_size = min(limit, 50)
        resp = (
            client.table("audit_events")
            .select("id,created_at,event_type,invoice_id,message")  # Exclude large JSONB
            .order("created_at", desc=True)
            .limit(page_size)
            .execute()
        )
        return True, resp.data or []
    except Exception as exc:
        # ... error handling
```

---

## 🧪 Test Suite Validation

### Run All Tests
```bash
python -m pytest -v

# Expected output:
# tests/test_finsight.py::test_clean PASSED
# tests/test_finsight.py::test_missing_vendor PASSED
# tests/test_finsight.py::test_limit PASSED
# ... (all 12 tests should pass)
```

### Connection-Specific Tests
```bash
# Test without external dependencies
python -m pytest -v -k "not frontend" --tb=short

# Test only rule engine (no Gemini/Supabase needed)
python -m pytest tests/test_finsight.py -v
```

### Frontend Integration Test
```bash
python -m pytest tests/test_frontend_app.py -v --timeout=30

# This validates:
# ✓ Sample CSV loads
# ✓ Analysis runs (rule engine works)
# ✓ UI renders without errors
# ✓ Copilot quick action wired correctly
```

---

## 📊 Monitoring Connection Health

### Add Health Check Dashboard
```python
# New file: src/health.py
import time
from datetime import datetime

class HealthMonitor:
    def __init__(self):
        self.checks = {}
    
    def log_check(self, service, ok, latency_ms, error=None):
        self.checks[service] = {
            "ok": ok,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(),
            "error": error
        }
    
    def supabase_health(self):
        start = time.time()
        from src.persistence import test_supabase_connection
        ok, msg = test_supabase_connection()
        latency = (time.time() - start) * 1000
        self.log_check("Supabase", ok, latency, msg if not ok else None)
        return ok, latency
    
    def gemini_health(self):
        start = time.time()
        from src.ai import test_gemini_connection
        ok, msg = test_gemini_connection()
        latency = (time.time() - start) * 1000
        self.log_check("Gemini", ok, latency, msg if not ok else None)
        return ok, latency
```

### Display in Streamlit
```python
# In figma_frontend.py sidebar
if st.button("📊 Health Check", width="stretch"):
    from src.health import HealthMonitor
    monitor = HealthMonitor()
    
    col1, col2 = st.columns(2)
    with col1:
        supabase_ok, latency = monitor.supabase_health()
        status = "✅ OK" if supabase_ok else "❌ FAILED"
        st.metric("Supabase", status, f"{latency:.0f}ms")
    
    with col2:
        gemini_ok, latency = monitor.gemini_health()
        status = "✅ OK" if gemini_ok else "❌ FAILED"
        st.metric("Gemini", status, f"{latency:.0f}ms")
```

---

## 🚀 Quick Start: Complete Checklist

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env and add your actual keys:
# GEMINI_API_KEY=ai-xxxxx...
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_KEY=xxxxx...

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Test connections
python -m pytest tests/test_finsight.py -v

# 4. Run Streamlit
streamlit run app/figma_frontend.py

# 5. In sidebar, click "Check connections" to verify both services
```

---

## 📞 Support Matrix

| Issue | Diagnostic | Fix |
|-------|-----------|-----|
| Supabase timeout | `persistence.test_supabase_connection()` | Check env vars, verify DNS, run schema SQL |
| Gemini rate limit | Check free tier quota at aistudio.google.com | Wait 1 minute or upgrade tier |
| Slow frontend | Chrome DevTools Network tab | Apply CSS/caching optimizations above |
| Test failures | `pytest -v --tb=long` | Check data/invoices.csv exists, verify Python 3.11+ |

---

## 🔗 Related Documentation
- Supabase Schema: `supabase_schema.sql`
- Rule Engine: `src/rule_engine.py`
- AI Module: `src/ai.py`
- Persistence Layer: `src/persistence.py`
