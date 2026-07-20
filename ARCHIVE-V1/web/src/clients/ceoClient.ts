"use client"

export {
  archiveAiChatThread as archiveCeoConversation,
  createAiChatMessage as createCeoConversationMessage,
  createAiChatThread as createCeoConversation,
  deleteAiChatThread as deleteCeoConversation,
  executeAiChatPaperActionDraft as executeCeoPaperActionDraft,
  exportAiChatThread as exportCeoConversation,
  getAiChatThread as getCeoConversation,
  getAiChatThreadRetention as getCeoConversationRetention,
  listAiChatActionDrafts as listCeoActionDrafts,
  listAiChatSignalProposals as listCeoSignalProposals,
  listAiChatThreads as listCeoConversations,
  listAiChatTools as listCeoChatTools,
  purgeAiChatThread as purgeCeoConversation,
  queueAiChatSignalProposalForReview as queueCeoSignalProposalForReview,
  regenerateAiChatResponse as regenerateCeoResponse,
  renameAiChatThread as renameCeoConversation,
  requestAiChatActionDraftApproval as requestCeoActionDraftApproval,
  restoreAiChatThread as restoreCeoConversation,
  saveAiChatSignalProposalToWatchlist as saveCeoSignalProposalToWatchlist,
  searchAiChatThreads as searchCeoConversations,
  streamAiChatResponse as streamCeoResponse,
  updateAiChatThreadContext as updateCeoConversationContext,
  updateAiChatThreadRetention as updateCeoConversationRetention,
} from "@/lib/api/ai-chat"

export const CEO_GATEWAY_CLIENT_NOTE =
  "The current /api/ai-chat routes are backed by services/ceo_gateway.py and are the UI equivalent of /api/ceo/chat."
