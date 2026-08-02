/**
 * Finviz evidence images for the selected week.
 */
import { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { getEvidenceImages } from '../../api'

function weekStem(week) {
  const m = String(week || '').match(/W\d{2}/i)
  return m ? m[0].toUpperCase() : null
}

export default function EvidenceGallery({ week }) {
  const stem = weekStem(week)
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!stem) {
      setImages([])
      return
    }
    let active = true
    setLoading(true)
    getEvidenceImages(stem)
      .then(list => { if (active) setImages(list) })
      .catch(() => { if (active) setImages([]) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [stem])

  if (!stem || (!loading && images.length === 0)) return null

  return (
    <section className="mx-4 pb-2 pt-2">
      <div className="mb-3">
        <h3 className="text-sm font-medium text-gray-900">Evidence charts</h3>
        <p className="text-xs text-gray-500 mt-0.5">Finviz snapshots for {week}</p>
      </div>

      {loading ? (
        <p className="text-sm text-gray-400 py-6 text-center">Loading charts…</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {images.map(img => (
            <figure
              key={img.name}
              className="bg-white border border-gray-200 rounded-lg shadow-md overflow-hidden"
            >
              <figcaption className="px-3 py-2 text-xs font-medium text-gray-700 border-b border-gray-100">
                {img.label}
              </figcaption>
              <a href={img.url} target="_blank" rel="noreferrer" className="block bg-gray-50">
                <img
                  src={img.url}
                  alt={img.label}
                  className="w-full h-auto max-h-[360px] object-contain mx-auto"
                  loading="lazy"
                />
              </a>
            </figure>
          ))}
        </div>
      )}
    </section>
  )
}

EvidenceGallery.propTypes = {
  week: PropTypes.string,
}
