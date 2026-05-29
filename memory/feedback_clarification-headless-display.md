---
name: clarification-headless-display
description: Graceful handling of display function in headless/server environments
metadata:
  type: feedback
---

When the graphical display environment is not available (headless server), the display function should log an error message and return normally (non-blocking) rather than crashing or requiring complex error handling.

**Why**: This allows batch/tournament modes to continue running without interruption while still making the error visible in logs for debugging.

**How to apply**: When implementing the post-game display function, wrap the display logic in a try/catch block that logs any display-related errors and returns gracefully, allowing the calling code to continue execution.