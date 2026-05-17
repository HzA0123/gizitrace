# GiziTrace Backend

This is the FastAPI backend for the GiziTrace MVP. It handles data processing, AI analysis, anomaly detection, and interactions with the Supabase database.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your Supabase details.
   **Note**: Use the `SUPABASE_SERVICE_ROLE_KEY` to bypass RLS for server-side operations.

4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Access the API docs at `http://127.0.0.1:8000/docs`.
