/**
 * About — what the app is, how the pipeline runs, where data comes from.
 */
import PropTypes from 'prop-types'
import { Activity, Database, GitBranch, Layers, Moon } from 'lucide-react'

function Card({ icon: Icon, title, children }) {
  return (
    <section className="bg-white border border-gray-200 rounded-xl shadow-md p-4 md:p-5">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-gray-500 shrink-0" />
        <h3 className="text-sm font-medium text-gray-900">{title}</h3>
      </div>
      <div className="text-sm text-gray-600 space-y-2 leading-relaxed">{children}</div>
    </section>
  )
}

Card.propTypes = {
  icon: PropTypes.elementType.isRequired,
  title: PropTypes.string.isRequired,
  children: PropTypes.node,
}

export default function SettingsPage() {
  return (
    <div className="flex-1 overflow-auto p-4 md:p-6 space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">About</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Market Intelligence — Team 1 · CP3405 Design Thinking 3
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card icon={Activity} title="What this is">
          <p>
            A weekly market-intelligence control panel: pull data, run Almanac /
            Macro / Technical agents, query LLMs, lock a Final Prediction, then
            score against actuals.
          </p>
          <p>
            Single-user local tool — no accounts or multi-tenant login. React UI
            talks to a Flask backend on your machine.
          </p>
        </Card>

        <Card icon={GitBranch} title="Pipeline">
          <p>
            Stages run one at a time from the Dashboard: data fetch → agents →
            LLM comparison → previous-week delta → human score / final prediction.
          </p>
          <p>
            Open a past week from the week picker to load archive outputs, charts
            as-of that date, and weekly actuals when they exist.
          </p>
        </Card>

        <Card icon={Database} title="Data">
          <p>
            Live prices and chart history come from yfinance via{' '}
            <code className="text-xs bg-gray-100 px-1 rounded">/market/history</code>.
            Macro inputs also use FRED where configured.
          </p>
          <p>
            Agent markdown, Finviz evidence PNGs, and{' '}
            <code className="text-xs bg-gray-100 px-1 rounded">actuals_WXX.md</code>{' '}
            live under <code className="text-xs bg-gray-100 px-1 rounded">data/</code>{' '}
            and are served through <code className="text-xs bg-gray-100 px-1 rounded">/artifacts/*</code>.
          </p>
        </Card>

        <Card icon={Layers} title="Pages">
          <ul className="list-disc pl-4 space-y-1">
            <li>
              <span className="font-medium text-gray-800">Dashboard</span> — run the
              pipeline and review agent / LLM / HSR / Final Prediction cards
            </li>
            <li>
              <span className="font-medium text-gray-800">Charts</span> — OHLC, index
              compare, macro strip, sector heatmap, pred vs weekly actual
            </li>
            <li>
              <span className="font-medium text-gray-800">Logs</span> — stage status for
              the current run
            </li>
            <li>
              <span className="font-medium text-gray-800">Calibration</span> — direction /
              range accuracy over scored weeks
            </li>
          </ul>
        </Card>

        <Card icon={Moon} title="Theme">
          <p>
            Defaults to your system light/dark preference. Toggle from the moon/sun
            control at the bottom of the left nav — that choice is saved in this
            browser and restored on reload.
          </p>
          <p>
            Page and week also sync into the URL (
            <code className="text-xs bg-gray-100 px-1 rounded">?page=&amp;week=</code>
            ) so you can share or bookmark a view.
          </p>
        </Card>
      </div>
    </div>
  )
}
