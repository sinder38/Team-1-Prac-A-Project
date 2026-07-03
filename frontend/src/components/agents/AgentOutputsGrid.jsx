/**
 * Grid of three agent cards plus the LLM comparison section.
 */
import { useState } from 'react'
import PropTypes from 'prop-types'
import AgentCard, { AgentCardPlaceholder } from './AgentCard'
import LlmComparisonPanel from './LlmComparisonPanel'

const AGENT_IDS = ['almanac', 'macro', 'technical']

export default function AgentOutputsGrid({ outputs = {} }) {
  const [open, setOpen] = useState({})
  const hasAny = AGENT_IDS.some(id => outputs[id])

  return (
    <div className="px-4 pb-6 space-y-4">
      <div>
        <h3 className="text-sm font-medium text-gray-900">Agent Signals</h3>
        <p className="text-xs text-gray-500 mt-0.5">Latest outputs from each agent</p>
      </div>

      {!hasAny ? (
        <div className="rounded-xl border border-dashed border-gray-200 bg-white px-4 py-10 text-center">
          <p className="text-sm text-gray-500">No agent outputs for this week</p>
          <p className="text-xs text-gray-400 mt-1">Run the pipeline or select another week</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-stretch">
          {AGENT_IDS.map(id =>
            outputs[id] ? (
              <AgentCard
                key={id}
                id={id}
                data={outputs[id]}
                open={!!open[id]}
                onToggle={() => setOpen(prev => ({ ...prev, [id]: !prev[id] }))}
              />
            ) : (
              <AgentCardPlaceholder key={id} id={id} />
            ),
          )}
        </div>
      )}

      <LlmComparisonPanel
        comparison={outputs.llmComparison}
        expanded={!!open.llm}
        onToggle={() => setOpen(prev => ({ ...prev, llm: !prev.llm }))}
      />
    </div>
  )
}

AgentOutputsGrid.propTypes = {
  outputs: PropTypes.object,
}
