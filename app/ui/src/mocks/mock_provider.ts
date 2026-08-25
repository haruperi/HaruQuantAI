/**
 * Dev-Only Mock Capability Provider for HaruQuantAI D-UI.
 *
 * Supplies mock capability data conforming strictly to ratified wire schemas.
 * Gated to development environments; excluded from production releases.
 */

import type { IUiPresentationClient } from "../clients/ui_client";
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
import {
  MOCK_ADMINISTER_SYSTEM_SUCCESS,
  MOCK_AUTHOR_STRATEGIES_SUCCESS,
  MOCK_COMPOSE_PORTFOLIOS_SUCCESS,
  MOCK_EDIT_CODE_SUCCESS,
  MOCK_EDIT_INPUTS_SUCCESS,
  MOCK_EDIT_PROJECTS_SUCCESS,
  MOCK_ENSURE_ACCESS_SUCCESS,
  MOCK_EXPLORE_RESULTS_SUCCESS,
  MOCK_EXTEND_VIEWS_SUCCESS,
  MOCK_MANAGE_DATA_SUCCESS,
  MOCK_MANAGE_LAYOUTS_SUCCESS,
  MOCK_MONITOR_WORK_SUCCESS,
  MOCK_OPERATE_DATABANKS_SUCCESS,
  MOCK_OPERATE_TRADING_SUCCESS,
  MOCK_RUN_RESEARCH_SUCCESS,
  MOCK_START_WORK_SUCCESS,
} from "./fixtures";

export class MockUiPresentationProvider implements IUiPresentationClient {
  public readonly isDevOnly = true;

  async startWork(_req: StartWorkPresentationRequest): Promise<StartWorkPresentationSuccess> {
    return MOCK_START_WORK_SUCCESS;
  }

  async manageLayouts(_req: ManageLayoutsPresentationRequest): Promise<ManageLayoutsPresentationSuccess> {
    return MOCK_MANAGE_LAYOUTS_SUCCESS;
  }

  async editInputs(_req: EditInputsPresentationRequest): Promise<EditInputsPresentationSuccess> {
    return MOCK_EDIT_INPUTS_SUCCESS;
  }

  async authorStrategies(_req: AuthorStrategiesPresentationRequest): Promise<AuthorStrategiesPresentationSuccess> {
    return MOCK_AUTHOR_STRATEGIES_SUCCESS;
  }

  async runResearch(_req: RunResearchPresentationRequest): Promise<RunResearchPresentationSuccess> {
    return MOCK_RUN_RESEARCH_SUCCESS;
  }

  async editProjects(_req: EditProjectsPresentationRequest): Promise<EditProjectsPresentationSuccess> {
    return MOCK_EDIT_PROJECTS_SUCCESS;
  }

  async manageData(_req: ManageDataPresentationRequest): Promise<ManageDataPresentationSuccess> {
    return MOCK_MANAGE_DATA_SUCCESS;
  }

  async operateDatabanks(_req: OperateDatabanksPresentationRequest): Promise<OperateDatabanksPresentationSuccess> {
    return MOCK_OPERATE_DATABANKS_SUCCESS;
  }

  async exploreResults(_req: ExploreResultsPresentationRequest): Promise<ExploreResultsPresentationSuccess> {
    return MOCK_EXPLORE_RESULTS_SUCCESS;
  }

  async composePortfolios(_req: ComposePortfoliosPresentationRequest): Promise<ComposePortfoliosPresentationSuccess> {
    return MOCK_COMPOSE_PORTFOLIOS_SUCCESS;
  }

  async editCode(_req: EditCodePresentationRequest): Promise<EditCodePresentationSuccess> {
    return MOCK_EDIT_CODE_SUCCESS;
  }

  async monitorWork(_req: MonitorWorkPresentationRequest): Promise<MonitorWorkPresentationSuccess> {
    return MOCK_MONITOR_WORK_SUCCESS;
  }

  async administerSystem(_req: AdministerSystemPresentationRequest): Promise<AdministerSystemPresentationSuccess> {
    return MOCK_ADMINISTER_SYSTEM_SUCCESS;
  }

  async operateTrading(_req: OperateTradingPresentationRequest): Promise<OperateTradingPresentationSuccess> {
    return MOCK_OPERATE_TRADING_SUCCESS;
  }

  async ensureAccess(_req: EnsureAccessPresentationRequest): Promise<EnsureAccessPresentationSuccess> {
    return MOCK_ENSURE_ACCESS_SUCCESS;
  }

  async extendViews(_req: ExtendViewsPresentationRequest): Promise<ExtendViewsPresentationSuccess> {
    return MOCK_EXTEND_VIEWS_SUCCESS;
  }
}
