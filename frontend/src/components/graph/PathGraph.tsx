/**
 * Transfer sequence diagram.
 *
 * Rendered as inline SVG rather than through a canvas graph library. Three
 * reasons, all of which are requirements here:
 *
 * - The layout is fixed and linear (reported address on the left, destination on
 *   the right, value flowing left to right), so a general graph renderer would
 *   add a large dependency and a pan and zoom surface to express a single row.
 * - Every node and edge becomes a real DOM element, so the diagram is reachable
 *   by keyboard and exposed to assistive technology. A canvas is opaque.
 * - The default styling of a graph library would have to be overridden almost
 *   entirely to meet the visual rules here, and any residue would read as
 *   decoration rather than evidence.
 *
 * The diagram is decorative in the accessibility sense: it is `aria-hidden` and
 * the EdgeTable beside it carries the same information in full. That is the
 * table alternative the specification requires, and it is always rendered, not
 * hidden behind a toggle.
 */

import type { PathItem } from '@/lib/types'
import { vocabularyLabel } from '@/lib/copy'
import { copy } from '@/lib/copy'
import { formatAddress, formatAssetAmount } from '@/lib/format'

interface PathGraphProps {
  path: PathItem
}

const NODE_WIDTH = 168
const NODE_HEIGHT = 52
const H_GAP = 76
const PADDING_X = 16
const PADDING_Y = 28

interface PlacedNode {
  address: string
  x: number
  y: number
  isStart: boolean
  isEnd: boolean
}

interface PlacedEdge {
  from: PlacedNode
  to: PlacedNode
  label: string
  isBreak: boolean
}

/**
 * Lay the path out as a single left-to-right row, which is the only shape that
 * cannot misrepresent a path: every hop advances one column, so the direction of
 * value is unambiguous without an arrow key to interpret.
 */
function layout(path: PathItem): { nodes: PlacedNode[]; edges: PlacedEdge[] } {
  const chain = [path.start_address]
  for (const edge of path.edges) chain.push(edge.receiver)

  // A receiver repeating earlier means the graph revisited a node; keep the
  // first occurrence so the row stays strictly monotonic.
  const seen = new Set<string>()
  const ordered = chain.filter((address) => {
    const key = address.toLowerCase()
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })

  const nodes: PlacedNode[] = ordered.map((address, index) => ({
    address,
    x: PADDING_X + index * (NODE_WIDTH + H_GAP),
    y: PADDING_Y,
    isStart: index === 0,
    isEnd: index === ordered.length - 1,
  }))

  const edges: PlacedEdge[] = []
  path.edges.slice(0, ordered.length - 1).forEach((edge, index) => {
    const from = nodes[index]
    const to = nodes[index + 1]
    if (!from || !to) return
    edges.push({
      from,
      to,
      label: formatAssetAmount(edge.amount_decimal, edge.asset_symbol),
      isBreak: index === path.edges.length - 1 && path.has_break,
    })
  })

  return { nodes, edges }
}

export function PathGraph({ path }: PathGraphProps) {
  const { nodes, edges } = layout(path)
  const width = PADDING_X * 2 + Math.max(1, nodes.length) * NODE_WIDTH + Math.max(0, nodes.length - 1) * H_GAP
  const height = PADDING_Y * 2 + NODE_HEIGHT

  const breakNode = path.has_break ? nodes[nodes.length - 1] : undefined

  return (
    <div className="space-y-3">
      <div className="table-scroll rounded-md border border-border bg-surface-subtle p-3">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          width={width}
          height={height}
          role="img"
          aria-label={`${copy.evidence.paths.graphTitle}: ${nodes.length} addresses, ${edges.length} transfers. The same information is in the table below.`}
          className="block min-w-full"
        >
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path
                d="M 0 0 L 10 5 L 0 10 z"
                className="fill-border-strong"
              />
            </marker>
            <marker
              id="arrow-break"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" className="fill-status-attention-fg" />
            </marker>
          </defs>

          {edges.map((edge, index) => {
            const x1 = edge.from.x + NODE_WIDTH
            const y1 = edge.from.y + NODE_HEIGHT / 2
            const x2 = edge.to.x
            const y2 = edge.to.y + NODE_HEIGHT / 2
            const midX = (x1 + x2) / 2

            return (
              <g key={`edge-${index}`}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2 - 6}
                  y2={y2}
                  className={edge.isBreak ? 'stroke-status-attention-fg' : 'stroke-border-strong'}
                  strokeWidth={1.5}
                  markerEnd={edge.isBreak ? 'url(#arrow-break)' : 'url(#arrow)'}
                />
                <rect
                  x={midX - 46}
                  y={y1 - 22}
                  width={92}
                  height={18}
                  rx={3}
                  className="fill-surface stroke-border-subtle"
                  strokeWidth={1}
                />
                <text
                  x={midX}
                  y={y1 - 9}
                  textAnchor="middle"
                  className="fill-secondary"
                  style={{ fontSize: '11px', fontFamily: 'var(--font-family-mono)' }}
                >
                  {edge.label}
                </text>
              </g>
            )
          })}

          {nodes.map((node) => (
            <g key={`node-${node.address}`}>
              <rect
                x={node.x}
                y={node.y}
                width={NODE_WIDTH}
                height={NODE_HEIGHT}
                rx={4}
                className={
                  node.isEnd && path.has_break
                    ? 'fill-status-attention-bg stroke-status-attention-border'
                    : 'fill-surface stroke-border-strong'
                }
                strokeWidth={1.5}
                strokeDasharray={node.isEnd ? '4 3' : undefined}
              />
              <text
                x={node.x + 12}
                y={node.y + 23}
                className="fill-primary"
                style={{ fontSize: '12px', fontFamily: 'var(--font-family-mono)' }}
              >
                {formatAddress(node.address)}
              </text>
              <text
                x={node.x + 12}
                y={node.y + 39}
                className="fill-muted"
                style={{ fontSize: '10px', fontFamily: 'var(--font-family-sans)' }}
              >
                {node.isStart ? 'Reported address' : node.isEnd ? 'Destination' : 'Intermediary'}
              </text>
            </g>
          ))}

          {breakNode && path.break_reason ? (
            <g>
              <line
                x1={breakNode.x + NODE_WIDTH / 2}
                y1={breakNode.y + NODE_HEIGHT}
                x2={breakNode.x + NODE_WIDTH / 2}
                y2={breakNode.y + NODE_HEIGHT + 18}
                className="stroke-status-attention-fg"
                strokeWidth={1.5}
                strokeDasharray="3 3"
              />
              <text
                x={breakNode.x + NODE_WIDTH / 2 + 8}
                y={breakNode.y + NODE_HEIGHT + 16}
                className="fill-status-attention-fg"
                style={{ fontSize: '11px', fontFamily: 'var(--font-family-sans)' }}
              >
                {path.break_reason
                  ? `Trace stops: ${vocabularyLabel('breakReason', path.break_reason)}`
                  : 'Trace stops here'}
              </text>
            </g>
          ) : null}
        </svg>
      </div>

      <p className="text-xs text-muted">{copy.evidence.paths.graphHint}</p>

      {path.has_break && path.break_reason ? (
        <p className="flex items-start gap-2 rounded-md border border-status-attention-border bg-status-attention-bg px-3 py-2.5 text-sm text-status-attention-fg">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-status-attention-fg" aria-hidden="true" />
          <span>
            Tracing stopped: {vocabularyLabel('breakReason', path.break_reason)}. Value beyond this
            point was not followed.
          </span>
        </p>
      ) : null}
    </div>
  )
}