/**
 * Catches render-time errors so a single broken component doesn't blank the
 * whole app. Shows a minimal recovery UI instead of a white screen.
 */
import { Component } from 'react'
import PropTypes from 'prop-types'
import { AlertTriangle } from 'lucide-react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    // TODO (backend task): forward to a logging endpoint when available.
    console.error('Unhandled UI error:', error, info)
  }

  handleReset = () => this.setState({ error: null })

  render() {
    const { error } = this.state
    if (!error) return this.props.children

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="max-w-md w-full bg-white border border-gray-200 rounded-lg shadow-md p-6 text-center">
          <div className="mx-auto w-10 h-10 rounded-full bg-red-50 flex items-center justify-center mb-3">
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <h1 className="text-base font-semibold text-gray-900">Something went wrong</h1>
          <p className="text-sm text-gray-500 mt-1">
            The screen hit an unexpected error. You can try again below.
          </p>
          {error?.message && (
            <p className="mt-3 text-xs text-gray-400 bg-gray-50 border border-gray-100 rounded-md px-3 py-2 break-words">
              {error.message}
            </p>
          )}
          <button
            onClick={this.handleReset}
            className="mt-4 px-4 py-2 rounded-md text-sm font-medium bg-gray-900 text-white hover:bg-gray-800"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node,
}
