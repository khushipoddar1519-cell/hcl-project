# 🏨 Hotel Analytics – Revenue Intelligence & Cancellation Prediction Suite

A complete, enterprise-grade, full-stack hotel revenue management and machine learning platform built on the **119,390 hotel reservations dataset** (City Hotel & Resort Hotel).

The project features a **decoupled REST Backend (FastAPI)**, a **Modern Luxury Web Frontend (Single Page Application)**, and an interactive **Streamlit Exploration Suite**.

---

## 🌟 Highlights & Architecture

```
hotel_analytics/
├── server.py               # FastAPI Backend & Static Asset Web Server
├── start.py                # Master CLI Launcher (Runs API, Web, or Streamlit)
├── run.sh / run.bat        # One-click startup scripts
├── backend/                # REST API Architecture
│   ├── api.py              # 21 REST API route controllers
│   ├── schemas.py          # Pydantic data validation schemas
│   ├── services.py         # Business logic, caching, and analytics engine
│   └── auth_jwt.py         # Authentication tokens and role protection
├── frontend/               # Modern Single Page Application
│   ├── index.html          # Clean HTML5 interface
│   ├── css/styles.css      # Luxury dark-slate theme & responsive styles
│   └── js/
│       ├── app.js          # SPA state management & reactive views
│       ├── api.js          # Unified REST API client
│       └── charts.js       # Zero-dependency SVG/Canvas visualization engine
├── modules/                # Core Data Science & ML Engine
│   ├── analytics.py        # KPIs, YoY comparisons, monthly trend, seasonal forecasting
│   ├── model.py            # HistGradientBoosting Classifier (86.9% Acc, 0.944 AUC)
│   ├── data_loader.py      # Cleaning, preprocessing & incremental persistence
│   ├── auth.py             # User accounts & salted password hashing
│   └── config.py           # Currency conversions, room mapping & segments
├── views/                  # Streamlit Dashboard Pages
└── app.py                  # Streamlit Multi-Page App
```

---

## 🚀 Quick Start (1-Minute Run)

### Requirements
- **Python 3.10+**

### Launch Everything
```bash
# Clone or enter the repository
cd hotel_analytics

# Run with virtual environment or standard python
./run.sh
```
*(Windows: double-click `run.bat` or run `python start.py`)*

### Launcher Options
| Command | What It Starts | URL |
|---|---|---|
| `python start.py` | FastAPI Server + Modern Web Frontend | `http://localhost:8000` |
| `python start.py --all` | Both FastAPI Web App & Streamlit App concurrently | `http://localhost:8000` & `http://localhost:8501` |
| `python start.py --streamlit` | Streamlit Multi-Page Dashboard only | `http://localhost:8501` |

> [!TIP]
> **Mobile & Tablet Access**: To open the website on your phone or tablet, make sure your device is connected to the same Wi-Fi network as your computer and browse to `http://<YOUR_COMPUTER_IP>:8000` (for example: `http://192.168.1.6:8000`). Do not type `localhost` on your phone, as `localhost` points to the phone itself.

---

## 🔐 User Authentication & Multiple Accounts

Anyone can **sign up and register a new personalized account** or sign in with any of the pre-configured accounts:

### Pre-Configured Accounts
| Role | Username / E-mail | Password | Permissions |
|---|---|---|---|
| **Revenue Analyst (User)** | `khushi` or `khushi@hotelanalytics.com` | `user123` | Analytics, Risk Calculator, Forecasting, Bookings |
| **System Administrator** | `admin` or `admin@hotelanalytics.com` | `admin123` | Full Access + ML Diagnostics, Model Retraining, User Management |
| **Hotel General Manager** | `manager` or `manager@hotelanalytics.com` | `manager123` | Analytics, Forecasts, Reports & Simulation |
| **Data Analyst** | `analyst` or `analyst@hotelanalytics.com` | `analyst123` | Analytics, Segmentation & Booking Management |

### How Any New User Can Sign In:
1. **Web App**:
   - Click the user badge (**"Sign In / Register"**) in the top right header.
   - Switch to the **"✨ Create New Account"** tab.
   - Enter your Full Name, Email, Username, Role, and Password, and click **Create Account & Sign In**.
   - You can also click any of the 4 quick demo buttons or log out using the **🚪 Logout** button.
   - Administrators can also add, inspect, or delete user accounts directly under **Admin & ML Model → User Accounts & Access Management**.
2. **Streamlit App**:
   - On the login screen, open the **"✨ Create Account"** tab.
   - Enter your name, email, desired username, and password, then click **Create Account & Sign In**.

---

## 📊 Core Features & Capabilities

### 0. 🌐 Public Landing Page & Auth Gateway
- **Enterprise Hero Presentation**: Explains the platform capabilities, model performance (119,390 bookings, 86.9% accuracy, 0.944 ROC-AUC), and core revenue benefits.
- **Embedded Interactive Auth Gateway**:
  - Switch smoothly between **"Sign In"** and **"Create Account"**.
  - 4 One-Click Demo Access buttons (*Khushi, Admin, Manager, Analyst*).
  - Anyone can register a custom account and immediately transition into the internal analytics dashboard.
  - Logging out gracefully brings users back to the landing page.
- **Feature Showcase Grid**: Highlighting Cancellation AI, Demand Forecasting, Revenue Recovery, and Booking Management.

### 1. 📈 Executive Analytics Dashboard
- **4 Real-time KPI Cards**: Total Bookings, Cancellation Rate, Net Revenue, and ADR with period-over-period comparisons.
- **Booking vs Cancellation Trend**: Interactive monthly volume comparison.
- **Revenue by Room Category**: Donut chart breakdown across Standard, Deluxe, Suite, and Family rooms.
- **Top Market Segments**: Ranked by revenue share with dynamic progress indicators.
- **Automated AI Insights**: Rule-based & seasonal alerts highlighting peak revenue windows and high-risk channels.

### 2. 🤖 AI Cancellation-Risk Calculator & Booking Studio
- **Instant ML Inference**: Computes cancellation probability in under 10 ms using a pre-trained **HistGradientBoosting Classifier** (86.9% accuracy, 0.944 ROC-AUC).
- **Interactive Radial Risk Gauge**: Visual meter with Low (<30%), Medium (30-60%), and High (>60%) risk tier badges.
- **Revenue at Risk Counter**: Computes projected loss based on ADR, nights, and probability.
- **What Drives This Score**: Feature impact waterfall breakdown (Lead time, deposit type, special requests, past cancellations, customer type).
- **Actionable Revenue Protection Tips**: Automated mitigation strategies (e.g. overbooking buffers, required prepayments, pre-arrival touchpoints).
- **Save Reservation**: 1-click persistence that saves the booking to the database and re-aggregates KPIs.

### 3. 🔍 Cancellation Deep Dive
- Lead time risk curves (0-7 days vs 180+ days).
- Deposit policy analysis (explains the non-refundable anomaly).
- Special requests retention impact (guests with special requests cancel significantly less).
- Country-level booking volume and cancellation percentage rankings.

### 4. 📉 Demand & Revenue Forecasting
- Damped linear trend decomposed with monthly seasonality indices.
- 80% confidence interval band (upper and lower bounds).
- **What-If Scenario Simulation**: Adjust market demand shocks from -30% to +30%.
- Switch between Net Bookings, Revenue, ADR, and Cancellations.

### 5. 💰 Revenue Opportunity Simulator
- Test revenue recovery targets (e.g. "What if we reduce cancellations by 20%?").
- Segment-by-segment potential revenue uplift projections.

### 6. 📑 Bookings Database
- Live search across Guest Name, Booking ID, or Country.
- Filter by Property (City vs Resort Hotel) and Status (Confirmed, Check-Out, Canceled).
- Real-time updates.

### 7. ⚙️ ML Model Diagnostics & Retraining
- Confusion matrix, ROC-AUC, accuracy, precision, and recall metrics.
- Permutation feature importance analysis.
- 1-click live retraining endpoint.

---

## 🌐 REST API Endpoints Overview

The backend provides full **OpenAPI / Swagger** documentation at `http://localhost:8000/docs`.

### Authentication
- `POST /api/auth/login` – Salted hash authentication, returns signed Bearer token.
- `GET /api/auth/me` – Returns currently logged in user profile.
- `POST /api/auth/reset-password` – Reset password using the recovery key.

### Analytics & Forecast
- `GET /api/analytics/kpis` – Current window KPIs, comparisons, and AI auto-insights.
- `GET /api/analytics/trend` – Monthly bookings, cancellations, revenue, and ADR.
- `GET /api/analytics/segments` – Market segment performance and share.
- `GET /api/analytics/rooms` – Room category revenue distribution.
- `GET /api/analytics/channels` – Distribution channel cancellation and revenue.
- `GET /api/analytics/cancellation-drivers` – Lead time, deposit, and guest behavior metrics.
- `GET /api/analytics/geography` – Top countries with booking and cancellation stats.
- `GET /api/analytics/forecast` – Trend × Seasonality forecast with confidence bounds.

### Machine Learning
- `POST /api/ml/predict` – Given reservation features, returns probability, risk tier, revenue at risk, impact drivers, and recommendations.
- `GET /api/ml/diagnostics` – Model holdout metrics, confusion matrix, and feature importances.
- `POST /api/ml/retrain` – Retrain model on completed reservations.

### Bookings & Export
- `GET /api/bookings` – Paginated and searchable reservations.
- `POST /api/bookings` – Add new booking with risk calculation.
- `PATCH /api/bookings/{id}/status` – Update booking status.
- `GET /api/reports/export` – Download CSV datasets (bookings, monthly financials, segments).

---

## 🛠️ Testing & Verification

Run tests on the analytics and ML prediction pipelines:
```bash
python -c "
from backend.services import service
from backend.schemas import BookingInput

print('KPIs:', service.get_kpis()['current']['bookings_formatted'])
pred = service.predict_risk(BookingInput(hotel='City Hotel', lead_time=60))
print('Risk:', pred.probability_pct, '%', pred.risk_level)
"
```
