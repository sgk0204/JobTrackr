# JobTrackr

An AI-powered job search portal that scrapes job listings from multiple sources, analyzes them using Google Gemini AI, and provides a centralized dashboard for users to track their applications, save jobs, and receive personalized career tips.

## Features
- **Centralized Search**: Search for jobs across platforms (LinkedIn, Indeed, Glassdoor) from a single interface.
- **AI Ranking Engine**: Uses Gemini AI to rank job postings based on relevance to your experience and role, assigning a 0-100 score and providing a personalized rationale.
- **Smart Query Generator**: Dynamically generates complex boolean search queries using AI to find the most relevant, hidden job posts.
- **Caching Layer**: Results are instantly fetched via Upstash Redis for rapid page loads on recurring searches.
- **Application Tracker (Kanban)**: Organize your job hunt with a drag-and-drop Kanban board (Applied, In Process, Rejected, Hired).
- **Secure Authentication**: JWT-based login and signup powered by robust PostgreSQL schemas.
- **Modern UI**: Fully responsive frontend built with React, Vite, and tailwind.

## Tech Stack
**Frontend:**
- React (Vite)
- Tailwind CSS
- React Router DOM
- @hello-pangea/dnd (Drag and Drop)
- Lucide React (Icons)

**Backend:**
- FastAPI (Python)
- PostgreSQL (via neon.tech)
- Redis (via Upstash)
- Google Gemini API (`generative-ai`)
- SerpApi (Google Jobs Scraper)

## Local Development Setup

Follow these instructions to run both the frontend and backend locally on your machine.

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- A PostgreSQL Database (Local or Neon)
- A Redis Instance (Local or Upstash)
- API Keys for Google Gemini AI and SerpApi

---

### 1. Backend Setup

The backend is built with FastAPI and runs on Python.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Mac/Linux:
   # source venv/bin/activate
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your `.env` file inside the `backend` folder and populate it with your keys:
   ```env
   DATABASE_URL="postgresql://user:password@localhost/jobtrackr"
   JWT_SECRET="generate_a_random_secret_string"
   GEMINI_API_KEY="your_google_gemini_api_key_here"
   SERPAPI_KEY="your_serpapi_key_here"
   UPSTASH_REDIS_URL="rediss://default:your_password@your-upstash-url.upstash.io:port"
   FRONTEND_URL="http://localhost:5173"
   ```

5. Run the FastAPI development server:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *(Ensure you run this command from the root project directory, not inside the `backend/` folder, based on how relative imports are structured).*

---

### 2. Frontend Setup

The frontend is a lightweight React SPA powered by Vite.

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies using npm:
   ```bash
   npm install
   ```

3. Create your `.env` file inside the `frontend` folder:
   ```env
   VITE_API_URL="http://localhost:8000/api/v1"
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```

5. The app should now be running locally at `http://localhost:5173`. Open this URL in your browser.

## Project Structure

```text
├── backend/
│   ├── auth/           # JWT & Password Hashing logic
│   ├── routes/         # API Endpoint controllers (auth, jobs)
│   ├── services/       # Core business logic (gemini, scraper, cache)
│   ├── database.py     # asyncpg connection pooling setup
│   ├── init_db.py      # Schema generation script
│   └── main.py         # FastAPI App Entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/ # Reusable UI components (Navbar, JobCard)
│   │   ├── context/    # React Context (AuthContext)
│   │   ├── pages/      # Route pages (Dashboard, Jobs, MyJobs, Login)
│   │   └── services/   # Axios interceptors & api config
│   ├── package.json
│   └── vite.config.js
└── guide.txt           # Detailed internal specifications
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
MIT
