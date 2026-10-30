import React, { useState } from 'react';
import { MarketplaceLocale } from './locale';

export interface InstallState {
  title: string;
  status: 'downloading' | 'verifying' | 'installing';
  progress?: number;
}

export interface SkippedFile {
  name: string;
  reason?: string;
}

export interface InstallResult {
  title: string;
  installDir: string;
  installedFiles: string[];
  skippedFiles: SkippedFile[];
  restartRequired: boolean;
}

export interface ShareTreeNodeItem {
  id: number;
  text: string;
  isDir?: boolean;
  userdata?: { name: string; content: string }[];
  item?: ShareTreeNodeItem[];
}

export interface MarketplaceWorkspaceProps {
  initialLocale?: string | null;
  baseIframeUrl?: string;
  installState?: InstallState | null;
  installResult?: InstallResult | null;
  uninstallTarget?: string | null;
  isShareOpen?: boolean;
  isUpdate?: boolean;
  shareTree?: ShareTreeNodeItem[];
  excludedDirs?: string[];
  onCloseInstallResult?: () => void;
  onConfirmUninstall?: (slug: string) => void;
  onCancelUninstall?: () => void;
  onCloseShare?: () => void;
  onSubmitShare?: (form: ShareFormData) => void;
}

export interface ShareFormData {
  title: string;
  description: string;
  details: string;
  categoryId: string;
  version: string;
  author: string;
  selectedFiles: string[];
}

export const MarketplaceWorkspace: React.FC<MarketplaceWorkspaceProps> = ({
  initialLocale = null,
  baseIframeUrl = '../MARKETPLACE/index.html',
  installState = null,
  installResult = null,
  uninstallTarget = null,
  isShareOpen = false,
  isUpdate = false,
  shareTree = [],
  excludedDirs = ['settings', 'log', 'logs', 'data', 'temp', 'cache'],
  onCloseInstallResult,
  onConfirmUninstall,
  onCancelUninstall,
  onCloseShare,
  onSubmitShare,
}) => {
  const normalizedLocale = MarketplaceLocale.from_flag(initialLocale);
  const iframeSrc = `${baseIframeUrl}?lang=${encodeURIComponent(normalizedLocale)}`;

  // Share form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [details, setDetails] = useState('');
  const [categoryId, setCategoryId] = useState('indicators');
  const [version, setVersion] = useState('1.0.0');
  const [author, setAuthor] = useState('');
  const [treeFilter, setTreeFilter] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);

  const handleToggleFile = (fileText: string) => {
    setSelectedFiles((prev) =>
      prev.includes(fileText)
        ? prev.filter((f) => f !== fileText)
        : [...prev, fileText],
    );
  };

  const handleShareSubmit = () => {
    if (onSubmitShare) {
      onSubmitShare({
        title,
        description,
        details,
        categoryId,
        version,
        author,
        selectedFiles,
      });
    }
  };

  // Filter tree nodes
  const filterNodes = (nodes: ShareTreeNodeItem[]): ShareTreeNodeItem[] => {
    if (!treeFilter.trim()) return nodes;
    const filterLower = treeFilter.trim().toLowerCase();
    return nodes
      .map((node) => {
        if (node.item && node.item.length > 0) {
          const matchingChildren = filterNodes(node.item);
          if (matchingChildren.length > 0 || node.text.toLowerCase().includes(filterLower)) {
            return { ...node, item: matchingChildren };
          }
          return null;
        }
        return node.text.toLowerCase().includes(filterLower) ? node : null;
      })
      .filter((n): n is ShareTreeNodeItem => n !== null);
  };

  const filteredTree = filterNodes(shareTree);

  return (
    <div
      className="sqx-app-marketplace"
      data-testid="marketplace-workspace"
      style={{ width: '100%', height: '100%', position: 'relative' }}
    >
      {/* Primary Marketplace IFrame */}
      <iframe
        id="marketplace-iframe"
        data-testid="marketplace-iframe"
        src={iframeSrc}
        title="SQX Marketplace"
        style={{ width: '100%', height: '100%', border: 'none' }}
      />

      {/* Install Overlay */}
      {installState && (
        <div
          className="marketplace-install-overlay"
          data-testid="marketplace-install-overlay"
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.65)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1050,
          }}
        >
          <div
            className="marketplace-install-box"
            style={{
              background: '#222',
              color: '#fff',
              padding: 24,
              borderRadius: 8,
              minWidth: 320,
              textAlign: 'center',
            }}
          >
            <div className="marketplace-install-spinner" style={{ marginBottom: 12 }}>
              <i className="fa fa-circle-o-notch fa-spin fa-2x" />
            </div>
            <h4 className="marketplace-install-title">Installing</h4>
            <div
              className="marketplace-install-name"
              data-testid="marketplace-install-name"
              style={{ fontWeight: 'bold', margin: '8px 0' }}
            >
              {installState.title}
            </div>

            <div
              className="marketplace-install-bar"
              style={{
                background: '#444',
                height: 10,
                borderRadius: 5,
                overflow: 'hidden',
                margin: '12px 0',
              }}
            >
              <div
                className={`marketplace-install-bar-fill ${
                  installState.status !== 'downloading' ? 'indeterminate' : ''
                }`}
                data-testid="marketplace-install-progress-bar"
                style={{
                  background: '#0284c7',
                  height: '100%',
                  width:
                    installState.status === 'downloading'
                      ? `${installState.progress ?? 0}%`
                      : '100%',
                  transition: 'width 0.2s',
                }}
              />
            </div>

            <div className="marketplace-install-step" data-testid="marketplace-install-step">
              {installState.status === 'downloading' && (
                <span>{`Downloading… ${installState.progress ?? 0}%`}</span>
              )}
              {installState.status === 'verifying' && (
                <span>Verifying package&hellip;</span>
              )}
              {installState.status === 'installing' && (
                <span>Installing files&hellip;</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Install Result Modal */}
      {installResult && (
        <div
          className="modal fade in not-resize"
          id="marketplaceInstallResultPopup"
          role="dialog"
          data-testid="marketplace-install-result-popup"
          style={{
            display: 'block',
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 1060,
          }}
        >
          <div
            className="modal-dialog"
            style={{
              margin: '60px auto',
              maxWidth: 500,
              background: '#fff',
              borderRadius: 6,
              overflow: 'hidden',
            }}
          >
            <div className="modal-content" style={{ padding: 20 }}>
              <div
                className="modal-header"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid #eee',
                  paddingBottom: 10,
                }}
              >
                <h4 className="modal-title" style={{ margin: 0 }}>
                  <i
                    className="fa fa-check-circle marketplace-install-result-ok"
                    style={{ color: '#16a34a', marginRight: 8 }}
                  />
                  <span>Installation complete</span>
                </h4>
                <button
                  type="button"
                  className="close"
                  onClick={onCloseInstallResult}
                  aria-label="Close"
                  data-testid="marketplace-install-result-close"
                  style={{ background: 'none', border: 'none', fontSize: 20 }}
                >
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>

              <div
                className="modal-body marketplace-install-result-body"
                style={{ padding: '16px 0' }}
              >
                <div className="marketplace-install-result-msg" style={{ marginBottom: 12 }}>
                  <strong>{installResult.title}</strong> was installed successfully.
                </div>

                {installResult.installDir && (
                  <div className="marketplace-install-result-loc" style={{ marginBottom: 12 }}>
                    <span className="marketplace-install-result-label">Unpacked into </span>
                    <code data-testid="marketplace-install-result-dir">
                      {installResult.installDir}
                    </code>
                  </div>
                )}

                {installResult.installedFiles.length > 0 && (
                  <div className="marketplace-install-result-section" style={{ marginBottom: 12 }}>
                    <div className="marketplace-install-result-label">
                      <span>Installed files</span>{' '}
                      <span className="marketplace-install-result-count">
                        ({installResult.installedFiles.length})
                      </span>
                    </div>
                    <ul
                      className="marketplace-install-result-list"
                      data-testid="marketplace-install-result-files"
                      style={{ maxHeight: 120, overflowY: 'auto', paddingLeft: 20 }}
                    >
                      {installResult.installedFiles.map((f, idx) => (
                        <li key={idx}>
                          <i className="fa fa-file-o" /> {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {installResult.skippedFiles.length > 0 && (
                  <div
                    className="marketplace-install-result-section marketplace-install-result-skipped"
                    style={{ marginBottom: 12 }}
                  >
                    <div className="marketplace-install-result-label">
                      <span>Skipped</span>{' '}
                      <span className="marketplace-install-result-count">
                        ({installResult.skippedFiles.length})
                      </span>
                    </div>
                    <ul
                      className="marketplace-install-result-list"
                      data-testid="marketplace-install-result-skipped"
                      style={{ maxHeight: 100, overflowY: 'auto', paddingLeft: 20 }}
                    >
                      {installResult.skippedFiles.map((s, idx) => (
                        <li key={idx}>
                          <i className="fa fa-ban" /> {s.name}{' '}
                          {s.reason && (
                            <span className="marketplace-install-result-reason">
                              &mdash; {s.reason}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {installResult.restartRequired && (
                  <div
                    className="marketplace-install-result-restart"
                    data-testid="marketplace-install-result-restart"
                    style={{ color: '#d97706', marginTop: 10 }}
                  >
                    <i className="fa fa-exclamation-triangle" style={{ marginRight: 6 }} />
                    <span>Restart StrategyQuant X to activate the installed plugin.</span>
                  </div>
                )}
              </div>

              <div
                className="modal-footer"
                style={{ textAlign: 'right', borderTop: '1px solid #eee', paddingTop: 10 }}
              >
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={onCloseInstallResult}
                  data-testid="marketplace-install-result-ok"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Uninstall Confirmation Modal */}
      {uninstallTarget && (
        <div
          className="modal fade in not-resize"
          id="marketplaceUninstallConfirmPopup"
          role="dialog"
          data-testid="marketplace-uninstall-confirm-popup"
          style={{
            display: 'block',
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 1060,
          }}
        >
          <div
            className="modal-dialog"
            style={{
              margin: '80px auto',
              maxWidth: 420,
              background: '#fff',
              borderRadius: 6,
              overflow: 'hidden',
            }}
          >
            <div className="modal-content" style={{ padding: 20 }}>
              <div
                className="modal-header"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid #eee',
                  paddingBottom: 10,
                }}
              >
                <h4 className="modal-title" style={{ margin: 0 }}>
                  Uninstall extension
                </h4>
                <button
                  type="button"
                  className="close"
                  onClick={onCancelUninstall}
                  aria-label="Close"
                  data-testid="marketplace-uninstall-confirm-close"
                  style={{ background: 'none', border: 'none', fontSize: 20 }}
                >
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>
              <div
                className="modal-body marketplace-uninstall-confirm-body"
                style={{ padding: '16px 0' }}
              >
                <div className="marketplace-uninstall-confirm-lead">
                  Are you sure you want to uninstall this extension?
                </div>
              </div>
              <div
                className="modal-footer"
                style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  gap: 8,
                  borderTop: '1px solid #eee',
                  paddingTop: 10,
                }}
              >
                <button
                  type="button"
                  className="btn btn-default"
                  onClick={onCancelUninstall}
                  data-testid="marketplace-uninstall-confirm-cancel"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-danger btn-delete"
                  onClick={() => onConfirmUninstall && onConfirmUninstall(uninstallTarget)}
                  data-testid="marketplace-uninstall-confirm-ok"
                >
                  Uninstall
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Share Product Modal */}
      {isShareOpen && (
        <div
          className="modal fade in not-resize"
          id="marketplaceSharePopup"
          role="dialog"
          data-testid="marketplace-share-popup"
          style={{
            display: 'block',
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 1060,
          }}
        >
          <div
            className="modal-dialog"
            style={{
              margin: '40px auto',
              maxWidth: 700,
              background: '#fff',
              borderRadius: 6,
              overflow: 'hidden',
            }}
          >
            <div className="modal-content" style={{ padding: 20 }}>
              <div
                className="modal-header"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid #eee',
                  paddingBottom: 10,
                }}
              >
                <h4 className="modal-title" style={{ margin: 0 }}>
                  {isUpdate ? 'Update product' : 'Share a product'}
                </h4>
                <button
                  type="button"
                  className="close"
                  onClick={onCloseShare}
                  aria-label="Close"
                  data-testid="marketplace-share-close"
                  style={{ background: 'none', border: 'none', fontSize: 20 }}
                >
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>

              <div
                className="modal-body marketplace-share-body"
                style={{
                  padding: '16px 0',
                  display: 'flex',
                  flexDirection: 'row',
                  gap: 16,
                }}
              >
                {/* Left column: form details */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <div>
                    <label htmlFor="mpShareTitle">Title *</label>
                    <input
                      id="mpShareTitle"
                      type="text"
                      className="form-control"
                      data-testid="marketplace-share-title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div>
                    <label htmlFor="mpShareDescription">Description *</label>
                    <textarea
                      id="mpShareDescription"
                      className="form-control"
                      rows={2}
                      data-testid="marketplace-share-description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div>
                    <label htmlFor="mpShareDetails">Detailed description</label>
                    <textarea
                      id="mpShareDetails"
                      data-testid="marketplace-share-details"
                      value={details}
                      onChange={(e) => setDetails(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div>
                    <label htmlFor="mpShareCategory">Category *</label>
                    <select
                      id="mpShareCategory"
                      className="form-control"
                      data-testid="marketplace-share-category"
                      value={categoryId}
                      onChange={(e) => setCategoryId(e.target.value)}
                      style={{ width: '100%' }}
                    >
                      <option value="indicators">Indicators</option>
                      <option value="snippets">Snippets</option>
                      <option value="strategies">Strategies</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="mpShareVersion">Version</label>
                    <input
                      id="mpShareVersion"
                      type="text"
                      className="form-control"
                      data-testid="marketplace-share-version"
                      value={version}
                      onChange={(e) => setVersion(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div>
                    <label htmlFor="mpShareAuthor">Author</label>
                    <input
                      id="mpShareAuthor"
                      type="text"
                      className="form-control"
                      data-testid="marketplace-share-author"
                      value={author}
                      onChange={(e) => setAuthor(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>

                {/* Right column: shareable files tree */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <label>Files to share</label>
                  <input
                    type="text"
                    className="form-control marketplace-share-filter"
                    placeholder="Filter files..."
                    data-testid="marketplace-share-filter"
                    value={treeFilter}
                    onChange={(e) => setTreeFilter(e.target.value)}
                    style={{ width: '100%' }}
                  />
                  <div
                    className="marketplace-share-tree"
                    data-testid="marketplace-share-tree"
                    style={{
                      border: '1px solid #ccc',
                      borderRadius: 4,
                      padding: 8,
                      maxHeight: 220,
                      overflowY: 'auto',
                    }}
                  >
                    {filteredTree.map((node) => (
                      <div key={node.id} style={{ marginBottom: 4 }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <input
                            type="checkbox"
                            checked={selectedFiles.includes(node.text)}
                            onChange={() => handleToggleFile(node.text)}
                          />
                          <i className={node.isDir ? 'fa fa-folder-o' : 'fa fa-file-o'} />
                          {node.text}
                        </label>
                        {node.item && (
                          <div style={{ paddingLeft: 16 }}>
                            {node.item.map((child) => (
                              <label
                                key={child.id}
                                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                              >
                                <input
                                  type="checkbox"
                                  checked={selectedFiles.includes(child.text)}
                                  onChange={() => handleToggleFile(child.text)}
                                />
                                <i className="fa fa-file-o" />
                                {child.text}
                              </label>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                    {filteredTree.length === 0 && (
                      <div className="marketplace-share-tree-empty" style={{ color: '#888' }}>
                        No shareable files found.
                      </div>
                    )}
                  </div>

                  {excludedDirs.length > 0 && (
                    <div
                      className="marketplace-share-hint"
                      data-testid="marketplace-share-excluded"
                      style={{ fontSize: '0.85em', color: '#666' }}
                    >
                      <span>Hidden system folders: </span>
                      {excludedDirs.join(', ')}
                    </div>
                  )}
                </div>
              </div>

              <div
                className="modal-footer"
                style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  gap: 8,
                  borderTop: '1px solid #eee',
                  paddingTop: 10,
                }}
              >
                <button
                  type="button"
                  className="btn btn-default"
                  onClick={onCloseShare}
                  data-testid="marketplace-share-cancel"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleShareSubmit}
                  data-testid="marketplace-share-submit"
                >
                  Submit
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
