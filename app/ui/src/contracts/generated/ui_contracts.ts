/**
 * Generated TypeScript definitions mirroring app/contracts/ui/models.py.
 * Do not manually modify semantic shapes without updating authoritative contracts.
 */

export type CapabilityPresentationState =
  | "loading"
  | "unavailable"
  | "incompatible"
  | "disabled"
  | "degraded"
  | "unauthorized"
  | "ready";

export interface UiFeatureDescriptor {
  readonly featureId: string;
  readonly name: string;
  readonly description: string;
  readonly requiredCapabilities?: readonly string[];
  readonly optionalCapabilities?: readonly string[];
}

export interface RouteTarget {
  readonly path: string;
  readonly workspaceId: string;
  readonly title: string;
  readonly icon?: string;
  readonly requiredPermission?: string;
}

export interface NavigationContribution {
  readonly id: string;
  readonly label: string;
  readonly route: RouteTarget;
  readonly order?: number;
  readonly parentId?: string;
  readonly badge?: string;
}

export interface UiCommandDescriptor {
  readonly commandId: string;
  readonly title: string;
  readonly category: string;
  readonly shortcut?: string;
  readonly enabled?: boolean;
}

export interface KeyboardBinding {
  readonly keyCombination: string;
  readonly commandId: string;
  readonly description: string;
  readonly scope?: string;
}

export interface ViewProjection {
  readonly viewId: string;
  readonly title: string;
  readonly dataSource: string;
  readonly parameters?: Readonly<Record<string, unknown>>;
}

export interface FieldDescriptor {
  readonly fieldName: string;
  readonly label: string;
  readonly fieldType: string;
  readonly required?: boolean;
  readonly defaultValue?: unknown;
  readonly constraints?: Readonly<Record<string, unknown>>;
}

export interface ClientSelection {
  readonly selectionId: string;
  readonly selectedKeys?: readonly string[];
  readonly isAllSelected?: boolean;
}

export interface ClientPageState {
  readonly pageIndex: number;
  readonly pageSize: number;
  readonly sortColumn?: string;
  readonly sortAscending?: boolean;
  readonly totalCount?: number;
}

export interface ChartAlternative {
  readonly chartId: string;
  readonly title: string;
  readonly summaryText: string;
  readonly tableData?: ReadonlyArray<Readonly<Record<string, unknown>>>;
}

export interface DraftEnvelope {
  readonly draftId: string;
  readonly schemaId: string;
  readonly workspaceId: string;
  readonly actorId: string;
  readonly entityVersion: number;
  readonly payload: Readonly<Record<string, unknown>>;
  readonly createdAtIso: string;
  readonly updatedAtIso: string;
}

export interface DraftConflict {
  readonly draftId: string;
  readonly baseVersion: number;
  readonly currentVersion: number;
  readonly conflictingFields?: readonly string[];
}

export interface ConfirmationPlan {
  readonly actionId: string;
  readonly targetDescription: string;
  readonly impactSummary: string;
  readonly affectedCount: number;
  readonly isReversible: boolean;
  readonly confirmationHash: string;
}

export interface UiNotification {
  readonly notificationId: string;
  readonly title: string;
  readonly message: string;
  readonly severity?: "info" | "success" | "warning" | "error";
  readonly timestampIso?: string;
  readonly owningTaskId?: string;
}

export interface ProgressPresentation {
  readonly taskId: string;
  readonly stageName: string;
  readonly progressPercent?: number;
  readonly isIndeterminate?: boolean;
  readonly message?: string;
}

export interface ErrorPresentation {
  readonly errorCode: string;
  readonly title: string;
  readonly detail: string;
  readonly causalReference?: string;
  readonly isRetryable?: boolean;
  readonly suggestedAction?: string;
}

export interface PanelContribution {
  readonly panelId: string;
  readonly title: string;
  readonly region: string;
  readonly isClosable?: boolean;
}

export interface TabContribution {
  readonly tabId: string;
  readonly title: string;
  readonly contentViewId: string;
  readonly isDirty?: boolean;
}

export interface LayoutSnapshot {
  readonly layoutId: string;
  readonly workspaceId: string;
  readonly activePanels?: readonly PanelContribution[];
  readonly openTabs?: readonly TabContribution[];
  readonly version?: number;
}

export interface ViewPreference {
  readonly theme?: "system" | "light" | "dark";
  readonly density?: "compact" | "comfortable";
  readonly fontScale?: number;
  readonly locale?: string;
}

export interface AccessibilityPreference {
  readonly highContrast?: boolean;
  readonly reducedMotion?: boolean;
  readonly screenReaderOptimized?: boolean;
}

export interface WorkspaceRoute {
  readonly workspaceId: string;
  readonly routePath: string;
  readonly displayName: string;
  readonly iconName?: string;
  readonly requiredCapabilities?: readonly string[];
  readonly isAuthorized?: boolean;
  readonly renderWorkspace?: () => React.ReactNode;
}

export interface ShellSnapshot {
  readonly activeWorkspaceId: string | null;
  readonly currentRoute: string;
  readonly availableWorkspaces: readonly WorkspaceRoute[];
  readonly capabilityStates: Readonly<Record<string, CapabilityPresentationState>>;
  readonly isReady: boolean;
  readonly statusMessage: string;
}
