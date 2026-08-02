/**
 * Candlestick / relative chart (lightweight-charts).
 */
import { useEffect, useRef } from 'react'
import PropTypes from 'prop-types'
import { createChart } from 'lightweight-charts'
import { rebaseCloses } from '../../lib/chartExtras'

export default function PriceChart({ data, showVolume = true, relative = false }) {
  const containerRef = useRef(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el || !data?.candles?.length) return

    const decimals = relative ? 2 : (data.decimals ?? 2)
    const chart = createChart(el, {
      autoSize: true,
      layout: { background: { color: '#ffffff' }, textColor: '#374151', fontFamily: 'inherit' },
      grid: { vertLines: { color: '#f3f4f6' }, horzLines: { color: '#f3f4f6' } },
      rightPriceScale: { borderColor: '#e5e7eb' },
      timeScale: { borderColor: '#e5e7eb', rightOffset: 4 },
      crosshair: { mode: 1 },
    })

    if (relative) {
      const line = chart.addLineSeries({
        color: '#111827',
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: true,
        priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
      })
      line.setData(rebaseCloses(data.candles))
    } else {
      const candles = chart.addCandlestickSeries({
        upColor: '#16a34a',
        downColor: '#dc2626',
        borderUpColor: '#16a34a',
        borderDownColor: '#dc2626',
        wickUpColor: '#16a34a',
        wickDownColor: '#dc2626',
        priceFormat: { type: 'price', precision: decimals, minMove: 1 / 10 ** decimals },
      })
      candles.setData(data.candles || [])

      const lineOpts = {
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
        lineWidth: 2,
      }
      if (data.ema8?.length) {
        chart.addLineSeries({ ...lineOpts, color: '#2563eb' }).setData(data.ema8)
      }
      if (data.ema21?.length) {
        chart.addLineSeries({ ...lineOpts, color: '#f59e0b' }).setData(data.ema21)
      }
    }

    if (showVolume && !relative && data.volume?.length) {
      const vol = chart.addHistogramSeries({ priceScaleId: '', priceFormat: { type: 'volume' } })
      vol.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
      vol.setData(data.volume)
    }

    chart.timeScale().fitContent()
    return () => chart.remove()
  }, [data, showVolume, relative])

  return <div ref={containerRef} className="w-full h-[440px]" />
}

PriceChart.propTypes = {
  data: PropTypes.shape({
    decimals: PropTypes.number,
    candles: PropTypes.array,
    ema8: PropTypes.array,
    ema21: PropTypes.array,
    volume: PropTypes.array,
  }),
  showVolume: PropTypes.bool,
  relative: PropTypes.bool,
}
