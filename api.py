"""FastAPI endpoints for the market research agent system."""

import threading
import time
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from main import run_pipeline

app = FastAPI(title="Market Research API")

# CORS middleware allowing requests from http://localhost:5500 and http://127.0.0.1:5500
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job status tracker
jobs: dict = {}


def run_pipeline_with_tracking(job_id: str, company_name: str):
    """Run the pipeline in a background thread, tracking status updates."""
    jobs[job_id]["status"] = "researching"
    jobs[job_id]["updated_at"] = time.time()

    # Manually step through the pipeline to track status
    from agents import ResearchAgent, AnalysisAgent, WriterAgent, CriticAgent
    from memory import SharedMemory

    # Step 1: Research
    jobs[job_id]["status"] = "researching"
    research_agent = ResearchAgent()
    research_findings = research_agent.research(company_name)
    memory = SharedMemory()
    memory.save_finding(
        company_name=company_name,
        source=research_findings.get("source"),
        date_collected=research_findings.get("date_collected"),
        content=research_findings.get("content", ""),
    )
    jobs[job_id]["status"] = "analyzing"
    jobs[job_id]["updated_at"] = time.time()

    # Step 2: Analyze
    analysis_agent = AnalysisAgent()
    analysis_result = analysis_agent.analyze(company_name, memory)
    if analysis_result.get("error"):
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = analysis_result["error"]
        jobs[job_id]["updated_at"] = time.time()
        memory.close()
        return
    jobs[job_id]["opportunity_score"] = analysis_result.get("opportunity_score")
    jobs[job_id]["swot"] = analysis_result.get("swot", {
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": [],
    })
    jobs[job_id]["status"] = "writing"
    jobs[job_id]["updated_at"] = time.time()

    # Step 3: Write report
    writer_agent = WriterAgent()
    report = writer_agent.write_report(company_name, memory.get_findings(company_name), analysis_result)
    if isinstance(report, dict) and report.get("error"):
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = report["error"]
        jobs[job_id]["updated_at"] = time.time()
        memory.close()
        return
    if isinstance(report, str) and report.startswith("# Error"):
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = report
        jobs[job_id]["updated_at"] = time.time()
        memory.close()
        return
    jobs[job_id]["report"] = report
    jobs[job_id]["status"] = "critiquing"
    jobs[job_id]["updated_at"] = time.time()

    # Step 4: Critique
    critic_agent = CriticAgent()
    critique = critic_agent.review(report, memory.get_findings(company_name))
    if critique.get("error"):
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = critique["error"]
        jobs[job_id]["updated_at"] = time.time()
        memory.close()
        return
    has_gaps = critique.get("has_gaps", False)
    gap_details = critique.get("gap_details", [])

    jobs[job_id]["gap_details"] = gap_details
    jobs[job_id]["status"] = "done"
    jobs[job_id]["updated_at"] = time.time()

    # Step 5: Handle gaps (already handled in critique), just close memory
    memory.close()


@app.post("/research")
def start_research(company_name_data: dict):
    """Start a market research pipeline for the given company."""
    company_name = company_name_data.get("company_name", "")
    if not company_name:
        raise HTTPException(status_code=400, detail="company_name is required")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "company_name": company_name,
        "status": "queued",
        "error": None,
        "report": None,
        "opportunity_score": None,
        "swot": {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        },
        "gap_details": [],
        "updated_at": time.time(),
    }

    thread = threading.Thread(target=run_pipeline_with_tracking, args=(job_id, company_name), daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    """Get the current status of a research job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return {
        "job_id": job_id,
        "step": job["status"],
        "error": job.get("error"),
    }


@app.get("/report/{job_id}")
def get_report(job_id: str):
    """Get the final report data for a completed research job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job is not done yet. Current step: {job['status']}")

    return {
        "job_id": job_id,
        "report": job.get("report"),
        "opportunity_score": job.get("opportunity_score"),
        "swot": job.get("swot"),
        "gap_details": job.get("gap_details"),
    }