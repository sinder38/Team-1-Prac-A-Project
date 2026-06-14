# Decision Log — W24 Development

## Scope of Automation

The team decided to automate four specialist agents — Technical, Almanac, Macro, and Evidence — alongside a flexible layer supporting multiple LLM providers. This scope was chosen deliberately: the work divides cleanly across five contributors with minimal overlap, given that each agent operates on its own data source and follows a shared, pre-defined structure.

A lightweight pipeline was also implemented to execute these agents in sequence using GitHub Actions and Python scripts, making it possible to run the full workflow without manual intervention.

## Why Agents First

The agents sit at the very beginning of the pipeline. Any errors or inconsistencies introduced at that stage propagate forward and compound, so getting them right early reduces risk for all downstream work. Addressing them first also unblocked other contributors who depend on agent outputs.

## Fetch and Process as One Step

For all agents except the LLM layer, data fetching and processing were combined into a single step rather than separated. This reflects the reality that each agent has its own dedicated data source, and modern libraries make retrieval straightforward enough that a separate fetch abstraction would add complexity without practical benefit.

## Output Handling

Writing agent outputs to disk was kept separate from the agents themselves. This means agents are only responsible for producing their results, while a dedicated module handles how and where those results are saved. This makes it easier to change output formats or storage locations in the future without modifying agent logic.

## Pipeline Context

A shared context object was introduced to collect each agent's output before it reaches the LLM stage. Rather than passing outputs individually, everything is gathered in one place and handed to the LLM as a single package. This keeps the LLM stage decoupled from the specifics of how many agents ran or in what order.

## Quality Enforcement

Tests were added to verify the integration points between agents, the shared context, and the LLM prompt-building stage. These are the areas most likely to break silently when a new agent is added or a schema changes. Automated type checking was also configured to run on every code change, catching structural errors before they reach review.
