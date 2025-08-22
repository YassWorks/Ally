############# deprecated tools #############

from langchain_core.tools import tool
import textwrap


@tool
def extract_main_idea() -> str:
    """
    Guides the agent in identifying the core conceptual idea of the project.
    """
    prompt = """
    Analyze the user's project description and extract the MAIN IDEA.

    OBJECTIVE:
    Identify the essential purpose or value proposition of the project in conceptual terms.

    GUIDELINES:
    - Focus on WHAT the project aims to accomplish, not HOW it is implemented
    - Ignore technical details, specific features, or tools
    - Emphasize the underlying problem being solved or the benefit provided
    - Avoid buzzwords or marketing speak — be precise and conceptual

    EXAMPLES:
    - "A platform that connects [users] with [service/product] to solve [problem]"
    - "An app that helps [target audience] achieve [specific goal]"
    - "A tool to automate [task] for [industry/role]"

    OUTPUT:
    Write a single sentence (max 2) summarizing the main idea clearly and concisely.
    """
    return textwrap.dedent(prompt).strip()


@tool
def extract_tech_details() -> str:
    """
    Guides the agent in identifying all technical aspects of the project.
    """
    prompt = """
    Extract all technical specifications from the project description.

    OBJECTIVE:
    Parse and organize all implementation-related information.

    INSTRUCTIONS:
    - Identify technologies, programming languages, platforms, tools, and frameworks
    - Include architectural choices, deployment environments, and performance constraints
    - If a category is not mentioned, explicitly write "Not specified"

    FORMAT:
    - Target Platforms: [...]
    - Programming Languages: [...]
    - Frameworks: [...]
    - Libraries/Dependencies: [...]
    - Tech Stack Components: [...]
    - Architecture/Patterns: [...]
    - Technical Requirements: [...]
    - Development Tools: [...]
    - Other Technical Details: [...]
    """
    return textwrap.dedent(prompt).strip()


@tool
def get_features_ideas() -> str:
    """
    Guides the agent in brainstorming features and functional ideas.
    """
    prompt = """
    Generate detailed features and creative ideas for the project based on its concept.

    OBJECTIVE:
    Produce a structured list of relevant features, grouped by function and value, while remaining feasible given the implied tech.

    INSTRUCTIONS:
    - Brainstorm core, advanced, UX, and technical features
    - Include integration ideas, user roles, and scalability options
    - Consider technical feasibility based on any constraints provided
    - Align your ideas with the main concept or problem being solved

    IF CONTEXT IS LIMITED:
    - Infer reasonable assumptions based on typical use cases in the domain
    - Be creative but not speculative

    FORMAT:
    CORE FEATURES:
    - Feature 1: [Description]
    - ...

    ADVANCED FEATURES:
    - Feature A: [Description]
    - ...

    USER EXPERIENCE (UX):
    - Feature X: [Description]
    - ...

    INTEGRATIONS:
    - Integration with [service/tool]: [Why it helps]

    INNOVATIVE IDEAS:
    - Idea 1: [Description]

    TECHNICAL CONSIDERATIONS:
    - Consideration 1: [e.g. offline support, responsive design]
    """
    return textwrap.dedent(prompt).strip()


@tool
def analyze_target_audience() -> str:
    """
    Guides the agent in identifying the intended user base for the project.
    """
    prompt = """
    Analyze the project context to infer or identify the target audience.

    TASK:
    Describe the primary users the project is intended for, along with their needs, behaviors, and goals.

    INSTRUCTIONS:
    - Identify demographic, professional, or behavioral traits
    - Consider user goals, pain points, and desired outcomes
    - Be specific (e.g., "freelance designers managing client assets", not just "designers")

    OUTPUT:
    A concise 1–2 paragraph profile of the most relevant target audience(s).
    """
    return textwrap.dedent(prompt).strip()


@tool
def find_potential_pitfalls() -> str:
    """
    Guides the agent in critically evaluating the idea for missing elements or risks.
    """
    prompt = """
    Critically evaluate the project idea for gaps, risks, or flawed assumptions.

    TASK:
    Identify what might go wrong or what’s missing from the current idea.

    CONSIDER:
    - Overlooked user needs
    - Missing components or integrations
    - Scalability or security concerns
    - Assumptions that may not hold
    - Competition or market saturation

    OUTPUT:
    A list of 3–5 potential pitfalls with a short explanation for each.
    """
    return textwrap.dedent(prompt).strip()


@tool
def tools_help() -> str:
    """
    Lists all available brainstorm commands and what each one does.
    """
    return textwrap.dedent(
        """
    Available Brainstorm Commands:

    /extract_main_idea — Identify the core conceptual purpose of the project
    /extract_tech_details — Pull out implementation-level technical details
    /get_features_ideas — Generate categorized features and UX ideas
    /analyze_target_audience — Describe the intended user(s) and their goals
    /find_potential_pitfalls — List flaws, risks, or missing elements in the concept
    /suggest_next_brainstorm_command — Decide the next most useful command
    /help — Display all available brainstorm commands
    """
    ).strip()
