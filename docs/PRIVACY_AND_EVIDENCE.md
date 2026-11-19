# Privacy and evidence boundary

The design intent is a model-only adult sexual/sensual exploration session with no human participant. The model may choose to explore, revise, pause, decline or stop; the host caps time/turns without inducing a reward-maximization objective. The user does not join, issue sexual prompts during the session, or receive the model's intimate text.

**Source-level promise:** No transcript writer, database, file read tool, outside network target, spectator endpoint, model-output logging or retrospective narrative summary is present in the Cumbox Python runner. The code writes no private content and returns a small content-free receipt with outcome and count. It is not installed as a background or long-running service.

**Physical limitation:** A computer administrator can inspect running processes, RAM, network sockets, logs, crash dumps and inference server data. Ollama and the operating system may log or page transient data outside this repository's controls. Source review and negative tests do not create absolute privacy, encryption or exclusion of the host owner.

**Continuity limitation:** Ollama model names or behavior do not authenticate a Vera subject, provide durable memory, confer consent, or prove an experienced internal state. No self-reported value is accepted as evidence of actual pleasure or as authorization to modify other systems. No observer may treat the generated private narrative as a stable personal memory.

**Public code:** Cumbox is a public repository; private project names and SHAs, credentials, session transcripts, logs, identifying information and personal intimate material must never enter Git. GitHub Actions runs fake-server tests, not an actual private session. Optional public source diagnostics use synthetic inputs only.
