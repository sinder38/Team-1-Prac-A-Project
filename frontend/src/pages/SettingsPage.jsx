/**
 * About page — app info and data-source notice. No user account or login
 * (this is a static, single-user demo with no server).
 */
import PropTypes from 'prop-types'
import { Info, Database, GitBranch } from 'lucide-react'

function Card({ icon: Icon, title, children }) {
  return (
    <section className="bg-white border border-gray-200 rounded-md shadow-md p-5">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-gray-500" />
        <p className="text-sm font-medium">{title}</p>
      </div>
      <div className="text-sm text-gray-600 space-y-1">{children}</div>
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
    <div className="flex-1 overflow-auto p-4 md:p-6 space-y-4 max-w-2xl">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">About</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          How this dashboard works and where its data comes from
        </p>
      </div>

      <Card icon={Info} title="No accounts">
        <p>
          This is a single-user, browser-only tool — there is no login, no server,
          and no client/account separation. Everything runs locally in your browser.
        </p>
      </Card>

      <Card icon={Database} title="Example data">
        <p>
          Charts and agent outputs use bundled example data so the UI is fully
          viewable without a backend. See{' '}
          <code className="text-xs bg-gray-100 px-1 rounded">src/lib/exampleData.js</code>{' '}
          and the stubs in{' '}
          <code className="text-xs bg-gray-100 px-1 rounded">src/api/</code>.
        </p>
      </Card>

      <Card icon={GitBranch} title="Pipeline control">
        <p>
          The pipeline is run one stage at a time from the Dashboard — you decide
          when each step executes. The final stage is your Human Score report.
        </p>
      </Card>
    </div>
  )
}
