# Delta Engine: Principles and Architecture

The Delta Engine compares a locked prediction with the following completed
week. It measures accuracy, keeps valid historical results and suggests small
weight changes for the next sprint.

## How Delta Works

```mermaid
flowchart TD
    P["Locked prediction<br/>vWn"]
    A["Completed actuals<br/>Wn + 1"]
    AUTO["Pipeline or API trigger"]
    MANUAL["CLI with completed actuals"]
    F{"Automated run:<br/>Friday market closed?"}
    V{"Correct week pair?"}
    N["Parse and normalise<br/>asset, direction, range, confidence"]
    S["Score each matching asset"]
    D["Direction score<br/>correct or incorrect"]
    R["Range score<br/>hit, miss and error"]
    H["Add earlier valid week pairs"]
    C["Calculate current and<br/>cumulative accuracy"]
    W{"Accuracy below 60%?"}
    K["Keep reviewed weights"]
    T["Suggest a small 0.05<br/>trial weight transfer"]
    X["Write next-sprint prescription"]
    O["Delta outputs<br/>Markdown report + JSON artifact"]
    E["Stop with a clear error"]

    AUTO --> F
    F -->|No| E
    F -->|Yes| V
    MANUAL --> V
    P --> V
    A --> V
    V -->|No| E
    V -->|Yes| N
    N --> S
    S --> D
    S --> R
    D --> H
    R --> H
    H --> C
    C --> W
    W -->|No| K
    W -->|Yes| T
    K --> X
    T --> X
    X --> O
```

The automated pipeline and API enforce the Friday-close check. The CLI is a
manual tool and expects the user to provide completed actuals. The engine never
estimates a missing week. If an older prediction or its matching actuals file
is unavailable, that week is skipped and explained in the report. Suggested
weights are reviewable recommendations; Delta does not silently replace the
team's final decision.

## Application Architecture

```mermaid
flowchart LR
    subgraph EntryPoints["Entry points"]
        CLI["CLI<br/>run_delta_engine.py"]
        PIPE["Weekly pipeline<br/>run_pipeline.py"]
        API["Backend API<br/>POST /stages/delta"]
    end

    subgraph Inputs["Project inputs"]
        PRED["Locked prediction<br/>data/final prediction/"]
        EVID["Evidence actuals<br/>file or API artifact"]
        OLD["Previous Delta JSON<br/>reviewed weights + history"]
    end

    subgraph Delta["Delta package"]
        STAGE["run_delta()<br/>week and Friday-close checks"]
        AGENT["DeltaAgent<br/>coordinates one Delta run"]
        PARSE["parsing.py<br/>read and normalise"]
        SCORE["scoring.py<br/>accuracy and weights"]
        MODEL["models.py<br/>shared result types"]
        REPORT["report.py<br/>Markdown rendering"]
    end

    subgraph Outputs["Stored outputs"]
        MD["data/qa/delta_Wn.md"]
        JSON["data/outputs/delta/<br/>delta_Wn.json"]
    end

    subgraph Consumers["Application consumers"]
        CALAPI["GET /calibration/<br/>accuracy-tracker"]
        UI["Calibration page<br/>charts, coverage and weights"]
        LLM["Next LLM synthesis<br/>Delta context"]
    end

    CLI --> AGENT
    PIPE --> STAGE
    API --> STAGE
    STAGE --> AGENT

    PRED --> AGENT
    EVID -->|API and pipeline| STAGE
    EVID -->|CLI path| AGENT
    OLD --> AGENT

    AGENT --> PARSE
    PARSE --> SCORE
    SCORE -->|Scored rows| AGENT
    AGENT --> REPORT
    MODEL -.-> AGENT
    MODEL -.-> PARSE
    MODEL -.-> SCORE
    MODEL -.-> REPORT

    AGENT --> JSON
    REPORT --> MD
    JSON --> CALAPI
    CALAPI --> UI
    JSON -.-> LLM
```

The three entry points share the same `DeltaAgent`, so the scoring rules stay
the same whether Delta runs from the command line, the weekly pipeline or the
web application.
