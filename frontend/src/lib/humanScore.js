/**
 * Human Score report logic: what the AI "said" per dimension and how to render
 * the report as Markdown. Kept out of the form component so it can be unit-tested
 * and reused. Modelled on data/human/human_score_W*.md.
 */
import { HUMAN_DIMENSIONS, EVIDENCE_SOURCES } from './constants'
import { prepareAgentCard } from './agentDisplay'
import { summarizeModelAgreement } from './bias'

export const PLACEHOLDER = '________'

/** Per-dimension summary of the AI outputs, shown in the "AI Said" column. */
export function aiSaidFor(outputs = {}) {
  const almanac = prepareAgentCard('almanac', outputs.almanac)
  const macro = prepareAgentCard('macro', outputs.macro)
  const technical = prepareAgentCard('technical', outputs.technical)

  return {
    macro: macro?.bias || '—',
    technical: technical?.bias || '—',
    almanac: almanac?.bias || '—',
    aiAgreement: summarizeModelAgreement(outputs.llmComparison),
    wildCard: 'nothing specifically flagged',
  }
}

function signed(score) {
  const n = Number(score) || 0
  return n > 0 ? `+${n}` : `${n}`
}

/** Render a submitted report as Markdown (used by the "Copy as Markdown" action). */
export function buildHumanScoreMarkdown(form, ctx) {
  const { week = '—', consensus = '—', aiSaid = {}, total = 0 } = ctx || {}
  const lines = []

  lines.push(`# Human Score Report — ${week}`, '')
  lines.push('## AI Consensus', '', `**${consensus}**`, '', '---', '')
  lines.push('## Human Score Table', '')
  lines.push('| Dimension | AI Said | Team Score | Team Reasoning |')
  lines.push('| --- | --- | --- | --- |')
  HUMAN_DIMENSIONS.forEach(d => {
    const score = form.scores[d.key]
    lines.push(
      `| ${d.label} | ${aiSaid[d.key] ?? '—'} | ${signed(score)} | ${form.reasoning[d.key] || PLACEHOLDER} |`,
    )
  })
  lines.push('', '## Human Score Total', '', `**${signed(total)}**`, '', '---', '')
  lines.push('## Human Call', '', `**${form.humanCall}**`, '', '---', '')
  lines.push('## Confidence', '', `**${form.confidence}**`, '', '---', '')
  lines.push('## Override Paragraph', '', form.overrideParagraph || PLACEHOLDER, '', '---', '')
  lines.push('## Wild Card Insight', '', form.wildCardInsight || PLACEHOLDER, '', '---', '')
  lines.push('## Invalidation Condition', '', form.invalidation || PLACEHOLDER, '', '---', '')
  lines.push('## Evidence Used', '')
  EVIDENCE_SOURCES.filter(s => form.evidence[s.key]).forEach(s => lines.push(`* ${s.label}`))

  return lines.join('\n')
}

/** Sum of the five team dimension scores. */
export function humanScoreTotal(form) {
  return HUMAN_DIMENSIONS.reduce((sum, d) => sum + (Number(form?.scores?.[d.key]) || 0), 0)
}
