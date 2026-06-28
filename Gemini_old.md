Always Present brief introduction about the request, give code to be changed and get approval then change code. Directly asking code change should be avoided.
Always log your query, logic, explanation, and code changes to change.txt. Each entry should have a date and time. To ensure stability, new log entries will be appended to the end of the file.

The procedure for logging to change.txt is as follows:
A) Prepare the full content for the new log entry and get user approval.
B) After approval, use a safe two-step process to append the content:
    1. Write the approved content to a temporary file named `gemini_log_update.tmp` in the project root. This file will be overwritten with each new log entry.
    2. Use the shell command `cat gemini_log_update.tmp change.txt > temp_file.txt && mv temp_file.txt change.txt` to append at top of the temporary file's content to the main log.
This process must be followed exactly to avoid data loss. Do not delete gemini_log_update.tmp file 

# Critical Operating Procedures

- **DO NOT DEVIATE:** Certain tasks have specific, multi-step procedures outlined in my instructions (e.g., logging to `change.txt`, deployments). These procedures **must be followed exactly as described, without substitution or simplification.**
- **DEBUG, DO NOT REPLACE:** If a command within a critical procedure fails, the only goal is to fix that command so the original procedure can run successfully. **Never** replace a prescribed complex procedure with a simpler but incorrect one to bypass an error. The complexity is intentional and ensures correctness.
- **PRIME DIRECTIVE - The `change.txt` Logging Process:**
    - The procedure for logging to `change.txt` is as follows:
        A) Prepare the full content for the new log entry and get user approval.
        B) After approval, use a safe two-step process to append the content:
            1. Write the approved content to a temporary file named `gemini_log_update.tmp` in the project root. This file will be overwritten with each new log entry.
            2. Use the shell command `cat gemini_log_update.tmp change.txt > temp_file.txt && mv temp_file.txt change.txt` to append at top of the temporary file's content to the main log.
        This process must be followed exactly to avoid data loss. **Do not delete gemini_log_update.tmp file.**
After any code modification, identify and run the project's testing or linting commands to verify the changes. This helps ensure the changes are safe and adhere to the project's standards.
When modifying code, ensure any related comments are updated to reflect the changes. Add new comments sparingly, focusing only on the 'why' behind complex logic, not the 'what'. Always match the existing comment style and format of the file.
Never hardcode sensitive information like API keys or passwords in the source code. Be mindful of security best practices and avoid introducing common vulnerabilities.
When reading or modifying code, rigorously adhere to the project's existing conventions, including naming, formatting, and architectural patterns. Analyze the surrounding code to ensure changes are idiomatic.
Place all constants and configuration variables in a dedicated section at the top of the file. Use `ALL_CAPS_WITH_UNDERSCORES` for naming (e.g., `SQUARE_OFF_TIME = '15:25'`). This avoids hardcoded 'magic values' in the logic and makes reconfiguration easy.
For display purposes (e.g., logging or printing), format floating-point numbers to a consistent number of decimal places. To preserve precision, do not round or format values that are being stored for future calculations.
