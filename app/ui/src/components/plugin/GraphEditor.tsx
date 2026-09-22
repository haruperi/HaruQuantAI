/**
 * Graph editor component rendering nodes, ports, and lossless placeholders for unavailable plugins.
 */

import React, { useState } from 'react';
import type {
  CatalogView,
  EdgeSpec,
  GraphDocument,
  NodeSpec,
} from '../../api/contracts.generated';
import { ParameterForm } from './ParameterForm';

export interface GraphEditorProps {
  document: GraphDocument;
  catalog: CatalogView | null;
  onChange: (doc: GraphDocument) => void;
  onValidate?: () => void;
  onEvaluate?: () => void;
  onExport?: () => void;
  disabled?: boolean;
}

export function GraphEditor({
  document,
  catalog,
  onChange,
  onValidate,
  onEvaluate,
  onExport,
  disabled = false,
}: GraphEditorProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const selectedNode = document.spec.nodes.find((n) => n.id === selectedNodeId);

  const getCatalogEntry = (pluginRefStr: string) => {
    return catalog?.entries.find(
      (e) => e.ref === pluginRefStr || e.ref.startsWith(`${pluginRefStr}@`),
    );
  };

  const handleAddNode = (pluginRefStr: string) => {
    const entry = getCatalogEntry(pluginRefStr);
    if (!entry) return;

    const newId = `node_${Date.now().toString(36)}`;
    const op = entry.operations[0];
    const defaultParams: Record<string, unknown> = {};
    if (op) {
      for (const p of op.parameters) {
        if (p.default !== undefined) {
          defaultParams[p.key] = p.default;
        }
      }
    }

    const newNode: NodeSpec = {
      id: newId,
      plugin_ref: entry.ref,
      operation_id: op ? op.operation_id : 'compute',
      parameters: defaultParams,
      title: `${entry.title} (${newId})`,
    };

    const updatedDoc: GraphDocument = {
      ...document,
      spec: {
        ...document.spec,
        nodes: [...document.spec.nodes, newNode],
      },
    };
    onChange(updatedDoc);
    setSelectedNodeId(newId);
  };

  const handleRemoveNode = (nodeId: string) => {
    const updatedDoc: GraphDocument = {
      ...document,
      spec: {
        ...document.spec,
        nodes: document.spec.nodes.filter((n) => n.id !== nodeId),
        edges: document.spec.edges.filter(
          (e) => e.source.node_id !== nodeId && e.target.node_id !== nodeId,
        ),
        designated_roots: document.spec.designated_roots.filter(
          (r) => r.node_id !== nodeId,
        ),
      },
    };
    onChange(updatedDoc);
    if (selectedNodeId === nodeId) {
      setSelectedNodeId(null);
    }
  };

  const handleParametersChange = (nodeId: string, params: Record<string, unknown>) => {
    const updatedNodes = document.spec.nodes.map((n) =>
      n.id === nodeId ? { ...n, parameters: params } : n,
    );
    onChange({
      ...document,
      spec: {
        ...document.spec,
        nodes: updatedNodes,
      },
    });
  };

  const handleAddEdge = (
    srcNodeId: string,
    srcPort: string,
    tgtNodeId: string,
    tgtPort: string,
  ) => {
    const newEdge: EdgeSpec = {
      source: { node_id: srcNodeId, port_key: srcPort },
      target: { node_id: tgtNodeId, port_key: tgtPort },
    };
    onChange({
      ...document,
      spec: {
        ...document.spec,
        edges: [...document.spec.edges, newEdge],
      },
    });
  };

  const handleRemoveEdge = (index: number) => {
    const updatedEdges = [...document.spec.edges];
    updatedEdges.splice(index, 1);
    onChange({
      ...document,
      spec: {
        ...document.spec,
        edges: updatedEdges,
      },
    });
  };

  return (
    <div className="graph-editor">
      <div className="graph-toolbar">
        <div className="toolbar-actions">
          {onValidate && (
            <button
              type="button"
              className="btn btn-secondary"
              disabled={disabled}
              onClick={onValidate}
            >
              Validate Graph
            </button>
          )}
          {onEvaluate && (
            <button
              type="button"
              className="btn btn-primary"
              disabled={disabled}
              onClick={onEvaluate}
            >
              Evaluate Run
            </button>
          )}
          {onExport && (
            <button
              type="button"
              className="btn btn-secondary"
              disabled={disabled}
              onClick={onExport}
            >
              Export Code
            </button>
          )}
        </div>
        <div className="add-node-picker">
          <select
            disabled={disabled || !catalog}
            value=""
            onChange={(e) => {
              if (e.target.value) handleAddNode(e.target.value);
            }}
            className="text-input"
          >
            <option value="">+ Add Quantitative Plugin Node...</option>
            {catalog?.entries
              .filter((e) => e.kind !== 'workspace')
              .map((e) => (
                <option key={e.ref} value={e.ref}>
                  {e.title} ({e.ref})
                </option>
              ))}
          </select>
        </div>
      </div>

      <div className="graph-canvas-container">
        <div className="nodes-board">
          <h3>Nodes ({document.spec.nodes.length})</h3>
          {document.spec.nodes.length === 0 ? (
            <div className="empty-graph-notice">
              No nodes in strategy graph. Add nodes from the dropdown above.
            </div>
          ) : (
            <div className="nodes-list">
              {document.spec.nodes.map((node) => {
                const entry = getCatalogEntry(node.plugin_ref);
                const isSelected = node.id === selectedNodeId;
                const isUnavailable = !entry;

                return (
                  <div
                    key={node.id}
                    className={`node-card ${isSelected ? 'selected' : ''} ${
                      isUnavailable ? 'unavailable' : ''
                    }`}
                    onClick={() => setSelectedNodeId(node.id)}
                  >
                    <div className="node-header">
                      <strong>{node.title || node.id}</strong>
                      <button
                        type="button"
                        className="btn-close"
                        disabled={disabled}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveNode(node.id);
                        }}
                      >
                        ×
                      </button>
                    </div>
                    {isUnavailable ? (
                      <div className="unavailable-badge">
                        <span className="pill warn">Unavailable Plugin</span>
                        <small>{node.plugin_ref}</small>
                      </div>
                    ) : (
                      <div className="node-details">
                        <span className="pill info">{entry.kind}</span>
                        <small>{entry.ref}</small>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          <div className="edges-section">
            <h4>Connections ({document.spec.edges.length})</h4>
            <ul className="edges-list">
              {document.spec.edges.map((edge, idx) => (
                <li key={`${edge.source.node_id}-${edge.target.node_id}-${idx}`}>
                  <span>
                    {edge.source.node_id}.{edge.source.port_key} →{' '}
                    {edge.target.node_id}.{edge.target.port_key}
                  </span>
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => handleRemoveEdge(idx)}
                  >
                    Disconnect
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="node-inspector">
          {selectedNode ? (
            <div>
              <h3>Node Inspector: {selectedNode.id}</h3>
              {(() => {
                const entry = getCatalogEntry(selectedNode.plugin_ref);
                if (!entry) {
                  return (
                    <div className="lossless-placeholder-view">
                      <div className="pill warn">Unknown / Unavailable Plugin</div>
                      <p>
                        Plugin <code>{selectedNode.plugin_ref}</code> is not installed in the
                        active catalog. Its parameters and edges are preserved losslessly.
                      </p>
                      <pre className="code-block">
                        {JSON.stringify(selectedNode.parameters, null, 2)}
                      </pre>
                    </div>
                  );
                }

                const op = entry.operations.find(
                  (o) => o.operation_id === selectedNode.operation_id,
                ) || entry.operations[0];

                if (!op || op.parameters.length === 0) {
                  return <p>This operation has no configurable parameters.</p>;
                }

                return (
                  <ParameterForm
                    parameters={op.parameters}
                    values={selectedNode.parameters}
                    disabled={disabled}
                    onChange={(newParams) =>
                      handleParametersChange(selectedNode.id, newParams)
                    }
                  />
                );
              })()}
            </div>
          ) : (
            <div className="inspector-placeholder">
              Select a node to inspect and configure parameters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
