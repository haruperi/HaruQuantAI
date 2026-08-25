/**
 * Generated-Contract UI Client Boundary for HaruQuantAI D-UI.
 *
 * Implements strongly-typed presentation client calls over generated contracts
 * without hand-written wire schema mirrors.
 */

import type {
  AdministerSystemPresentationRequest,
  AdministerSystemPresentationSuccess,
  AuthorStrategiesPresentationRequest,
  AuthorStrategiesPresentationSuccess,
  ComposePortfoliosPresentationRequest,
  ComposePortfoliosPresentationSuccess,
  EditCodePresentationRequest,
  EditCodePresentationSuccess,
  EditInputsPresentationRequest,
  EditInputsPresentationSuccess,
  EditProjectsPresentationRequest,
  EditProjectsPresentationSuccess,
  EnsureAccessPresentationRequest,
  EnsureAccessPresentationSuccess,
  ExploreResultsPresentationRequest,
  ExploreResultsPresentationSuccess,
  ExtendViewsPresentationRequest,
  ExtendViewsPresentationSuccess,
  ManageDataPresentationRequest,
  ManageDataPresentationSuccess,
  ManageLayoutsPresentationRequest,
  ManageLayoutsPresentationSuccess,
  MonitorWorkPresentationRequest,
  MonitorWorkPresentationSuccess,
  OperateDatabanksPresentationRequest,
  OperateDatabanksPresentationSuccess,
  OperateTradingPresentationRequest,
  OperateTradingPresentationSuccess,
  RunResearchPresentationRequest,
  RunResearchPresentationSuccess,
  StartWorkPresentationRequest,
  StartWorkPresentationSuccess,
} from "../contracts/generated/ui";

export interface IUiPresentationClient {
  startWork(req: StartWorkPresentationRequest): Promise<StartWorkPresentationSuccess>;
  manageLayouts(req: ManageLayoutsPresentationRequest): Promise<ManageLayoutsPresentationSuccess>;
  editInputs(req: EditInputsPresentationRequest): Promise<EditInputsPresentationSuccess>;
  authorStrategies(req: AuthorStrategiesPresentationRequest): Promise<AuthorStrategiesPresentationSuccess>;
  runResearch(req: RunResearchPresentationRequest): Promise<RunResearchPresentationSuccess>;
  editProjects(req: EditProjectsPresentationRequest): Promise<EditProjectsPresentationSuccess>;
  manageData(req: ManageDataPresentationRequest): Promise<ManageDataPresentationSuccess>;
  operateDatabanks(req: OperateDatabanksPresentationRequest): Promise<OperateDatabanksPresentationSuccess>;
  exploreResults(req: ExploreResultsPresentationRequest): Promise<ExploreResultsPresentationSuccess>;
  composePortfolios(req: ComposePortfoliosPresentationRequest): Promise<ComposePortfoliosPresentationSuccess>;
  editCode(req: EditCodePresentationRequest): Promise<EditCodePresentationSuccess>;
  monitorWork(req: MonitorWorkPresentationRequest): Promise<MonitorWorkPresentationSuccess>;
  administerSystem(req: AdministerSystemPresentationRequest): Promise<AdministerSystemPresentationSuccess>;
  operateTrading(req: OperateTradingPresentationRequest): Promise<OperateTradingPresentationSuccess>;
  ensureAccess(req: EnsureAccessPresentationRequest): Promise<EnsureAccessPresentationSuccess>;
  extendViews(req: ExtendViewsPresentationRequest): Promise<ExtendViewsPresentationSuccess>;
}

export class HttpUiPresentationClient implements IUiPresentationClient {
  constructor(private readonly baseUrl: string = "/api/v1/ui") {}

  private async post<TReq, TRes>(path: string, request: TReq): Promise<TRes> {
    const res = await fetch(`${this.baseUrl}/${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      throw new Error(`UI presentation API request failed with status ${res.status}: ${res.statusText}`);
    }

    return (await res.json()) as TRes;
  }

  startWork(req: StartWorkPresentationRequest): Promise<StartWorkPresentationSuccess> {
    return this.post("start-work", req);
  }

  manageLayouts(req: ManageLayoutsPresentationRequest): Promise<ManageLayoutsPresentationSuccess> {
    return this.post("manage-layouts", req);
  }

  editInputs(req: EditInputsPresentationRequest): Promise<EditInputsPresentationSuccess> {
    return this.post("edit-inputs", req);
  }

  authorStrategies(req: AuthorStrategiesPresentationRequest): Promise<AuthorStrategiesPresentationSuccess> {
    return this.post("author-strategies", req);
  }

  runResearch(req: RunResearchPresentationRequest): Promise<RunResearchPresentationSuccess> {
    return this.post("run-research", req);
  }

  editProjects(req: EditProjectsPresentationRequest): Promise<EditProjectsPresentationSuccess> {
    return this.post("edit-projects", req);
  }

  manageData(req: ManageDataPresentationRequest): Promise<ManageDataPresentationSuccess> {
    return this.post("manage-data", req);
  }

  operateDatabanks(req: OperateDatabanksPresentationRequest): Promise<OperateDatabanksPresentationSuccess> {
    return this.post("operate-databanks", req);
  }

  exploreResults(req: ExploreResultsPresentationRequest): Promise<ExploreResultsPresentationSuccess> {
    return this.post("explore-results", req);
  }

  composePortfolios(req: ComposePortfoliosPresentationRequest): Promise<ComposePortfoliosPresentationSuccess> {
    return this.post("compose-portfolios", req);
  }

  editCode(req: EditCodePresentationRequest): Promise<EditCodePresentationSuccess> {
    return this.post("edit-code", req);
  }

  monitorWork(req: MonitorWorkPresentationRequest): Promise<MonitorWorkPresentationSuccess> {
    return this.post("monitor-work", req);
  }

  administerSystem(req: AdministerSystemPresentationRequest): Promise<AdministerSystemPresentationSuccess> {
    return this.post("administer-system", req);
  }

  operateTrading(req: OperateTradingPresentationRequest): Promise<OperateTradingPresentationSuccess> {
    return this.post("operate-trading", req);
  }

  ensureAccess(req: EnsureAccessPresentationRequest): Promise<EnsureAccessPresentationSuccess> {
    return this.post("ensure-access", req);
  }

  extendViews(req: ExtendViewsPresentationRequest): Promise<ExtendViewsPresentationSuccess> {
    return this.post("extend-views", req);
  }
}
