/**
 * Candlestick price chart (ProRealTime / yfinance style) using lightweight-charts.
 * Renders candles plus 8 EMA and 21 EMA overlays and a volume histogram.
 */
import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

export default function PriceChart({ data }) {
  const containerRef = useRef(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el || !data) return

    const decimals = data.decimals ?? 2
    const chart = createChart(el, {
      autoSize: true,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#374151',
        fontFamily: 'inherit',
      },
      grid: {
        vertLines: { color: '#f3f4f6' },
        horzLines: { color: '#f3f4f6' },
      },
      rightPriceScale: { borderColor: '#e5e7eb' },
      timeScale: { borderColor: '#e5e7eb', rightOffset: 4 },
      crosshair: { mode: 1 },
    })

    const candle = chart.addCandlestickSeries({
      upColor: '#16a34a',
      downColor: '#dc2626',
      borderUpColor: '#16a34a',
      borderDownColor: '#dc2626',
      wickUpColor: '#16a34a',
      wickDownColor: '#dc2626',
      priceFormat: { type: 'price', precision: decimals, minMove: 1 / 10 ** decimals },
    })
    candle.setData(data.candles)

    const ema8 = chart.addLineSeries({
      color: '#2563eb',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    })
    ema8.setData(data.ema8)

    const ema21 = chart.addLineSeries({
      color: '#f59e0b',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    })
    ema21.setData(data.ema21)

    if (data.volume && data.volume.length) {
      const vol = chart.addHistogramSeries({
        priceScaleId: '',
        priceFormat: { type: 'volume' },
      })
      vol.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
      vol.setData(data.volume)
    }

    chart.timeScale().fitContent()

    return () => chart.remove()
  }, [data])

  return <div ref={containerRef} className="w-full h-[440px]" />
}
