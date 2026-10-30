import { useState, useMemo } from 'react';
import {
  DATABANK_METRIC_COLUMNS,
  type ColumnDefinition,
  type DatabankView,
  type MetricCategory,
} from '../ProjectDatabanks/databankColumns';
import { useDatabankViewsService } from './DatabankViewsService';

export function useDatabankViewsDialog() {
  const {
    views,
    activeViewId,
    setActiveView,
    addView,
    updateView,
    deleteView,
    cloneView,
    resetViews,
  } = useDatabankViewsService();

  const [selectedViewId, setSelectedViewId] = useState<string>(activeViewId);
  const [newViewName, setNewViewName] = useState('');
  const [cloneViewName, setCloneViewName] = useState('');
  const [showAddColumns, setShowAddColumns] = useState(false);
  const [colSearch, setColSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState<MetricCategory | 'All'>('All');
  const [selectedPropsCol, setSelectedPropsCol] = useState<ColumnDefinition | null>(null);

  const activeView = useMemo(() => {
    return views.find(v => v.id === selectedViewId) || views[0];
  }, [views, selectedViewId]);

  const [editedColumns, setEditedColumns] = useState(activeView.columns);
  const [isDirty, setIsDirty] = useState(false);

  // Sync edited columns when selected view changes
  const handleSelectView = (viewId: string) => {
    setSelectedViewId(viewId);
    const v = views.find(item => item.id === viewId) || views[0];
    setEditedColumns([...v.columns]);
    setIsDirty(false);
  };

  const metricMap = useMemo(() => {
    const map = new Map<string, ColumnDefinition>();
    for (const col of DATABANK_METRIC_COLUMNS) {
      map.set(col.id, col);
    }
    return map;
  }, []);

  const moveColumn = (index: number, direction: 'up' | 'down') => {
    const targetIdx = direction === 'up' ? index - 1 : index + 1;
    if (targetIdx < 0 || targetIdx >= editedColumns.length) return;
    const updated = [...editedColumns];
    const temp = updated[index];
    updated[index] = updated[targetIdx];
    updated[targetIdx] = temp;
    setEditedColumns(updated);
    setIsDirty(true);
  };

  const removeColumn = (index: number) => {
    const updated = editedColumns.filter((_, i) => i !== index);
    setEditedColumns(updated);
    setIsDirty(true);
  };

  const handleCreateView = () => {
    if (!newViewName.trim()) return;
    const newView: DatabankView = {
      id: `view-${Date.now()}`,
      name: newViewName.trim(),
      isDefault: false,
      columns: [
        { columnId: 'name', width: 180 },
        { columnId: 'symbol', width: 85 },
        { columnId: 'netProfit', width: 100 },
        { columnId: 'profitFactor', width: 90 },
        { columnId: 'drawdown', width: 90 },
      ],
    };
    addView(newView);
    setSelectedViewId(newView.id);
    setEditedColumns(newView.columns);
    setNewViewName('');
    setIsDirty(false);
  };

  const handleCloneView = () => {
    if (!cloneViewName.trim()) return;
    const cloned = cloneView(selectedViewId, cloneViewName.trim());
    setSelectedViewId(cloned.id);
    setEditedColumns(cloned.columns);
    setCloneViewName('');
    setIsDirty(false);
  };

  const handleSave = () => {
    if (activeView.isDefault) return;
    updateView({
      ...activeView,
      columns: editedColumns,
    });
    setIsDirty(false);
  };

  const handleDelete = () => {
    if (activeView.isDefault) return;
    deleteView(activeView.id);
    const remaining = views.filter(v => v.id !== activeView.id);
    if (remaining.length > 0) {
      handleSelectView(remaining[0].id);
    }
  };

  const handleAddColumn = (columnId: string) => {
    if (editedColumns.some(c => c.columnId === columnId)) return;
    const metric = metricMap.get(columnId);
    const updated = [
      ...editedColumns,
      { columnId, width: metric?.defaultWidth || 90 },
    ];
    setEditedColumns(updated);
    setIsDirty(true);
  };

  const filteredMetrics = useMemo(() => {
    return DATABANK_METRIC_COLUMNS.filter(m => {
      const matchCat = selectedCat === 'All' || m.category === selectedCat;
      const matchSearch =
        colSearch.trim() === '' ||
        m.name.toLowerCase().includes(colSearch.toLowerCase()) ||
        m.id.toLowerCase().includes(colSearch.toLowerCase()) ||
        m.description.toLowerCase().includes(colSearch.toLowerCase());
      return matchCat && matchSearch;
    });
  }, [selectedCat, colSearch]);

  return { views, setActiveView, resetViews, selectedViewId, newViewName, setNewViewName, cloneViewName, setCloneViewName, showAddColumns, setShowAddColumns, colSearch, setColSearch, selectedCat, setSelectedCat, selectedPropsCol, setSelectedPropsCol, activeView, editedColumns, setEditedColumns, isDirty, setIsDirty, handleSelectView, metricMap, moveColumn, removeColumn, handleCreateView, handleCloneView, handleSave, handleDelete, handleAddColumn, filteredMetrics };
}
