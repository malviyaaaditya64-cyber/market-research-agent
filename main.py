"""Main entry point for the autonomous market research agent system."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import ResearchAgent, AnalysisAgent, WriterAgent, CriticAgent
from memory import SharedMemory


def run_pipeline(company_name):
    """Run the full market research pipeline for a given company.

    Steps:
    1. Research the company and save findings to shared memory.
    2. Analyze the research findings and generate SWOT analysis.
    3. Write a market research report based on research and analysis.
    4. Critically review the report against research findings.
    5. If gaps are identified, print them and add a Note to the report.
    6. Save and return the final report.
    """
    print(f"\n{'='*60}")
    print(f"Market Research Pipeline for: {company_name}")
    print(f"{'='*60}\n")

    # Step 1: Research
    print("Step 1: Researching company...")
    research_agent = ResearchAgent()
    research_findings = research_agent.research(company_name)

    memory = SharedMemory()
    memory.save_finding(
        company_name=company_name,
        source=research_findings.get("source"),
        date_collected=research_findings.get("date_collected"),
        content=research_findings.get("content", ""),
    )
    print(f"  Research complete. Found: {len(research_findings.get('content', ''))} chars of content\n")

    # Step 2: Analyze
    print("Step 2: Analyzing research findings...")
    analysis_agent = AnalysisAgent()
    analysis_result = analysis_agent.analyze(company_name, memory)
    if analysis_result.get("error"):
        print(f"  Step 2 failed: {analysis_result['error']}\n")
        memory.close()
        return None
    print(f"  Analysis complete. Opportunity score: {analysis_result.get('opportunity_score', 'N/A')}\n")

    # Step 3: Write report
    print("Step 3: Writing report...")
    writer_agent = WriterAgent()
    report = writer_agent.write_report(company_name, memory.get_findings(company_name), analysis_result)
    if isinstance(report, dict) and report.get("error"):
        print(f"  Step 3 failed: {report['error']}\n")
        memory.close()
        return None
    if isinstance(report, str) and report.startswith("# Error"):
        print(f"  Step 3 failed: {report}\n")
        memory.close()
        return None
    print(f"  Report drafted ({len(report)} chars)\n")

    # Step 4: Critique
    print("Step 4: Critiquing report...")
    critic_agent = CriticAgent()
    critique = critic_agent.review(report, memory.get_findings(company_name))
    if critique.get("error"):
        print(f"  Step 4 failed: {critique['error']}\n")
        memory.close()
        return None
    print(f"  Critique complete. Gaps: {critique.get('has_gaps', False)}, Confidence: {critique.get('confidence_score', 'N/A')}\n")

# Step 5: Handle gaps
    has_gaps = critique.get("has_gaps", False)
    gap_details = critique.get("gap_details", [])

    print("Step 5: Checking for gaps...")
    if has_gaps:
        print("-" * 60)
        for i, gap in enumerate(gap_details, 1):
            print(f"  {i}. {gap}")
        print("-" * 60)
        print()
        print("IMPORTANT: The following points could not be verified against")
        print("the source research due to limited data (Wikipedia scraping).")
        print("No additional research has been invented to fill these gaps.")
        print()
        # Add Note section to the report if not already present
        if "Note" not in report:
            note_section = "\n\n## Note\n*Certain points in this report could not be verified against"
            report = report.rstrip() + note_section

    # Step 6: Save and return the final report
    print("Step 6: Saving final report...")
    filename = f"{company_name}_report.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Report saved to: {filename}\n")

    memory.close()
    return report


def main():
    """Run the market research agent system CLI."""
    if len(sys.argv) < 2:
        print("Usage: python main.py \"Company Name\"")
        sys.exit(1)

    company_name = sys.argv[1]
    run_pipeline(company_name)


if __name__ == "__main__":
    main()