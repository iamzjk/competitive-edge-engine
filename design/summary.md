A clean, well-structured summary will ensure the coding AI agent builds exactly what you need for your **Competitive Edge Engine**.

Here is a comprehensive summary of the project, covering the purpose, architecture, core features, and technical stack, broken down into sections suitable for an implementation brief.

## 📝 Project Summary for Coding AI Agent

### 1. Project Goal & Purpose

The goal is to build a web application for an inverter generator seller to **monitor competitor product pricing and specifications** in real-time to maintain a competitive edge.

* **Key Metric:** The core comparison metric is **"Dollar per Wattage"** ($\frac{\text{Price}}{\text{Running Wattage}}$).
* **Data Sources:** Amazon, Home Depot, Walmart, and Lowes.
* **Trigger:** Data collection is initiated manually by the user.

---

### 2. Core Technical Architecture

The application will use the robust and scalable **FastAPI + React.js** stack with **Supabase** as the database.

* **Backend (API):** **FastAPI (Python)**. Handles all server-side logic:
    * $crawl4ai$ execution.
    * AI-NLP processing.
    * Supabase data interaction.
* **Frontend (UI):** **React.js (JavaScript/TypeScript)**. Delivers a fast, interactive dashboard.
* **Database (DB):** **Supabase**. Stores all product, competitor, and historical data.

---

### 3. Core Features & Logic

The app is defined by two primary intelligence features:

#### A. The "Phantom Matchmaker" (Automated Discovery)
This feature automatically suggests competitors for a user's product, eliminating manual searching.

* **Input:** User selects a product from the **`my_products`** table.
* **Process:**
    1.  FastAPI generates search queries based on the product's **Wattage** and **Name**.
    2.  FastAPI uses $crawl4ai$ to search retailer sites and scrape promising URLs.
    3.  A Python **AI-NLP component** processes the scraped text for each URL to extract and normalize specs (**Running Wattage, Weight, Price**).
    4.  The AI calculates a **Confidence Score** based on weighted alignment:
        $$\text{Confidence Score} = (60\% \times \text{Spec Similarity}) + (40\% \times \text{Semantic Similarity})$$
    5.  Results are stored in the temporary **`match_candidates`** table.
* **UI Action:** The user reviews and **Approves** matches, moving them to the permanent **`competitor_listings`** table.

#### B. The "Specification Scrubber" (Comparison & Alerts)
This feature provides actionable visual insights based on the collected data.

* **Display:** A side-by-side comparison table showing **Your Product** vs. **Competitor Listing**.
* **Visual Alerting:** Cells are flagged instantly if the competitor has an advantage:
    * **Red Flag:** Competitor price is lower.
    * **Yellow/Orange Flag:** Competitor specification is better (e.g., lower **Dry Weight**, better **Dollar per Wattage**).

---

### 4. Database Schema (Supabase)

The agent should create these core tables with the following key fields:

| Table Name | Purpose | Key Fields | Relationship |
| :--- | :--- | :--- | :--- |
| **`my_products`** | User's product catalog. | `id` (PK), `sku`, `name`, `running_wattage`, `dry_weight`, `dimensions`, `your_price` | One-to-Many $\rightarrow$ `competitor_listings` |
| **`competitor_listings`** | Approved competitor URLs to track. | `id` (PK), `my_product_id` (FK), `url`, `retailer_name`, `last_crawled_at`, `current_price` | One-to-Many $\rightarrow$ `price_history` |
| **`match_candidates`** | Temporary staging table for AI-suggested matches awaiting approval. | `id` (PK), `my_product_id` (FK), `temp_url`, `confidence_score` | Temporary |
| **`price_history`** | Stores every historical price point for analysis. | `id` (PK), `listing_id` (FK), `price`, `recorded_at` | |

---

### 5. Essential UI/UX Elements

The React frontend must implement these screens and user flows:

1.  **Dashboard:** Top-level view with **Drift Alert Summary Cards** and a filterable table of all monitored listings, prominently featuring the **Dollar per Wattage** metric.
2.  **Product Discovery Screen:** Contains the list of your products and is the launching point for the **Phantom Matchmaker** process.
3.  **Manual Entry Forms (Modals/Flyouts):**
    * **"Add My Product":** Form to manually add a new product to the **`my_products`** table.
    * **"Manual Competitor Link":** Form to manually enter a competitor's URL and link it to a product, triggering an immediate single crawl.
