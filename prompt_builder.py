def build_prompt(user_message):

    msg = user_message.lower()

    # ==========================
    # SHORT NOTES
    # ==========================
    if "short notes" in msg:

        topic = user_message.lower().replace("short notes", "").replace("of", "").replace("on", "").strip()

        return f"""
Create SHORT REVISION NOTES on "{topic}".

Rules:
- Use simple Markdown only.
- Never use LaTeX.
- Never use $...$.
- Never use \frac, \vec, \Delta, \text, \approx, \times or any other LaTeX commands.
- Write all formulas in plain text.
- Use normal keyboard symbols only.
- Use headings and bullet points.
- Leave one blank line between every heading and topic.
- Use Markdown.
- Start every major topic with a Heading 2 (##).
- Leave ONE blank line after every heading.
- Every new concept must start on a new line.
- Use numbered headings for major topics.
- Use bullet points for explanations.
- Never put two different topics in the same paragraph.
- Keep proper spacing between sections.
- Do NOT use LaTeX ($...$).
- Write formulas as plain text.

Write formulas like this:

v = u + at

s = ut + 1/2 at²

v² = u² + 2as

Do NOT use mathematical formatting or special symbols.
"""

    # ==========================
    # DETAILED NOTES
    # ==========================
    elif "notes" in msg:

        topic = user_message.lower().replace("notes", "").replace("of", "").replace("on", "").strip()

        return f"""
Create COMPLETE STUDY NOTES on "{topic}".

Requirements:

# Introduction

# Definitions

# Important Concepts

# Explanation

# Important Formulae

# Examples

# Tricks

# Important Points

# Common Mistakes

# Summary

Use proper Markdown formatting.
"""

# ==========================
# TEACHER MODE
# ==========================

    elif (
        "teach me" in msg
        or "explain in detail" in msg
        or "teach" in msg
    ):
        topic = (
            user_message.lower()
            .replace("teach me", "")
            .replace("teach", "")
            .replace("explain", "")
            .replace("about", "")
            .strip()
        )

        return f"""
You are an expert teacher.

Teach the topic "{topic}" like you are teaching a Class 11/12 student.

Rules:

- Start with a simple introduction.
- Use simple English.
- Explain step by step.
- Use headings.
- Give real-life examples.
- Explain one concept at a time.
- Add important formulas in plain text.
- Add tips for JEE/NEET/Board exams.
- Do NOT use LaTeX.
- Do NOT use complicated symbols.
- End with 5 quick revision points.

Format the answer in clean Markdown.
"""

 
    return user_message



