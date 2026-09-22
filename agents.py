"""Agent modules for the autonomous market research system."""

import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai


class AnalysisAgent:
    """Agent responsible for analyzing research findings and generating SWOT analysis.

    Takes collected research data and produces structured strategic analysis
    including SWOT (Strengths, Weaknesses, Opportunities, Threats) and an
    opportunity score from 1-10 based on the available evidence.
    """

    def analyze(self, company_name, memory):
        """Generate SWOT analysis and opportunity score for a company.

        Retrieves stored research findings from memory and uses an LLM to
        generate a structured SWOT analysis and numeric opportunity score.

        Args:
            company_name: Name of the company to analyze.
            memory: SharedMemory instance containing research findings.

        Returns:
            A dictionary with keys:
            - swot: dict with keys 'strengths', 'weaknesses', 'opportunities', 'threats' (each a list of strings)
            - opportunity_score: integer from 1-10
            - reasoning: string explaining the analysis
            Returns an error dictionary if no findings are available.
        """
        findings = memory.get_findings(company_name)

        if not findings:
            return {
                "error": f"No research findings found for company: {company_name}",
                "source": None,
                "date_collected": datetime.utcnow().isoformat() + "Z",
                "content": "",
            }

        # Collect research content
        content_text = " ".join(f.get("content", "") for f in findings if f.get("content"))

        # Configure Gemini API with API key from environment
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("API_KEY", "")
        if not api_key:
            return {
                "error": "No API key configured. Set GEMINI_API_KEY or API_KEY environment variable.",
                "source": None,
                "date_collected": datetime.utcnow().isoformat() + "Z",
                "content": "",
            }

        genai.configure(api_key=api_key)

        # Build prompt for LLM
        prompt = f"""You are performing a strategic analysis of a company based on collected research findings.

Company: {company_name}

Research findings:
{content_text}

Please provide a SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) as a list of key points, and a numeric opportunity_score from 1-10 with reasoning. 

Format your response as JSON with this exact structure:
{{
  "swot": {{
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."],
    "opportunities": ["...", "..."],
    "threats": ["...", "..."]
  }},
  "opportunity_score": <integer 1-10>,
  "reasoning": "string explaining the analysis"
}}
"""

        try:
            model = genai.GenerativeModel("gemini-3.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                ),
            )

            content = response.text.strip()

            # Try to find JSON in the response
            start_idx = content.index("{")
            end_idx = content.rindex("}") + 1
            json_str = content[start_idx:end_idx]
            result = json.loads(json_str)

            # Ensure score is clamped to 1-10
            score = result.get("opportunity_score", 5)
            result["opportunity_score"] = max(1, min(10, score))

            return result

        except Exception as e:
            return {
                "error": f"LLM analysis failed: {str(e)}",
                "source": None,
                "date_collected": datetime.utcnow().isoformat() + "Z",
                "content": "",
            }


class ResearchAgent:
    """Agent responsible for conducting market research.

    Performs basic web scraping to collect raw public information
    about companies or products from open web sources.
    """

    def research(self, company_name):
        """Search and scrape basic public information about a company.

        Fetches a simple web source (Wikipedia) and extracts general
        description and metadata. No analysis, scoring, or opinions
        are included — only raw collected data.

        Args:
            company_name: Name of the company or product to research.

        Returns:
            A dictionary with keys: source, date_collected, content.
            Returns an error dictionary if the request fails.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; MarketResearchAgent/1.0)"
        }

        try:
            search_url = f"https://en.wikipedia.org/w/index.php?search={company_name.replace(' ', '+')}&title=Special:Search"
            response = requests.get(search_url, timeout=10, headers=headers)
            response.raise_for_status()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Try to find the first result link
            first_link = soup.find("a", class_="mw-search-result-title")
            if first_link:
                article_url = first_link["href"]
                if not article_url.startswith("http"):
                    article_url = f"https://en.wikipedia.org{article_url}"
            else:
                # Fall back to the direct Wikipedia article URL for well-known subjects
                article_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"

            # Fetch the actual article page
            article_response = requests.get(article_url, timeout=10, headers=headers)
            article_response.raise_for_status()

            article_soup = BeautifulSoup(article_response.text, "html.parser")

            # Extract the first non-empty paragraph as general description
            content_div = article_soup.find("div", id="mw-content-text")
            if content_div:
                paragraphs = content_div.find_all("p")
                content = ""
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and "mw-empty-elt" not in p.get("class", []):
                        content = text
                        break
            else:
                content = ""

            result = {
                "source": article_url,
                "date_collected": datetime.utcnow().isoformat() + "Z",
                "content": content,
            }
            return result

        except requests.RequestException as e:
            return {
                "source": None,
                "date_collected": datetime.utcnow().isoformat() + "Z",
                "content": "",
                "error": str(e),
            }


class TrendAnalyzer:
    """Agent for analyzing market trends.

    Will perform tasks such as:
    - Processing time-series market data
    - Identifying upward/downward trends
    - Seasonal pattern detection
    - Trend forecasting
    """


class CompetitorAnalyzer:
    """Agent for competitor analysis.

    Will perform tasks such as:
    - Scraping competitor websites
    - Comparing pricing and features
    - Monitoring product launches
    - Analyzing market positioning
    """


class WriterAgent:
    """Agent responsible for generating formatted market research reports.

    Uses an LLM to synthesize research findings and SWOT analysis into
    a well-structured Markdown report with sections: Executive Summary,
    Company Overview, SWOT Analysis, Opportunity Assessment, and Recommendations.
    """

    def write_report(self, company_name, research_findings, analysis_result):
        """Generate a Markdown report for a company based on research and analysis.

        Args:
            company_name: Name of the company to generate a report for.
            research_findings: List of dicts from memory containing raw research data.
            analysis_result: Dict with keys 'swot', 'opportunity_score', 'reasoning'
                from the AnalysisAgent.

        Returns:
            The generated report text as a string.
        """
        # Configure Gemini API with API key from environment
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("API_KEY", "")
        if not api_key:
            return "# Error\nNo API key configured. Set GEMINI_API_KEY or API_KEY environment variable."

        genai.configure(api_key=api_key)

        # Extract SWOT and analysis data
        swot = analysis_result.get("swot", {})
        opportunity_score = analysis_result.get("opportunity_score", 5)
        reasoning = analysis_result.get("reasoning", "")

        # Collect research content
        content_text = " ".join(f.get("content", "") for f in research_findings if f.get("content"))

        # Build prompt for LLM
        prompt = f"""You are generating a professional market research report in Markdown format.

Company: {company_name}

Research findings:
{content_text}

SWOT Analysis:
- Strengths: {swot.get('strengths', [])}
- Weaknesses: {swot.get('weaknesses', [])}
- Opportunities: {swot.get('opportunities', [])}
- Threats: {swot.get('threats', [])}

Opportunity Score: {opportunity_score}/10
Reasoning: {reasoning}

Please generate a well-structured Markdown report with the following sections:

1. **Executive Summary**: A concise overview of the company and key findings
2. **Company Overview**: Detailed description of the company based on the research
3. **SWOT Analysis**: Structured analysis using the provided SWOT data
4. **Opportunity Assessment**: Evaluation of the opportunity score with explanation
5. **Recommendations**: Strategic recommendations based on the analysis

Format the output as Markdown. Return ONLY the Markdown text, no additional commentary.
"""

        try:
            model = genai.GenerativeModel("gemini-3.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                ),
            )

            report = response.text.strip()

            # Save report to file
            filename = f"{company_name}_report.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)

            return report

        except Exception as e:
            return f"# Report Generation Error\nFailed to generate report: {str(e)}"


class CriticAgent:
    """Agent responsible for critically reviewing market research reports.

    Evaluates generated reports against research findings to identify gaps,
    missing business aspects, and assesses overall confidence in the report's quality.
    """

    def review(self, report_text, research_findings):
        """Critically review a market research report against research findings.

        Checks for claims in the report that aren't supported by the research,
        important business aspects that seem missing or shallow, and overall
        confidence in the report's quality.

        Args:
            report_text: The generated report text to review.
            research_findings: List of dicts from memory containing raw research data.

        Returns:
            A dictionary with keys:
            - has_gaps: boolean (False if gap_details is empty)
            - gap_details: list of specific missing points as strings
            - confidence_score: integer from 1-10
        """
        # Configure Gemini API with API key from environment
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("API_KEY", "")
        if not api_key:
            return {
                "error": "No API key configured. Set GEMINI_API_KEY or API_KEY environment variable.",
                "has_gaps": False,
                "gap_details": [],
                "confidence_score": 1,
            }

        genai.configure(api_key=api_key)

        # Collect research content
        content_text = " ".join(f.get("content", "") for f in research_findings if f.get("content"))

        # Build prompt for LLM
        prompt = f"""You are critically reviewing a market research report against the original research findings.

Report text:
{report_text}

Research findings:
{content_text}

Please critique the report by checking for:
(a) Any claims in the report that aren't supported by the research findings
(b) Important business aspects that seem missing or shallow
(c) Overall confidence in the report's quality (1-10 scale)

Return your response as JSON with this exact structure:
{{
  "has_gaps": true or false,
  "gap_details": ["specific missing point 1", "specific missing point 2", ...],
  "confidence_score": <integer 1-10>
}}
Note: has_gaps should be false if gap_details is empty.
"""

        try:
            model = genai.GenerativeModel("gemini-3.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                ),
            )

            content = response.text.strip()

            # Try to find JSON in the response
            start_idx = content.index("{")
            end_idx = content.rindex("}") + 1
            json_str = content[start_idx:end_idx]
            result = json.loads(json_str)

            # Ensure has_gaps is boolean and consistent with gap_details
            # If gap_details is empty and has_gaps is True, that's contradictory — trust gap_details
            # If gap_details has items and has_gaps is False, that's contradictory — trust gap_details
            # Otherwise preserve the LLM's original has_gaps value (especially important for low confidence)
            if result.get("gap_details") and not result.get("has_gaps"):
                result["has_gaps"] = True
            elif not result.get("gap_details") and result.get("has_gaps") is True:
                # Only override has_gaps to False if confidence is also high (not 1)
                # When confidence is 1 (very low), preserve the LLM's has_gaps=True
                score = result.get("confidence_score", 5)
                if 5 <= score <= 10:
                    result["has_gaps"] = False

            # Ensure confidence_score is clamped to 1-10
            score = result.get("confidence_score", 5)
            result["confidence_score"] = max(1, min(10, score))

            return result

        except Exception as e:
            return {
                "error": f"LLM review failed: {str(e)}",
                "has_gaps": False,
                "gap_details": [],
                "confidence_score": 1,
            }


class SentimentAnalyzer:
    """Agent for sentiment analysis.

    Will perform tasks such as:
    - Analyzing customer reviews and feedback
    - Tracking social media sentiment
    - Identifying positive/negative trends
    - Generating sentiment reports
    """