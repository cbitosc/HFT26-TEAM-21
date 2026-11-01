"""
Portfolio extraction service for SkillProof AI (Module 3).
Parses JSON and PDF portfolio submissions into a standardized PortfolioStructure.
Treats all uploaded content as untrusted data.
"""

from __future__ import annotations

import io
import json
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
import httpx
import pypdf

from app.models import PortfolioStructure, ProjectItem, SkillsStructure

logger = logging.getLogger("skillproof.portfolio.extractor")

# Maximum allowed file size: 5 MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

# Dictionaries of known technical terms for deterministic PDF parsing
KNOWN_LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C", "Go", "Golang",
    "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Dart", "SQL", "R", "Scala", "Shell", "Bash"
]

KNOWN_TOOLS = [
    "React", "Next.js", "Vue.js", "Angular", "Node.js", "Express.js", "FastAPI",
    "Django", "Flask", "Spring Boot", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
    "Git", "GitHub", "PostgreSQL", "MySQL", "MongoDB", "Redis", "GraphQL", "REST API",
    "Tailwind CSS", "Bootstrap", "Linux", "Nginx", "Terraform", "Kafka"
]

KNOWN_DOMAINS = [
    "Web Development", "Backend Development", "Frontend Development", "Full Stack Development",
    "Cloud Computing", "Machine Learning", "Data Science", "Artificial Intelligence",
    "Cybersecurity", "Mobile Development", "DevOps", "Database Management", "Distributed Systems"
]

KNOWN_DSA_TOPICS = [
    "Arrays", "Strings", "Linked Lists", "Stacks", "Queues", "Hash Tables",
    "Trees", "Binary Search Trees", "Binary Search", "Graphs", "Dynamic Programming",
    "Recursion", "Backtracking", "Sorting", "Two Pointers", "Sliding Window",
    "Greedy Algorithms", "Bit Manipulation", "Heap / Priority Queue", "Trie"
]


def validate_file(filename: str, content: bytes) -> str:
    """
    Validates file extension, magic bytes, and file size.
    Returns detected file type: 'pdf' or 'json'.
    Raises HTTPException 400/413 on invalid input.
    """
    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of 5 MB ({len(content)} bytes).",
        )

    clean_name = filename.strip().lower()
    
    # Check PDF
    if clean_name.endswith(".pdf"):
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file. Header magic bytes %PDF missing or corrupted.",
            )
        return "pdf"

    # Check JSON
    if clean_name.endswith(".json"):
        stripped = content.strip()
        if not (stripped.startswith(b"{") or stripped.startswith(b"[")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON file. Content must start with a valid JSON object or array.",
            )
        return "json"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported file format. Only PDF (.pdf) and JSON (.json) files are permitted.",
    )


def _dedup_list(items: List[str]) -> List[str]:
    """Deduplicates a list while preserving original order and trimming blanks."""
    seen = set()
    result = []
    for item in items:
        if isinstance(item, str):
            clean = item.strip()
            if clean and clean.lower() not in seen:
                seen.add(clean.lower())
                result.append(clean)
    return result


def extract_portfolio_from_json(content: bytes) -> PortfolioStructure:
    """
    Parses untrusted JSON portfolio payload into standardized PortfolioStructure.
    Handles schema variations and normalizes missing fields without inventing data.
    """
    try:
        raw_text = content.decode("utf-8", errors="replace")
        data = json.loads(raw_text)
    except Exception as exc:
        logger.warning("JSON decode failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed JSON file: {str(exc)}",
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON root must be a JSON object (key-value dictionary).",
        )

    # 1. Projects normalization
    raw_projects = data.get("projects") or data.get("portfolio") or data.get("experience") or []
    projects: List[ProjectItem] = []
    if isinstance(raw_projects, list):
        for p in raw_projects:
            if isinstance(p, dict):
                p_name = str(p.get("name") or p.get("title") or "").strip()
                p_desc = str(p.get("description") or p.get("summary") or p.get("overview") or "").strip()
                p_tech_raw = p.get("technologies") or p.get("tech_stack") or p.get("tools") or []
                p_tech: List[str] = []
                if isinstance(p_tech_raw, list):
                    p_tech = _dedup_list([str(t) for t in p_tech_raw])
                elif isinstance(p_tech_raw, str):
                    p_tech = _dedup_list(re.split(r"[,;|]", p_tech_raw))

                if p_name or p_desc or p_tech:
                    projects.append(ProjectItem(
                        name=p_name,
                        description=p_desc,
                        technologies=p_tech,
                    ))

    # 2. Skills normalization
    raw_skills = data.get("skills") or {}
    prog_langs: List[str] = []
    frameworks: List[str] = []

    if isinstance(raw_skills, dict):
        raw_langs = raw_skills.get("programming_languages") or raw_skills.get("languages") or []
        if isinstance(raw_langs, list):
            prog_langs.extend([str(l) for l in raw_langs])
        elif isinstance(raw_langs, str):
            prog_langs.extend(re.split(r"[,;|]", raw_langs))

        raw_tools = raw_skills.get("frameworks_and_tools") or raw_skills.get("frameworks") or raw_skills.get("tools") or []
        if isinstance(raw_tools, list):
            frameworks.extend([str(t) for t in raw_tools])
        elif isinstance(raw_tools, str):
            frameworks.extend(re.split(r"[,;|]", raw_tools))

    elif isinstance(raw_skills, list):
        for s in raw_skills:
            if isinstance(s, str):
                s_clean = s.strip()
                # Categorize into languages vs tools if matched against known vocabulary
                if any(s_clean.lower() == kl.lower() for kl in KNOWN_LANGUAGES):
                    prog_langs.append(s_clean)
                else:
                    frameworks.append(s_clean)

    # 3. Domains normalization
    raw_domains = data.get("domains") or data.get("technical_domains") or data.get("domain") or []
    domains: List[str] = []
    if isinstance(raw_domains, list):
        domains = [str(d) for d in raw_domains]
    elif isinstance(raw_domains, str):
        domains = re.split(r"[,;|]", raw_domains)

    # 4. DSA Topics normalization
    raw_dsa = data.get("dsa_topics") or data.get("dsa") or data.get("algorithms") or []
    dsa_topics: List[str] = []
    if isinstance(raw_dsa, list):
        dsa_topics = [str(d) for d in raw_dsa]
    elif isinstance(raw_dsa, str):
        dsa_topics = re.split(r"[,;|]", raw_dsa)

    return PortfolioStructure(
        projects=projects,
        skills=SkillsStructure(
            programming_languages=_dedup_list(prog_langs),
            frameworks_and_tools=_dedup_list(frameworks),
        ),
        domains=_dedup_list(domains),
        dsa_topics=_dedup_list(dsa_topics),
    )


def extract_portfolio_from_pdf(content: bytes) -> PortfolioStructure:
    """
    Extracts text from a PDF document using pypdf and applies deterministic
    keyword extraction to extract projects, skills, domains, and DSA topics.
    Rejects corrupted or empty PDFs.
    """
    try:
        stream = io.BytesIO(content)
        reader = pypdf.PdfReader(stream)
    except Exception as exc:
        logger.warning("pypdf initialization failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to read PDF file. File may be corrupted or encrypted: {str(exc)}",
        )

    if len(reader.pages) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF document contains zero pages.",
        )

    extracted_pages: List[str] = []
    for idx, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_pages.append(page_text)
        except Exception as exc:
            logger.warning("Error reading PDF page %d: %s", idx, exc)

    full_text = "\n".join(extracted_pages).strip()
    if not full_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF file contains no extractable text content (e.g. image-only or scanned document).",
        )

    # Deterministic vocabulary scanning
    detected_languages: List[str] = []
    for lang in KNOWN_LANGUAGES:
        # Match word boundaries case-insensitively
        pattern = rf"(?<!\w){re.escape(lang)}(?!\w)"
        if re.search(pattern, full_text, flags=re.IGNORECASE):
            detected_languages.append(lang)

    detected_tools: List[str] = []
    for tool in KNOWN_TOOLS:
        pattern = rf"(?<!\w){re.escape(tool)}(?!\w)"
        if re.search(pattern, full_text, flags=re.IGNORECASE):
            detected_tools.append(tool)

    detected_domains: List[str] = []
    for domain in KNOWN_DOMAINS:
        pattern = rf"(?<!\w){re.escape(domain)}(?!\w)"
        if re.search(pattern, full_text, flags=re.IGNORECASE):
            detected_domains.append(domain)

    detected_dsa: List[str] = []
    for dsa in KNOWN_DSA_TOPICS:
        pattern = rf"(?<!\w){re.escape(dsa)}(?!\w)"
        if re.search(pattern, full_text, flags=re.IGNORECASE):
            detected_dsa.append(dsa)

    # Heuristic project parsing from text
    # Look for sections like "PROJECTS" or "PERSONAL PROJECTS"
    projects: List[ProjectItem] = []
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    
    in_projects_section = False
    current_proj_name = ""
    current_proj_desc = []
    current_proj_tech = []

    for line in lines:
        upper_line = line.upper()
        if any(heading in upper_line for heading in ["PROJECTS", "PERSONAL PROJECTS", "ACADEMIC PROJECTS", "FEATURED PROJECTS"]):
            in_projects_section = True
            continue
        elif in_projects_section and any(heading in upper_line for heading in ["EDUCATION", "EXPERIENCE", "CERTIFICATIONS", "AWARDS", "PUBLICATIONS"]):
            in_projects_section = False
            # Save the last project if any
            if current_proj_name:
                projects.append(ProjectItem(
                    name=current_proj_name,
                    description=" ".join(current_proj_desc[:4]).strip(),
                    technologies=_dedup_list(current_proj_tech),
                ))
                current_proj_name = ""
                current_proj_desc = []
                current_proj_tech = []
            break

        if in_projects_section:
            # Check if this line looks like a project title (short line, not a bullet)
            if len(line) < 60 and not line.startswith(("-", "•", "*")) and (":" not in line or line.startswith("Project")):
                if current_proj_name:
                    projects.append(ProjectItem(
                        name=current_proj_name,
                        description=" ".join(current_proj_desc[:4]).strip(),
                        technologies=_dedup_list(current_proj_tech),
                    ))
                    current_proj_desc = []
                    current_proj_tech = []
                current_proj_name = re.sub(r"^(Project\s*\d*[:\-]?\s*)", "", line, flags=re.IGNORECASE).strip()
            else:
                current_proj_desc.append(line)
                # Check for tech mentioned in this line
                for tech in detected_languages + detected_tools:
                    if re.search(rf"(?<!\w){re.escape(tech)}(?!\w)", line, flags=re.IGNORECASE):
                        current_proj_tech.append(tech)

    # Append trailing project if detected
    if in_projects_section and current_proj_name:
        projects.append(ProjectItem(
            name=current_proj_name,
            description=" ".join(current_proj_desc[:4]).strip(),
            technologies=_dedup_list(current_proj_tech),
        ))

    # If no project headers were found, leave projects list empty rather than inventing false data
    return PortfolioStructure(
        projects=projects,
        skills=SkillsStructure(
            programming_languages=_dedup_list(detected_languages),
            frameworks_and_tools=_dedup_list(detected_tools),
        ),
        domains=_dedup_list(detected_domains),
        dsa_topics=_dedup_list(detected_dsa),
    )


# ---------------------------------------------------------------------------
# Featherless AI Portfolio Semantic Interpretation (Privacy-Shielded)
# ---------------------------------------------------------------------------

class PortfolioAIInterpretation(BaseModel):
    """Structured Pydantic schema for Featherless portfolio analysis."""
    inferred_technologies: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    dsa_topics: List[str] = Field(default_factory=list)
    project_insights: Optional[List[Dict[str, Any]]] = None


def _strip_pii_for_ai(text: str) -> str:
    """
    Removes personal identifying information (emails, phone numbers, personal urls, physical addresses)
    before dispatching to external AI providers.
    """
    if not text:
        return ""
    # Strip email addresses
    clean = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL_REDACTED]", text)
    # Strip phone numbers (various formats)
    clean = re.sub(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "[PHONE_REDACTED]", clean)
    # Strip personal URLs (linkedin.com/in/..., github.com/<user>)
    clean = re.sub(r"https?://(www\.)?(linkedin\.com/in|github\.com)/[a-zA-Z0-9_-]+/?", "[PROFILE_LINK_REDACTED]", clean)
    return clean


async def interpret_portfolio_with_featherless(
    base_portfolio: PortfolioStructure,
) -> PortfolioStructure:
    """
    Enhances extracted portfolio data using Featherless AI semantic interpretation:
      - Extracts technologies, technical domains, and algorithmic concepts from project context.
      - Strictly protects privacy by redacting candidate PII before external dispatch.
      - Validates output with Pydantic against PortfolioAIInterpretation schema.
      - Never marks skills as verified (skills_status remains unverified).
      - Gracefully falls back to deterministic extraction on any failure or missing credentials.
    """
    from app.config import get_settings

    settings = get_settings()

    if not settings.is_featherless_configured:
        return base_portfolio

    # Prepare sanitized project context (ONLY project names, descriptions, and detected tech)
    sanitized_projects = []
    for p in base_portfolio.projects:
        sanitized_projects.append({
            "name": _strip_pii_for_ai(p.name),
            "description": _strip_pii_for_ai(p.description),
            "technologies": p.technologies,
        })

    if not sanitized_projects and not base_portfolio.skills.programming_languages:
        return base_portfolio

    system_prompt = (
        "You are a technical portfolio analyzer for software engineering candidates. "
        "Analyze the candidate's project descriptions to identify technical domains, "
        "technologies, and algorithmic/DSA concepts demonstrated by their work.\n"
        "Strict Rules:\n"
        "1. Return ONLY a valid JSON object matching this schema:\n"
        '   {"inferred_technologies": ["string"], "domains": ["string"], "dsa_topics": ["string"]}\n'
        "2. 'domains' should be standard engineering domains (e.g. 'Web Development', 'Backend Development', 'Algorithms & DSA', 'Cloud Computing', 'Machine Learning', 'Distributed Systems', 'Mobile Development').\n"
        "3. 'dsa_topics' should be standard data structures & algorithms (e.g. 'Arrays', 'Hash Tables', 'Two Pointers', 'Trees', 'Graphs', 'Dynamic Programming', 'Sorting', 'Stacks', 'Queues').\n"
        "4. Do NOT hallucinate skills or invent experience not supported by the text.\n"
        "5. Do NOT include any markdown code fencing (```json), explanation, or commentary. Output raw JSON only."
    )

    user_prompt = (
        "Analyze these projects and technical skills:\n"
        + json.dumps({
            "projects": sanitized_projects[:5],  # Bounded to top 5 projects
            "languages": base_portfolio.skills.programming_languages,
            "tools": base_portfolio.skills.frameworks_and_tools,
        }, indent=2)
    )

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(
                f"{settings.featherless_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.featherless_api_key.strip()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.featherless_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.2,
                },
            )
            if response.status_code != 200:
                logger.warning("Featherless portfolio analysis returned HTTP %d", response.status_code)
                return base_portfolio

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            # Clean potential markdown fences
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)
            validated = PortfolioAIInterpretation(**parsed)

            # Merge validated inferred items with base portfolio
            # 1. Inferred tech into languages or tools
            merged_langs = list(base_portfolio.skills.programming_languages)
            merged_tools = list(base_portfolio.skills.frameworks_and_tools)
            for tech in validated.inferred_technologies:
                if isinstance(tech, str):
                    clean_tech = tech.strip()
                    if any(clean_tech.lower() == kl.lower() for kl in KNOWN_LANGUAGES):
                        merged_langs.append(clean_tech)
                    else:
                        merged_tools.append(clean_tech)

            # 2. Inferred domains (prefer known taxonomy)
            merged_domains = list(base_portfolio.domains)
            for dom in validated.domains:
                if isinstance(dom, str):
                    matched_domain = next(
                        (kd for kd in KNOWN_DOMAINS if kd.lower() == dom.strip().lower()),
                        dom.strip()
                    )
                    merged_domains.append(matched_domain)

            # 3. Inferred DSA topics (prefer known taxonomy)
            merged_dsa = list(base_portfolio.dsa_topics)
            for dsa in validated.dsa_topics:
                if isinstance(dsa, str):
                    matched_dsa = next(
                        (kd for kd in KNOWN_DSA_TOPICS if kd.lower() == dsa.strip().lower()),
                        dsa.strip()
                    )
                    merged_dsa.append(matched_dsa)

            return PortfolioStructure(
                projects=base_portfolio.projects,
                skills=SkillsStructure(
                    programming_languages=_dedup_list(merged_langs),
                    frameworks_and_tools=_dedup_list(merged_tools),
                ),
                domains=_dedup_list(merged_domains),
                dsa_topics=_dedup_list(merged_dsa),
            )

    except Exception as exc:
        logger.info(
            "Featherless portfolio intelligence fallback activated (%s): %s",
            type(exc).__name__,
            exc,
        )
        return base_portfolio

