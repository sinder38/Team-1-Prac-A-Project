/**
 * Human Score report logic: what the AI "said" per dimension and how to render
 * the report as Markdown. Kept out of the form component so it can be unit-tested
 * and reused. Modelled on data/human/human_score_W28.md.
 */
import { HUMAN_DIMENSIONS, EVIDENCE_SOURCES } from './constants'
import { prepareAgentCard } from './agentDisplay'
import { classifyBias, summarizeModelAgreement } from './bias'

export const PLACEHOLDER = '________'

const BREAKDOWN_LABELS = {
  macro: 'Macro',
  technical: 'Technical',
  almanac: 'Almanac',
  aiAgreement: 'AI Agreement',
  wildCard: 'Wild Card',
}

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

/** Format a team score with an explicit plus sign for positives. */
export function formatSignedScore(score) {
  return signed(score)
}

/** "2026-W28" / "W28" → "Week 28" for the report title. */
export function weekTitleLabel(week) {
  const m = String(week || '').match(/W(\d{1,2})/i)
  return m ? `Week ${Number(m[1])}` : week || '—'
}

/** Build the bold AI Consensus line, matching W28 style when model counts are known. */
export function formatConsensusHeading(consensus, llm) {
  const base = (consensus || '—').trim()
  const models = Array.isArray(llm?.models) ? llm.models : []
  if (!models.length || /\(\d+\s+of\s+\d+/i.test(base)) {
    return `**${base}**`
  }
  const direction = classifyBias(llm?.finalConsensus || base)
  const matching = models.filter(m => classifyBias(m?.consensus) === direction).length
  return `**${base} (${matching} of ${models.length} models)**`
}

function scoreBreakdown(form) {
  return HUMAN_DIMENSIONS.map(d => {
    const n = Number(form?.scores?.[d.key]) || 0
    return `${BREAKDOWN_LABELS[d.key]} ${signed(n)}`
  }).join(' + ')
}

/** Render a submitted report as Markdown (Copy as Markdown / export). */
export function buildHumanScoreMarkdown(form, ctx) {
  const {
    week = '—',
    consensus = '—',
    aiSaid = {},
    total = 0,
    llmComparison = null,
  } = ctx || {}
  const lines = []
  const titleWeek = weekTitleLabel(week)

  lines.push(`# Human Score Analyst Output — ${titleWeek}`, '')
  lines.push('## AI Consensus', '')
  lines.push(formatConsensusHeading(consensus, llmComparison), '')
  lines.push('---', '')

  lines.push('## Human Score Table', '')
  lines.push(
    '| Dimension                         | AI Said                                   | Team Score | Team Reasoning |',
  )
  lines.push(
    '| --------------------------------- | ----------------------------------------- | :--------: | -------------- |',
  )
  HUMAN_DIMENSIONS.forEach(d => {
    const score = form.scores?.[d.key]
    const reason = (form.reasoning?.[d.key] || PLACEHOLDER).replace(/\|/g, '/')
    const said = String(aiSaid[d.key] ?? '—').replace(/\|/g, '/')
    lines.push(
      `| **${d.label}** | ${said} | **${signed(score)}** | ${reason} |`,
    )
  })
  lines.push('', '---', '')

  lines.push('## Human Score Total', '')
  lines.push(`**${signed(total)}**`, '')
  lines.push(`(${scoreBreakdown(form)})`, '')
  lines.push('---', '')

  lines.push('## Five-Dimension Judgement', '')
  HUMAN_DIMENSIONS.forEach((d, i) => {
    const score = form.scores?.[d.key]
    const body = form.reasoning?.[d.key] || PLACEHOLDER
    lines.push(`### ${i + 1}. ${d.label} — Score: ${signed(score)}`, '')
    lines.push(body, '')
  })
  lines.push('---', '')

  lines.push('## Human Call', '', `**${form.humanCall || 'Neutral'}**`, '', '---', '')
  lines.push('## Confidence', '', `**${form.confidence || 'Medium'}**`, '', '---', '')
  lines.push('## Override Paragraph', '', form.overrideParagraph || PLACEHOLDER, '', '---', '')
  lines.push('## Wild Card Insight', '', form.wildCardInsight || PLACEHOLDER, '', '---', '')
  lines.push('## Invalidation Condition', '', form.invalidation || PLACEHOLDER, '', '---', '')
  lines.push('## Evidence Used', '')
  EVIDENCE_SOURCES.filter(s => form.evidence?.[s.key]).forEach(s => lines.push(`* ${s.label}`))

  return lines.join('\n')
}

/** Sum of the five team dimension scores. */
export function humanScoreTotal(form) {
  return HUMAN_DIMENSIONS.reduce((sum, d) => sum + (Number(form?.scores?.[d.key]) || 0), 0)
}

/** Bundle form + context for display and export. */
export function buildHumanScoreReport(form, { week, outputs, predictionDate }) {
  if (!form) return null
  const aiSaid = aiSaidFor(outputs)
  const consensus = outputs?.llmComparison?.finalConsensus || 'Pending — run the pipeline'
  return {
    form,
    week,
    predictionDate,
    consensus,
    aiSaid,
    total: humanScoreTotal(form),
    llmComparison: outputs?.llmComparison || null,
  }
}
